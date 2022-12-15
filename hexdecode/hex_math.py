from __future__ import annotations

import math
from enum import Enum


class Angle(Enum):
    FORWARD = (0, "w")
    w = (0, "w")
    RIGHT = (1, "e")
    e = (1, "e")
    RIGHT_BACK = (2, "d")
    d = (2, "d")
    BACK = (3, "s")
    LEFT_BACK = (4, "a")
    a = (4, "a")
    LEFT = (5, "q")
    q = (5, "q")

    @classmethod
    def from_number(cls, num):
        return {0: cls.FORWARD, 1: cls.RIGHT, 2: cls.RIGHT_BACK, 3: cls.BACK, 4: cls.LEFT_BACK, 5: cls.LEFT}[
            num % len(Angle)
        ]

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

    def pixel(self, size: int) -> tuple[float, float]:
        return (size * (math.sqrt(3) * self.q + math.sqrt(3) / 2 * self.r), size * (3 / 2 * self.r))  # x  # y

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
