from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import override

from hexdoc.core import ResourceLocation
from pydantic import BaseModel

from .hex_math import HexAngle, HexDir, HexPattern
from .patterns import PatternOperator


class SpecialHandlerInfo(BaseModel):
    id: ResourceLocation
    raw_name: str
    """Raw special handler name, including the `: %s` at the end."""
    operator: PatternOperator


@dataclass(kw_only=True)
class SpecialHandlerMatch[T]:
    handler: SpecialHandler[T]
    info: SpecialHandlerInfo
    direction: HexDir
    signature: str
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

    def get_name(self, raw_name: str, value: T) -> str:
        """Given the raw name from the lang file and a value, returns a formatted
        pattern name."""
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
