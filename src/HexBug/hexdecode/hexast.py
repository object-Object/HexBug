from __future__ import annotations

import re
import struct
import uuid
from itertools import pairwise
from typing import Generator

from sty import fg

from .hex_math import Angle, Direction, get_aligned_pattern_segments
from .registry import Registry

localize_regex = re.compile(r"((?:number|mask))(: .+)")


class Iota:
    def __init__(self, datum):
        self._datum = datum

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


class UnknownPattern(Unknown, Pattern):
    def __init__(self, initial_direction, turns):
        self._initial_direction = initial_direction
        super().__init__(turns)

    def presentation_name(self):
        return f"unknown: {self._initial_direction.name} {self._datum}"


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
    def str(self):
        return self._datum

    def color(self):
        return fg.li_green


class Vector(NumberConstant):
    def __init__(self, x, y, z):
        super().__init__(f"({x._datum}, {y._datum}, {z._datum})")

    def color(self):
        return fg(207)  # pink


class Entity(Iota):
    def __init__(self, uuid_bits):
        packed = struct.pack("iiii", *uuid_bits)
        super().__init__(uuid.UUID(bytes_le=packed))

    def color(self):
        return fg.li_blue


class Null(Iota):
    def __init__(self):
        super().__init__("NULL")

    def color(self):
        return fg.magenta


def _parse_number(pattern):
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


def _get_pattern_directions(starting_direction, pattern):
    directions = [starting_direction]
    for c in pattern:
        directions.append(directions[-1].rotated(c))
    return directions


def _parse_bookkeeper(starting_direction, pattern):
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
    if (
        (info := registry.from_pattern.get(pattern._datum))
        or (
            segments := get_aligned_pattern_segments(
                pattern._initial_direction, pattern._datum
            )
        )
        and (info := registry.from_segments.get(segments))
    ):
        return _handle_named_pattern(info.name), info.name
    elif bk := _parse_bookkeeper(pattern._initial_direction, pattern._datum):
        return Bookkeeper(bk), "mask"
    elif pattern._datum.startswith(("aqaa", "dedd")):
        return _parse_number(pattern._datum), "number"
    else:
        return pattern, ""


def massage_raw_pattern_list(
    pattern, registry: Registry
) -> Generator[Iota, None, None]:
    match pattern:
        case [*subpatterns]:
            yield ListOpener("[")
            for subpattern in subpatterns:
                yield from massage_raw_pattern_list(subpattern, registry)
            yield ListCloser("]")
        case UnknownPattern():
            yield _parse_unknown_pattern(pattern, registry)[0]
        case other:
            yield other
