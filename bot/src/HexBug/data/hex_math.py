from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from pydantic import Field
from pydantic.dataclasses import dataclass as pydantic_dataclass

from HexBug.utils.enums import WrappingEnum, pydantic_enum


@pydantic_enum
class HexDir(WrappingEnum):
    NORTH_EAST = 0
    EAST = 1
    SOUTH_EAST = 2
    SOUTH_WEST = 3
    WEST = 4
    NORTH_WEST = 5

    @property
    def delta(self) -> HexCoord:
        match self:
            case HexDir.NORTH_EAST:
                return HexCoord(1, -1)
            case HexDir.EAST:
                return HexCoord(1, 0)
            case HexDir.SOUTH_EAST:
                return HexCoord(0, 1)
            case HexDir.SOUTH_WEST:
                return HexCoord(-1, 1)
            case HexDir.WEST:
                return HexCoord(-1, 0)
            case HexDir.NORTH_WEST:
                return HexCoord(0, -1)

    def rotated_by(self, angle: HexAngle) -> HexDir:
        return HexDir(self.value + angle.value)

    def angle_from(self, other: HexDir) -> HexAngle:
        return HexAngle(self.value - other.value)


@pydantic_enum
class HexAngle(WrappingEnum):
    FORWARD = 0
    RIGHT = 1
    RIGHT_BACK = 2
    BACK = 3
    LEFT_BACK = 4
    LEFT = 5

    w = FORWARD
    e = RIGHT
    d = RIGHT_BACK
    s = BACK
    a = LEFT_BACK
    q = LEFT

    @property
    def letter(self) -> str:
        match self:
            case HexAngle.FORWARD:
                return "w"
            case HexAngle.RIGHT:
                return "e"
            case HexAngle.RIGHT_BACK:
                return "d"
            case HexAngle.BACK:
                return "s"
            case HexAngle.LEFT_BACK:
                return "a"
            case HexAngle.LEFT:
                return "q"

    def rotated_by(self, other: HexAngle) -> HexAngle:
        return HexAngle(self.value + other.value)


@dataclass
class HexCoord:
    q: int
    r: int

    @property
    def s(self):
        return -self.q - self.r


@pydantic_dataclass
class HexPattern:
    direction: HexDir
    signature: str = Field(pattern=r"[aqweds]*")

    def iter_angles(self) -> Iterator[HexAngle]:
        for c in self.signature:
            yield HexAngle[c.lower()]

    def iter_directions(self) -> Iterator[HexDir]:
        compass = self.direction
        yield compass
        for angle in self.iter_angles():
            compass = compass.rotated_by(angle)
            yield compass
