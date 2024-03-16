from __future__ import annotations

import re
from dataclasses import dataclass, field
from itertools import pairwise
from typing import TYPE_CHECKING, Any, Iterator, TypeAlias

from lark import Token
from sty import fg

from .hex_math import Angle, Direction

if TYPE_CHECKING:
    from .registry import Registry

localize_regex = re.compile(r"((?:number|mask))(: .+)")


@dataclass
class Iota:
    _datum: Any

    def __post_init__(self):
        if isinstance(self._datum, Token):
            self._datum = str(self._datum)

    def color(self) -> str:
        return ""

    def presentation_name(self):
        return str(self._datum)

    def localize(self, registry: Registry, name: str | None = None):
        presentation_name = name if name is not None else self.presentation_name()
        value = ""
        if match := localize_regex.match(presentation_name):
            (presentation_name, value) = match.groups()
        return (
            registry.get_translation_from_name(presentation_name, presentation_name)
            + value
        )

    def print(self, level: int, highlight: bool, registry: Registry) -> str:
        indent = "  " * level
        datum_name = self.localize(registry)
        return (
            indent + self.color() + datum_name + fg.rs
            if highlight
            else indent + datum_name
        )

    def preadjust(self, level: int) -> int:
        return level

    def postadjust(self, level: int) -> int:
        return level


class ListOpener(Iota):
    def presentation_name(self):
        return "["

    def postadjust(self, level: int) -> int:
        return level + 1


class ListCloser(Iota):
    def presentation_name(self):
        return "]"

    def preadjust(self, level: int) -> int:
        return level - 1


class Pattern(Iota):
    def pattern_name(self) -> str:
        return str(self._datum)

    def localize_pattern_name(self, registry: Registry) -> str:
        return self.localize(registry, self.pattern_name())

    def color(self):
        return fg.yellow


class Unknown(Iota):
    def color(self):
        return fg(124)  # red


@dataclass
class UnknownPattern(Unknown, Pattern):
    _datum: Any = field(init=False, compare=False, repr=False)

    _initial_direction: Direction
    _angles: str = ""

    def __post_init__(self):
        self._angles = str(self._angles)
        self._datum = self._angles

    def presentation_name(self):
        return f"unknown: {self._initial_direction.name} {self._angles}"

    @property
    def _cmp_key(self):
        return (self._initial_direction, self._angles)


class Bookkeeper(Pattern):
    def pattern_name(self) -> str:
        return self.presentation_name()

    def presentation_name(self):
        return f"mask: {self._datum}"


class Number(Pattern):
    def pattern_name(self) -> str:
        return self.presentation_name()

    def presentation_name(self):
        return f"number: {float(self._datum):g}"


class PatternOpener(Pattern):
    def presentation_name(self):
        return "{"

    def postadjust(self, level: int) -> int:
        return level + 1


class PatternCloser(Pattern):
    def presentation_name(self):
        return "}"

    def preadjust(self, level: int) -> int:
        return level - 1


class NumberConstant(Iota):
    def __post_init__(self):
        super().__post_init__()
        self._datum = float(self._datum)

    def str(self):
        return self._datum

    def color(self):
        return fg.li_green


@dataclass
class Vector(NumberConstant):
    _datum: Any = field(init=False, compare=False, repr=False)

    x: NumberConstant
    y: NumberConstant
    z: NumberConstant

    def __post_init__(self):
        self._datum = f"({self.x._datum}, {self.y._datum}, {self.z._datum})"

    @classmethod
    def from_raw(cls, x: float, y: float, z: float):
        return cls(NumberConstant(x), NumberConstant(y), NumberConstant(z))

    def color(self):
        return fg(207)  # pink


class Null(Iota):
    def __init__(self, *_: str):
        super().__init__("NULL")

    def color(self):
        return fg.magenta


class Boolean(Iota):
    def __post_init__(self):
        super().__post_init__()
        match str(self._datum).lower():
            case "true":
                self._datum = True
            case "false":
                self._datum = False
            case _:
                raise ValueError(f"Invalid Boolean datum: {self._datum}")

    def color(self):
        return fg.magenta


class String(Iota):
    def presentation_name(self):
        return f'"{self._datum}"'


@dataclass
class Matrix(Iota):
    _datum: Any = field(init=False, compare=False, repr=False, default=None)

    rows: int
    """m"""
    columns: int
    """n"""
    data: list[list[float]]
    """rows"""

    @classmethod
    def from_rows(cls, *data: list[float]):
        rows = len(data)
        columns = 0

        if data:
            columns = len(data[0])
            if any(len(r) != columns for r in data[1:]):
                raise ValueError(f"Mismatched row count: {rows}")

        return cls(rows, columns, list(data))


ParsedIota: TypeAlias = list[Iota] | Iota


def _parse_number(pattern: str):
    negate = pattern.startswith("dedd")
    accumulator = 0
    for c in pattern[4:]:
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
    if negate:
        accumulator = -accumulator
    return Number(accumulator)


def _get_pattern_directions(starting_direction: Direction, pattern: str):
    directions = [starting_direction]
    for c in pattern:
        directions.append(directions[-1].rotated(c))
    return directions


def _parse_bookkeeper(starting_direction: Direction, pattern: str):
    if not pattern:
        return "-"
    directions = _get_pattern_directions(starting_direction, pattern)
    flat_direction = (
        starting_direction.rotated(Angle.LEFT)
        if pattern[0] == "a"
        else starting_direction
    )
    mask = ""
    skip = False
    for index, direction in enumerate(directions):
        if skip:
            skip = False
            continue
        angle = direction.angle_from(flat_direction)
        if angle == Angle.FORWARD:
            mask += "-"
            continue
        if index >= len(directions) - 1:
            return None
        angle2 = directions[index + 1].angle_from(flat_direction)
        if angle == Angle.RIGHT and angle2 == Angle.LEFT:
            mask += "v"
            skip = True
            continue
        return None
    return mask


def generate_bookkeeper(mask: str):
    if mask[0] == "v":
        starting_direction = Direction.SOUTH_EAST
        pattern = "a"
    else:
        starting_direction = Direction.EAST
        pattern = ""

    for previous, current in pairwise(mask):
        match previous, current:
            case "-", "-":
                pattern += "w"
            case "-", "v":
                pattern += "ea"
            case "v", "-":
                pattern += "e"
            case "v", "v":
                pattern += "da"

    return starting_direction, pattern


def _handle_named_pattern(name: str):
    match name:
        case "open_paren":
            return PatternOpener("open_paren")
        case "close_paren":
            return PatternCloser("close_paren")
        case _:
            return Pattern(name)


def _parse_unknown_pattern(
    pattern: UnknownPattern, registry: Registry
) -> tuple[Pattern, str]:
    if info := registry.from_pattern_or_segments(
        pattern._initial_direction, pattern._datum
    ):
        return _handle_named_pattern(info.name), info.name
    elif bk := _parse_bookkeeper(pattern._initial_direction, pattern._datum):
        return Bookkeeper(bk), "mask"
    elif pattern._datum.startswith(("aqaa", "dedd")):
        return _parse_number(pattern._datum), "number"
    else:
        return pattern, ""


def massage_raw_parsed_iota(iota: ParsedIota, registry: Registry) -> Iterator[Iota]:
    match iota:
        case [*subpatterns]:
            yield ListOpener("[")
            for subpattern in subpatterns:
                yield from massage_raw_parsed_iota(subpattern, registry)
            yield ListCloser("]")
        case UnknownPattern():
            yield _parse_unknown_pattern(iota, registry)[0]
        case other:
            yield other
