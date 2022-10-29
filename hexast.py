"""
MIT License

Copyright (c) 2022 Graham Hughes, object-Object

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

https://github.com/gchpaco/hexdecode
"""

from __future__ import annotations
from enum import Enum
import math
import re
import struct
from typing import Generator, Generic, Iterable, Literal, Mapping, Tuple, Type, TypeGuard, TypeVar, TypedDict, NotRequired, LiteralString, get_args
import uuid
from sty import fg
from dataclasses import dataclass, field
from itertools import pairwise
from HexMod.doc.collate_data import FormatTree

localize_regex = re.compile(r"((?:number|mask))(: .+)")

ModName = Literal["Hex Casting", "Hexal"]
BASE_URLS: dict[ModName, str] = {
    "Hex Casting": "https://gamma-delta.github.io/HexMod/",
    "Hexal": "https://talia-12.github.io/Hexal/",
}

@dataclass
class Registry:
    pattern_to_name: dict[str, str] = field(default_factory=dict)
    great_spells: dict[frozenset[Segment], str] = field(default_factory=dict)
    """segments: name"""
    name_to_translation: dict[str, str] = field(default_factory=dict)
    translation_to_pattern: dict[str, tuple[Direction, str, bool, str]] = field(default_factory=dict)
    """translation: (direction, pattern, is_great, name)"""
    page_title_to_url: dict[str, tuple[ModName, str, list[str]]] = field(default_factory=dict)
    """page_title: (mod, url, name)"""
    name_to_url: dict[str, tuple[ModName, str]] = field(default_factory=dict)
    """name: (mod, url)"""
    name_to_args: dict[str, str] = field(default_factory=dict)

class Iota:
    def __init__(self, datum):
        self._datum = datum
    def color(self) -> str:
        return ""
    def presentation_name(self):
        return str(self._datum)
    def localize(self, registry: Registry):
        presentation_name = self.presentation_name()
        value = ""
        if match := localize_regex.match(presentation_name):
            (presentation_name, value) = match.groups()
        return registry.name_to_translation.get(presentation_name, presentation_name) + value
    def print(self, level: int, highlight: bool, registry: Registry) -> str:
        indent = "  " * level
        datum_name = self.localize(registry)
        return indent + self.color() + datum_name + fg.rs if highlight else indent + datum_name
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
    def color(self):
        return fg.yellow

class Unknown(Iota):
    def color(self):
        return fg(124) # red

class UnknownPattern(Unknown, Pattern):
    def __init__(self, initial_direction, turns):
        self._initial_direction = initial_direction
        super().__init__(turns)
    def presentation_name(self):
        return f"unknown: {self._initial_direction.name} {self._datum}"

class Bookkeeper(Pattern):
    def presentation_name(self):
        return f"mask: {self._datum}"

class Number(Pattern):
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
        return fg(207) # pink

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

class Angle(Enum):
    FORWARD    = (0, "w")
    w          = (0, "w")
    RIGHT      = (1, "e")
    e          = (1, "e")
    RIGHT_BACK = (2, "d")
    d          = (2, "d")
    BACK       = (3, "s")
    LEFT_BACK  = (4, "a")
    a          = (4, "a")
    LEFT       = (5, "q")
    q          = (5, "q")

    @classmethod
    def from_number(cls, num):
        return {0: cls.FORWARD, 1: cls.RIGHT, 2: cls.RIGHT_BACK,
           3: cls.BACK, 4: cls.LEFT_BACK, 5: cls.LEFT}[num % len(Angle)]

    @classmethod
    def get_offset(cls, angle: Angle | str | int) -> int:
        match angle:
            case Angle():
                return angle.offset
            case str():
                return Angle[angle].offset
            case int():
                return Angle.from_number(angle).offset

    @property
    def offset(self) -> int:
        return self.value[0]

    @property
    def deg(self) -> float:
        return ((len(Angle) - self.ordinal) * 60) % 360

    def __init__(self, ordinal, letter):
        self.ordinal = ordinal
        self.letter = letter


# Uses axial coordinates as per https://www.redblobgames.com/grids/hexagons/ (same system as Hex)
class Coord:
    @classmethod
    def origin(cls) -> Coord:
        return Coord(0, 0)

    def __init__(self, q: int, r: int) -> None:
        self._q = q
        self._r = r
    
    @property
    def q(self):
        return self._q
    
    @property
    def r(self):
        return self._r

    @property
    def s(self):
        # Hex has this as q - r, but the rotation formulas from the above link don't seem to work with that
        return -self.q - self.r
    
    def __hash__(self) -> int:
        return hash((self.q, self.r))
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Coord):
            return (self.q, self.r) == (other.q, other.r)
        return NotImplemented
    
    def __repr__(self) -> str:
        return f"({self.q}, {self.r})"
    
    def __add__(self, other: Direction | Coord) -> Coord:
        return self.shifted(other)
    
    def __sub__(self, other: Coord) -> Coord:
        return self.delta(other)
    
    def pixel(self, size: int) -> Tuple[float, float]:
        return (
            size * (math.sqrt(3) * self.q + math.sqrt(3)/2 * self.r), # x
            size * (3/2 * self.r) # y
        )
    
    def shifted(self, other: Direction | Coord) -> Coord:
        if isinstance(other, Direction):
            other = other.as_delta()
        return Coord(self.q + other.q, self.r + other.r)
    
    def rotated(self, angle: Angle | str | int) -> Coord:
        offset = Angle.get_offset(angle)
        rotated = self
        for _ in range(abs(offset)):
            rotated = Coord(-rotated.r, -rotated.s)
        return rotated
    
    def delta(self, other: Coord) -> Coord:
        return Coord(self.q - other.q, self.r - other.r)
    
    def immediate_delta(self, other: Coord) -> Direction | None:
        match other.delta(self):
            case Coord(q=1, r=0):
                return Direction.EAST
            case Coord(q=0, r=1):
                return Direction.SOUTH_EAST
            case Coord(q=-1, r=1):
                return Direction.SOUTH_WEST
            case Coord(q=-1, r=0):
                return Direction.WEST
            case Coord(q=0, r=-1):
                return Direction.NORTH_WEST
            case Coord(q=1, r=-1):
                return Direction.NORTH_EAST
            case _:
                return None

class Direction(Enum): # numbers increase clockwise
    NORTH_EAST = 0
    EAST       = 1
    SOUTH_EAST = 2
    SOUTH_WEST = 3
    WEST       = 4
    NORTH_WEST = 5

    @property
    def side(self):
        return "WEST" if self in [Direction.NORTH_WEST, Direction.WEST, Direction.SOUTH_WEST] else "EAST"

    def angle_from(self, other: Direction) -> Angle:
        return Angle.from_number((self.value - other.value) % len(Angle))

    def rotated(self, angle: Angle | str | int) -> Direction:
        return Direction((self.value + Angle.get_offset(angle)) % len(Direction))
    
    def __mul__(self, angle: Angle) -> Direction:
        return self.rotated(angle)
    
    def as_delta(self) -> Coord:
        match self:
            case Direction.NORTH_EAST:
                return Coord(1, -1)
            case Direction.EAST:
                return Coord(1, 0)
            case Direction.SOUTH_EAST:
                return Coord(0, 1)
            case Direction.SOUTH_WEST:
                return Coord(-1, 1)
            case Direction.WEST:
                return Coord(-1, 0)
            case Direction.NORTH_WEST:
                return Coord(0, -1)

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

class Segment:
    def __init__(self, root: Coord, direction: Direction):
        # because otherwise there's two ways to represent any given line
        if direction.side == "EAST":
            self._root = root
            self._direction = direction
        else:
            self._root = root + direction
            self._direction = direction.rotated(Angle.BACK)
    
    def __hash__(self) -> int:
        return hash((self.root, self.direction))
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Segment):
            return (self.root, self.direction) == (other.root, other.direction)
        return NotImplemented
    
    def __repr__(self) -> str:
        return f"{self.root}@{self.direction}"
    
    @property
    def root(self):
        return self._root

    @property
    def direction(self):
        return self._direction
    
    @property
    def end(self):
        return self.root + self.direction
    
    @property
    def min_q(self):
        return min(self.root.q, self.end.q)
    
    @property
    def max_q(self):
        return max(self.root.q, self.end.q)

    @property
    def min_r(self):
        return min(self.root.r, self.end.r)
    
    @property
    def max_r(self):
        return max(self.root.r, self.end.r)
    
    def shifted(self, other: Direction | Coord) -> Segment:
        return Segment(self.root.shifted(other), self.direction)

    def rotated(self, angle: Angle | str | int) -> Segment:
        return Segment(self.root.rotated(angle), self.direction.rotated(angle))

T = TypeVar("T", bound=LiteralString)
class BookPage(TypedDict, Generic[T]):
    type: T

class BookPage_patchouli_text(BookPage[Literal["patchouli:text"]]):
    """title"""
    text: FormatTree
    anchor: NotRequired[str]
    title: NotRequired[str]

class BookPage_patchouli_spotlight(BookPage[Literal["patchouli:spotlight"]]):
    """item_name"""
    item: str
    item_name: str
    link_recipe: bool
    text: FormatTree
    anchor: NotRequired[str]

class BookPage_hexcasting_pattern(BookPage[Literal["hexcasting:pattern"]]):
    """name"""
    name: str
    op: list
    op_id: str
    text: FormatTree
    anchor: NotRequired[str]
    hex_size: NotRequired[int]
    input: NotRequired[str]
    output: NotRequired[str]

class BookPage_hexcasting_manual_pattern(BookPage[Literal["hexcasting:manual_pattern"]]):
    """header"""
    anchor: str
    header: str
    input: str
    op: list
    op_id: str
    output: str
    patterns: list
    text: FormatTree

# no anchor (ie. I can ignore them)

class BookPage_patchouli_crafting(BookPage[Literal["patchouli:crafting"]]):
    """actually has an anchor but not worth listing"""
    item_name: list
    recipe: str
    anchor: NotRequired[str]
    recipe2: NotRequired[str]
    text: NotRequired[FormatTree]

class BookPage_hexcasting_manual_pattern_nosig(BookPage[Literal["hexcasting:manual_pattern_nosig"]]):
    header: str
    op: list
    text: FormatTree
    patterns: NotRequired[list | dict]

class BookPage_patchouli_link(BookPage[Literal["patchouli:link"]]):
    link_text: str
    text: FormatTree
    url: str

class BookPage_hexcasting_crafting_multi(BookPage[Literal["hexcasting:crafting_multi"]]):
    heading: str
    item_name: list
    recipes: list
    text: FormatTree

class BookPage_hexcasting_brainsweep(BookPage[Literal["hexcasting:brainsweep"]]):
    output_name: str
    recipe: str
    text: FormatTree

class BookPage_patchouli_image(BookPage[Literal["patchouli:image"]]):
    border: bool
    images: list
    title: str

class BookPage_patchouli_empty(BookPage[Literal["patchouli:empty"]]):
    pass

class BookPage_hexal_everbook_entry(BookPage[Literal["hexal:everbook_entry"]]):
    pass

class BookEntry(TypedDict):
    category: str
    icon: str
    id: str
    name: str
    pages: list[BookPage]
    advancement: NotRequired[str]
    entry_color: NotRequired[str]
    extra_recipe_mappings: NotRequired[dict]
    flag: NotRequired[str]
    priority: NotRequired[bool]
    read_by_default: NotRequired[bool]
    sort_num: NotRequired[int]
    sortnum: NotRequired[int | float]

class BookCategory(TypedDict):
    description: FormatTree
    entries: list[BookEntry]
    icon: str
    id: str
    name: str
    sortnum: int
    entry_color: NotRequired[str]
    flag: NotRequired[str]
    parent: NotRequired[str]

class Book(TypedDict):
    name: str
    landing_text: FormatTree
    version: int
    show_progress: bool
    creative_tab: str
    model: str
    book_texture: str
    filler_texture: str
    i18n: dict[str, str]
    macros: dict[str, str]
    resource_dir: str
    modid: str
    pattern_reg: dict[str, tuple[str, str, bool]]
    """pattern_id: (pattern, direction, is_great)"""
    categories: list[BookCategory]
    blacklist: set[str]
    spoilers: set[str]

U = TypeVar("U", bound=BookPage)
def isbookpage(page: Mapping, book_type: Type[U]) -> TypeGuard[U]:
    try:
        # this feels really really really gross. but it works
        return page["type"] == get_args(get_args(book_type.__orig_bases__[0])[0])[0]  # type: ignore
    except IndexError:
        return False

def _get_pattern_directions(starting_direction, pattern):
    directions = [starting_direction]
    for c in pattern:
        directions.append(directions[-1].rotated(c))
    return directions

def _parse_bookkeeper(starting_direction, pattern):
    if not pattern:
        return "-"
    directions = _get_pattern_directions(starting_direction, pattern)
    flat_direction = starting_direction.rotated(Angle.LEFT) if pattern[0] == "a" else starting_direction
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

def _get_segments(direction: Direction, pattern: str) -> frozenset[Segment]:
    cursor = Coord.origin()
    compass = direction

    segments = [Segment(cursor, compass)]

    for c in pattern:
        cursor += compass
        compass = compass.rotated(Angle[c])
        segments.append(Segment(cursor, compass))

    return frozenset(segments)

def _align_segments_to_origin(segments: Iterable[Segment]) -> frozenset[Segment]:
    min_q = min(segment.min_q for segment in segments)
    min_r = min(segment.min_r for segment in segments)

    top_left = Coord(min_q, min_r)
    delta = Coord.origin() - top_left

    return frozenset([segment.shifted(delta) for segment in segments])

def _get_pattern_segments(direction: Direction, pattern: str, align=True) -> frozenset[Segment]:
    segments = _get_segments(direction, pattern)
    return _align_segments_to_origin(segments) if align else segments

def get_rotated_pattern_segments(direction: Direction, pattern: str) -> Generator[frozenset[Segment], None, None]:
    segments = _get_pattern_segments(direction, pattern, False)
    for n in range(6):
        yield _align_segments_to_origin([segment.rotated(n) for segment in segments])

def _handle_named_pattern(name: str):
    match name:
        case "open_paren":
            return PatternOpener("open_paren")
        case "close_paren":
            return PatternCloser("close_paren")
        case _:
            return Pattern(name)

def _parse_unknown_pattern(pattern: UnknownPattern, registry: Registry) -> tuple[Pattern, str]:
    if (
        (name := registry.pattern_to_name.get(pattern._datum)) or
        (segments := _get_pattern_segments(pattern._initial_direction, pattern._datum)) and
        (name := registry.great_spells.get(segments))
    ):
        return _handle_named_pattern(name), name
    elif bk := _parse_bookkeeper(pattern._initial_direction,
                                    pattern._datum):
        return Bookkeeper(bk), "mask"
    elif pattern._datum.startswith(("aqaa", "dedd")):
        return _parse_number(pattern._datum), "number"
    else:
        return pattern, ""

def massage_raw_pattern_list(pattern, registry: Registry) -> Generator[Iota, None, None]:
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
