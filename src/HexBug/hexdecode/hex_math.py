from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Generator, Iterable, Self


class Angle(Enum):
    FORWARD = (0, "w")
    w = (0, "w")
    RIGHT = (1, "e")
    e = (1, "e")
    RIGHT_BACK = (2, "d")
    d = (2, "d")
    BACK = (3, "s")
    s = (3, "s")
    LEFT_BACK = (4, "a")
    a = (4, "a")
    LEFT = (5, "q")
    q = (5, "q")

    @classmethod
    def from_number(cls, num: int):
        return {
            0: cls.FORWARD,
            1: cls.RIGHT,
            2: cls.RIGHT_BACK,
            3: cls.BACK,
            4: cls.LEFT_BACK,
            5: cls.LEFT,
        }[num % len(Angle)]

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

    def __init__(self, ordinal: int, letter: str):
        self.ordinal = ordinal
        self.letter = letter


# Uses axial coordinates as per https://www.redblobgames.com/grids/hexagons/ (same system as Hex)
@dataclass(frozen=True)
class Coord:
    q: int
    r: int

    @classmethod
    def origin(cls) -> Coord:
        return Coord(0, 0)

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

    def pixel(self, size=1) -> tuple[float, float]:
        return (
            size * (math.sqrt(3) * self.q + math.sqrt(3) / 2 * self.r),
            -size * (3 / 2 * self.r),
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


class Direction(Enum):  # numbers increase clockwise
    NORTH_EAST = 0
    EAST = 1
    SOUTH_EAST = 2
    SOUTH_WEST = 3
    WEST = 4
    NORTH_WEST = 5

    @classmethod
    def from_shorthand(cls, shorthand: str):
        shorthand = (
            shorthand.lower()
            .replace("_", "")
            .replace("-", "")
            .replace("north", "n")
            .replace("south", "s")
            .replace("west", "w")
            .replace("east", "e")
        )

        return {
            "e": Direction.EAST,
            "se": Direction.SOUTH_EAST,
            "sw": Direction.SOUTH_WEST,
            "w": Direction.WEST,
            "nw": Direction.NORTH_WEST,
            "ne": Direction.NORTH_EAST,
        }.get(shorthand)

    @property
    def side(self):
        return (
            "WEST"
            if self in [Direction.NORTH_WEST, Direction.WEST, Direction.SOUTH_WEST]
            else "EAST"
        )

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

    def as_pyplot_angle(self) -> float:
        return self.angle_from(Direction.EAST).deg - 90


@dataclass(frozen=True)
class Segment:
    root: Coord
    direction: Direction

    _canonical_tuple: tuple[Coord, Direction] = field(init=False)
    end: Coord = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "end", self.root + self.direction)
        is_canonical = self.direction.side == "EAST"
        canonical_root = self.root if is_canonical else self.end
        canonical_direction = (
            self.direction if is_canonical else self.direction.rotated(Angle.BACK)
        )
        object.__setattr__(
            self, "_canonical_tuple", (canonical_root, canonical_direction)
        )

    def __repr__(self) -> str:
        return f"{self.root}@{self.direction}"

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

    @property
    def min_s(self):
        return min(self.root.s, self.end.s)

    @property
    def max_s(self):
        return max(self.root.s, self.end.s)

    def shifted(self, other: Direction | Coord):
        return Segment(self.root.shifted(other), self.direction)

    def rotated(self, angle: Angle | str | int):
        return Segment(self.root.rotated(angle), self.direction.rotated(angle))

    def next_segment(self, angle: Angle | str | int):
        return Segment(self.end, self.direction.rotated(angle))

    def __hash__(self) -> int:
        return hash(self._canonical_tuple)

    def __eq__(self, other: Self) -> bool:
        return self._canonical_tuple == other._canonical_tuple


def get_pattern_points(
    direction: Direction, pattern: str
) -> Generator[Coord, None, None]:
    compass = direction
    cursor = compass.as_delta()

    yield Coord.origin()
    yield cursor

    for c in pattern:
        compass = compass.rotated(Angle[c])
        cursor += compass
        yield cursor


def get_pattern_segments(
    direction: Direction, pattern: str
) -> Generator[Segment, None, None]:
    cursor = Coord.origin()
    compass = direction

    yield Segment(cursor, compass)

    for c in pattern:
        cursor += compass
        compass = compass.rotated(Angle[c])
        yield Segment(cursor, compass)


def _align_segments_to_origin(segments: Iterable[Segment]) -> frozenset[Segment]:
    min_q = min(segment.min_q for segment in segments)
    min_r = min(segment.min_r for segment in segments)

    top_left = Coord(min_q, min_r)
    delta = Coord.origin() - top_left

    return frozenset([segment.shifted(delta) for segment in segments])


def get_aligned_pattern_segments(
    direction: Direction, pattern: str, align=True
) -> frozenset[Segment]:
    segments = frozenset(get_pattern_segments(direction, pattern))
    return _align_segments_to_origin(segments) if align else segments


def get_rotated_aligned_pattern_segments(
    direction: Direction, pattern: str
) -> Generator[frozenset[Segment], None, None]:
    segments = get_aligned_pattern_segments(direction, pattern, False)
    for n in range(6):
        yield _align_segments_to_origin([segment.rotated(n) for segment in segments])
