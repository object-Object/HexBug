from __future__ import annotations

import itertools
import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, override

from hexdoc.core import ResourceLocation
from hexdoc.minecraft import I18n, LocalizedStr
from pydantic import BaseModel

from .hex_math import HexAngle, HexDir, HexPattern
from .patterns import PatternOperator
from .utils.strings import format_number

if TYPE_CHECKING:
    from .registry import HexBugRegistry

VALID_MASK_PATTERN = re.compile(r"[-v]+")


class SpecialHandlerInfo(BaseModel):
    id: ResourceLocation
    raw_name: str
    """Raw special handler name, including the `: %s` at the end."""
    base_name: str
    """Pattern name, not including a specific value or any placeholders."""
    operator: PatternOperator

    @property
    def mod_id(self):
        return self.id.namespace


class SpecialHandlerMatch[T](SpecialHandlerInfo):
    model_config = {"arbitrary_types_allowed": True}

    handler: SpecialHandler[T]
    value: T

    @staticmethod
    def from_parts[_T](
        info: SpecialHandlerInfo,
        handler: SpecialHandler[_T],
        value: _T,
    ) -> SpecialHandlerMatch[_T]:
        return SpecialHandlerMatch(**dict(info), handler=handler, value=value)

    @property
    def name(self) -> str:
        return self.handler.get_name(self.raw_name, self.value)


class SpecialHandlerPattern[T](SpecialHandlerMatch[T]):
    pattern: HexPattern

    @staticmethod
    def from_parts[_T](  # pyright: ignore[reportIncompatibleMethodOverride]
        info: SpecialHandlerInfo,
        handler: SpecialHandler[_T],
        value: _T,
        pattern: HexPattern,
    ) -> SpecialHandlerPattern[_T]:
        return SpecialHandlerPattern(
            **dict(info),
            handler=handler,
            value=value,
            pattern=pattern,
        )


class SpecialHandler[T](ABC):
    def __init__(self, id: ResourceLocation):
        super().__init__()
        self.id = id

    @abstractmethod
    def try_match(self, pattern: HexPattern) -> T | None:
        """Attempts to match the given pattern against this special handler."""

    @abstractmethod
    def generate_pattern(
        self,
        registry: HexBugRegistry,
        value: str,
    ) -> tuple[T, HexPattern]:
        """Attempts to generate a valid pattern for this special handler from the given
        value.

        Raises ValueError on failure.
        """

    @property
    def supports_unprefixed_shorthand(self) -> bool:
        return False

    def localize(self, i18n: I18n) -> LocalizedStr:
        """Returns the raw name of this handler from the lang file."""
        result = i18n.localize(f"hexcasting.special.{self.id}")
        if result.key == result.value:
            raise ValueError(f"Special handler not localized: {self.id}")
        return result

    def get_name(self, raw_name: str, value: T | None) -> str:
        """Given the raw name from the lang file and a value, returns a formatted
        pattern name."""
        if value is None:
            return raw_name.removesuffix(": %s")
        try:
            return raw_name % str(value)
        except TypeError as e:
            e.add_note(f"{raw_name=} {value=}")
            raise


class PrefixSpecialHandler[T, P](SpecialHandler[T]):
    @property
    @abstractmethod
    def prefix_map(self) -> dict[str, P]: ...

    @abstractmethod
    def try_match_suffix(self, prefix: P, /, suffix: str) -> T | None: ...

    @override
    def try_match(self, pattern: HexPattern) -> T | None:
        for prefix, value in self.prefix_map.items():
            if pattern.signature.startswith(prefix):
                return self.try_match_suffix(
                    value,
                    suffix=pattern.signature.removeprefix(prefix),
                )


class NumberSpecialHandler(PrefixSpecialHandler[float, int]):
    @property
    @override
    def supports_unprefixed_shorthand(self) -> bool:
        return True

    @property
    @override
    def prefix_map(self):
        return {
            "aqaa": 1,
            "dedd": -1,
        }

    @override
    def try_match_suffix(self, sign: int, suffix: str) -> float | None:
        accumulator = 0
        for c in suffix:
            match c:
                case "w":
                    accumulator += 1
                case "q":
                    accumulator += 5
                case "e":
                    accumulator += 10
                case "a":
                    accumulator *= 2
                case "d":
                    accumulator /= 2
                case _:
                    pass

        return sign * accumulator

    @override
    def generate_pattern(self, registry: HexBugRegistry, value: str):
        value = value.strip()
        if not value.removeprefix("-").isnumeric():
            raise ValueError(f"Invalid integer: {value}")

        n = int(value)
        if n not in registry.pregenerated_numbers:
            raise ValueError(f"No pregenerated number found for {n}.")

        return n, registry.pregenerated_numbers[n]

    @override
    def get_name(self, raw_name: str, value: float | None) -> str:
        if value is not None:
            return raw_name % format_number(value)
        return super().get_name(raw_name, value)


class MaskSpecialHandler(SpecialHandler[str]):
    @property
    @override
    def supports_unprefixed_shorthand(self) -> bool:
        return True

    @override
    def try_match(self, pattern: HexPattern) -> str | None:
        if pattern.signature.startswith(HexAngle.LEFT_BACK.letter):
            flat_dir = pattern.direction.rotated_by(HexAngle.LEFT)
        else:
            flat_dir = pattern.direction

        result = ""
        is_on_baseline = True

        for direction in pattern.iter_directions():
            match direction.angle_from(flat_dir):
                case HexAngle.FORWARD if is_on_baseline:
                    result += "-"
                case HexAngle.RIGHT if is_on_baseline:
                    is_on_baseline = False
                case HexAngle.LEFT if not is_on_baseline:
                    result += "v"
                    is_on_baseline = True
                case _:
                    return None

        if not is_on_baseline:
            return None

        return result

    @override
    def generate_pattern(self, registry: HexBugRegistry, value: str):
        value = value.lower().strip()
        if not VALID_MASK_PATTERN.fullmatch(value):
            raise ValueError(f"Invalid mask (expected only - and v): {value}")

        if value[0] == "v":
            direction = HexDir.SOUTH_EAST
            signature = "a"
        else:
            direction = HexDir.EAST
            signature = ""

        for previous, current in itertools.pairwise(value):
            match previous, current:
                case "-", "-":
                    signature += "w"
                case "-", "v":
                    signature += "ea"
                case "v", "-":
                    signature += "e"
                case "v", "v":
                    signature += "da"
                case _:
                    raise RuntimeError("unreachable")

        return value, HexPattern(direction, signature)


class OverevaluateTailDepthSpecialHandler(PrefixSpecialHandler[int, Any]):
    def __init__(
        self,
        id: ResourceLocation,
        direction: HexDir,
        prefix: str,
        initial_depth: int,
        tail_chars: str,
    ):
        super().__init__(id)
        self.direction = direction
        self.prefix = prefix
        self.initial_depth = initial_depth
        self.tail_chars = tail_chars

    @property
    @override
    def prefix_map(self):
        return {self.prefix: None}

    @override
    def try_match_suffix(self, _: Any, suffix: str) -> int | None:
        depth = self.initial_depth
        for index, char in enumerate(suffix):
            if char != self.get_tail_char(index):
                return None
            depth += 1

        return depth

    @override
    def generate_pattern(self, registry: HexBugRegistry, value: str):
        value = value.strip()
        if value.isnumeric():
            depth = int(value)
        elif all(c == "-" for c in value):
            depth = len(value)
        else:
            raise ValueError(
                f"Invalid tail depth (expected an integer or dashes): {value}"
            )

        if depth < self.initial_depth:
            raise ValueError(
                f"Invalid tail depth (expected at least {self.initial_depth}): {depth}"
            )

        # sanity check
        if depth > 128:
            raise ValueError(f"Invalid tail depth: {depth}")

        signature = self.prefix + "".join(
            self.get_tail_char(index) for index in range(depth - self.initial_depth)
        )

        return depth, HexPattern(self.direction, signature)

    def get_tail_char(self, index: int):
        return self.tail_chars[index % len(self.tail_chars)]


class ComplexHexLongSpecialHandler(PrefixSpecialHandler[int, int]):
    @property
    @override
    def prefix_map(self):
        return {
            "awdedwaaw": 1,
            "dwaqawddw": -1,
        }

    @override
    def try_match_suffix(self, sign: int, suffix: str) -> int | None:
        accumulator = 0
        for c in suffix:
            match c:
                case "w":
                    accumulator += 1
                case "q":
                    accumulator += 5
                case "e":
                    accumulator += 10
                case "a":
                    accumulator <<= 1
                case "d":
                    accumulator >>= 1
                case _:
                    pass

        return sign * accumulator

    @override
    def generate_pattern(self, registry: HexBugRegistry, value: str):
        value = value.strip()
        if not value.removeprefix("-").isnumeric():
            raise ValueError(f"Invalid integer: {value}")

        # TODO: implement?
        raise NotImplementedError

    # TODO: remove localize and get_name when kinetic fixes the lang entry

    @override
    def localize(self, i18n: I18n):
        try:
            return super().localize(i18n)
        except ValueError:
            return i18n.localize(f"hexcasting.action.{self.id}")

    @override
    def get_name(self, raw_name: str, value: int | None) -> str:
        if ":" in raw_name:
            return super().get_name(raw_name, value)

        if value is None:
            return raw_name
        return f"{raw_name}: {value}"


class HexFlowNumberSpecialHandler(PrefixSpecialHandler[float, int]):
    @property
    @override
    def prefix_map(self):
        return {
            "aqawdedq": 1,
            "dedwaqae": -1,
        }

    @override
    def try_match_suffix(self, sign: int, suffix: str) -> float | None:
        res = 0
        mode = HexDir.EAST
        for c in suffix:
            mode = mode.rotated_by(HexAngle[c])
            match mode:
                case HexDir.NORTH_EAST:
                    res = res * 2 + 1
                case HexDir.EAST:
                    res *= 2
                case HexDir.SOUTH_EAST:
                    res /= 10
                case _:
                    pass
        return res * sign

    @override
    def generate_pattern(
        self,
        registry: HexBugRegistry,
        value: str,
    ) -> tuple[float, HexPattern]:
        raise NotImplementedError

    # TODO: remove localize and get_name when yukkuri fixes the lang entry

    @override
    def localize(self, i18n: I18n):
        try:
            return super().localize(i18n)
        except ValueError:
            return i18n.localize(f"hexcasting.action.{self.id}")

    @override
    def get_name(self, raw_name: str, value: float | None) -> str:
        if ":" in raw_name:
            return super().get_name(raw_name, value)

        if value is None:
            return raw_name
        return f"{raw_name}: {value}"


class HexTraceSpecialHandler(PrefixSpecialHandler[str, Any]):
    prefix = "qqqaw"

    @property
    @override
    def prefix_map(self):
        return {self.prefix: None}

    @override
    def try_match_suffix(self, _: Any, suffix: str) -> str | None:
        return suffix or None

    @override
    def generate_pattern(
        self,
        registry: HexBugRegistry,
        value: str,
    ) -> tuple[str, HexPattern]:
        return value, HexPattern(HexDir.WEST, self.prefix + value)

    @override
    def get_name(self, raw_name: str, value: str | None) -> str:
        return raw_name

    # TODO: remove localize when vivi fixes the lang entry

    @override
    def localize(self, i18n: I18n):
        try:
            return super().localize(i18n)
        except ValueError:
            return i18n.localize(f"hexcasting.action.{self.id}")


class HexThingsNoopSpecialHandler(PrefixSpecialHandler[str, Any]):
    prefix = "dade"

    @property
    @override
    def prefix_map(self):
        return {self.prefix: None}

    @override
    def try_match_suffix(self, _: Any, suffix: str):
        return suffix

    @override
    def generate_pattern(
        self,
        registry: HexBugRegistry,
        value: str,
    ) -> tuple[str, HexPattern]:
        if value in ["-", '"-"']:
            value = ""
        return value, HexPattern(HexDir.NORTH_EAST, self.prefix + value)

    @override
    def get_name(self, raw_name: str, value: str | None) -> str:
        return raw_name
