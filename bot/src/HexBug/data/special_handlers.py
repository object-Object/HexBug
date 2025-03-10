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
    def name(self) -> str:
        return self.handler.get_name(self.info.raw_name, self.value)


class SpecialHandler[T](ABC):
    def __init__(self, id: ResourceLocation):
        super().__init__()
        self.id = id

    @abstractmethod
    def try_match(self, direction: HexDir, signature: str) -> T | None:
        """Attempts to match the given pattern against this special handler."""

    @abstractmethod
    def try_parse_value(
        self,
        registry: HexBugRegistry,
        value: str,
    ) -> tuple[T, HexPattern] | None:
        """Attempts to generate a valid pattern for this special handler from the given
        value."""

    def get_name(self, raw_name: str, value: T | None) -> str:
        """Given the raw name from the lang file and a value, returns a formatted
        pattern name."""
        if value is None:
            return raw_name.removesuffix(": %s")
        return raw_name % str(value)


class NumberSpecialHandler(SpecialHandler[float]):
    @override
    def try_match(self, direction: HexDir, signature: str) -> float | None:
        match signature[:4]:
            case "aqaa":
                sign = 1
            case "dedd":
                sign = -1
            case _:
                return None

        accumulator = 0
        for c in signature[4:]:
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
    def try_parse_value(self, registry: HexBugRegistry, value: str):
        value = value.strip()
        if not value.removeprefix("-").isnumeric():
            return None

        n = int(value)
        if n not in registry.pregenerated_numbers:
            return None

        return n, registry.pregenerated_numbers[n]


class MaskSpecialHandler(SpecialHandler[str]):
    @override
    def try_match(self, direction: HexDir, signature: str) -> str | None:
        if signature.startswith(HexAngle.LEFT_BACK.letter):
            flat_dir = direction.rotated_by(HexAngle.LEFT)
        else:
            flat_dir = direction

        result = ""
        is_on_baseline = True

        for direction in HexPattern(direction, signature).iter_directions():
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

        return result

    @override
    def try_parse_value(self, registry: HexBugRegistry, value: str):
        value = value.lower().strip()
        if not VALID_MASK_PATTERN.fullmatch(value):
            return None

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
