from __future__ import annotations

import itertools
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from hexdoc.core import ResourceLocation
from pydantic import BaseModel

from .hex_math import HexAngle, HexDir, HexPattern
from .patterns import PatternOperator

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


@dataclass(kw_only=True)
class SpecialHandlerMatch[T]:
    handler: SpecialHandler[T]
    info: SpecialHandlerInfo
    value: T

    @property
    def id(self) -> ResourceLocation:
        return self.info.id

    @property
    def name(self) -> str:
        return self.handler.get_name(self.info.raw_name, self.value)


class SpecialHandler[T](ABC):
    def __init__(self, id: ResourceLocation):
        super().__init__()
        self.id = id

    @abstractmethod
    def try_match(self, pattern: HexPattern) -> T | None:
        """Attempts to match the given pattern against this special handler."""

    @abstractmethod
    def parse_value(
        self,
        registry: HexBugRegistry,
        value: str,
    ) -> tuple[T, HexPattern]:
        """Attempts to generate a valid pattern for this special handler from the given
        value.

        Raises ValueError on failure.
        """

    def get_name(self, raw_name: str, value: T | None) -> str:
        """Given the raw name from the lang file and a value, returns a formatted
        pattern name."""
        if value is None:
            return raw_name.removesuffix(": %s")
        return raw_name % str(value)


class NumberSpecialHandler(SpecialHandler[float]):
    @override
    def try_match(self, pattern: HexPattern) -> float | None:
        match pattern.signature[:4]:
            case "aqaa":
                sign = 1
            case "dedd":
                sign = -1
            case _:
                return None

        accumulator = 0
        for c in pattern.signature[4:]:
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
    def parse_value(self, registry: HexBugRegistry, value: str):
        value = value.strip()
        if not value.removeprefix("-").isnumeric():
            raise ValueError(f"Invalid integer: {value}")

        n = int(value)
        if n not in registry.pregenerated_numbers:
            raise ValueError(f"No pregenerated number found for {n}.")

        return n, registry.pregenerated_numbers[n]


class MaskSpecialHandler(SpecialHandler[str]):
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
    def parse_value(self, registry: HexBugRegistry, value: str):
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


class OverevaluateTailDepthSpecialHandler(SpecialHandler[int]):
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

    @override
    def try_match(self, pattern: HexPattern) -> int | None:
        tail = pattern.signature.removeprefix(self.prefix)
        if tail == pattern.signature:
            return None

        depth = self.initial_depth
        for index, char in enumerate(tail):
            if char != self.get_tail_char(index):
                return None
            depth += 1

        return depth

    @override
    def parse_value(self, registry: HexBugRegistry, value: str):
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

        signature = self.prefix + "".join(
            self.get_tail_char(index) for index in range(depth - self.initial_depth)
        )

        return depth, HexPattern(self.direction, signature)

    def get_tail_char(self, index: int):
        return self.tail_chars[index % len(self.tail_chars)]
