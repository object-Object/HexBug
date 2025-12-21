from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Any, Iterable, Iterator

from hex_renderer_py import PatternVariant
from pydantic import BeforeValidator, Field
from pydantic.dataclasses import dataclass as pydantic_dataclass

from .utils.enums import WrappingEnum, pydantic_enum

if TYPE_CHECKING:
    from HexBug.rendering.draw import RenderablePattern

PATTERN_SIGNATURE_MAX_LENGTH = 512

_VALID_SIGNATURE_PATTERN = re.compile(r"^[aqweds]*$")


@pydantic_enum
class HexDir(WrappingEnum):
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
            .strip()
            .replace("_", "")
            .replace("-", "")
            .replace("north", "n")
            .replace("south", "s")
            .replace("west", "w")
            .replace("east", "e")
        )

        return {
            "e": HexDir.EAST,
            "se": HexDir.SOUTH_EAST,
            "sw": HexDir.SOUTH_WEST,
            "w": HexDir.WEST,
            "nw": HexDir.NORTH_WEST,
            "ne": HexDir.NORTH_EAST,
        }.get(shorthand)

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

    def __neg__(self) -> HexDir:
        return self.rotated_by(HexAngle.BACK)


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

    def __neg__(self) -> HexAngle:
        return HexAngle(-self.value)


@dataclass(frozen=True)
class HexCoord:
    q: int
    r: int

    @classmethod
    def origin(cls) -> HexCoord:
        return HexCoord(0, 0)

    @property
    def s(self):
        return -self.q - self.r

    def shifted_by(self, other: HexCoord | HexDir) -> HexCoord:
        if isinstance(other, HexDir):
            other = other.delta
        return HexCoord(self.q + other.q, self.r + other.r)

    def rotated_by(self, angle: HexAngle) -> HexCoord:
        result = self
        for _ in range(angle.value):
            result = HexCoord(-result.r, -result.s)
        return result

    def delta(self, other: HexCoord) -> HexCoord:
        return HexCoord(self.q - other.q, self.r - other.r)

    def __add__(self, other: HexCoord | HexDir) -> HexCoord:
        return self.shifted_by(other)

    def __sub__(self, other: HexCoord) -> HexCoord:
        return self.delta(other)


@dataclass(frozen=True, eq=False)
class HexSegment:
    root: HexCoord
    direction: HexDir

    @property
    def end(self):
        return self.root.shifted_by(self.direction)

    @property
    def _canonical_values(self) -> tuple[HexCoord, HexDir]:
        if "EAST" in self.direction.name:
            return (self.root, self.direction)
        return (self.end, -self.direction)

    def shifted_by(self, other: HexCoord | HexDir) -> HexSegment:
        return HexSegment(self.root.shifted_by(other), self.direction)

    def rotated_by(self, angle: HexAngle) -> HexSegment:
        return HexSegment(self.root.rotated_by(angle), self.direction.rotated_by(angle))

    def __hash__(self) -> int:
        return hash(self._canonical_values)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, HexSegment):
            return False
        return self._canonical_values == other._canonical_values


def _before_validator_PatternSignature(value: Any):
    if isinstance(value, str):
        return value.strip().lower()
    return value


type PatternSignature = Annotated[
    str,
    BeforeValidator(_before_validator_PatternSignature),
    Field(
        pattern=_VALID_SIGNATURE_PATTERN,
        max_length=PATTERN_SIGNATURE_MAX_LENGTH,  # :/
    ),
]


@pydantic_dataclass(frozen=True)
class HexPattern:
    direction: HexDir
    signature: PatternSignature

    @classmethod
    def from_renderable(cls, renderable: RenderablePattern) -> HexPattern:
        match renderable:
            case HexPattern():
                return renderable
            case PatternVariant():
                return cls(
                    direction=HexDir[renderable.direction],
                    signature=renderable.angle_sigs,
                )

    def pattern_variant(self, great_spell: bool = False) -> PatternVariant:
        """Converts this pattern to a `PatternVariant` for use with hex_renderer_py."""
        return PatternVariant(
            direction=self.direction.name,
            angle_sigs=self.signature,
            great_spell=great_spell,
        )

    def display(self) -> str:
        return f"{self.direction.name} {self.signature}".rstrip()

    def iter_angles(self) -> Iterator[HexAngle]:
        for c in self.signature:
            yield HexAngle[c]

    def iter_directions(self) -> Iterator[HexDir]:
        compass = self.direction
        yield compass
        for angle in self.iter_angles():
            compass = compass.rotated_by(angle)
            yield compass

    def iter_segments(self) -> Iterator[HexSegment]:
        cursor = HexCoord.origin()
        compass = self.direction
        yield HexSegment(cursor, compass)

        for angle in self.iter_angles():
            cursor = cursor.shifted_by(compass)
            compass = compass.rotated_by(angle)
            yield HexSegment(cursor, compass)

    def get_aligned_segments(self) -> frozenset[HexSegment]:
        return align_segments_to_origin(self.iter_segments())


def align_segments_to_origin(segments: Iterable[HexSegment]) -> frozenset[HexSegment]:
    segments = list(segments)

    min_q = min(q for segment in segments for q in [segment.root.q, segment.end.q])
    min_r = min(r for segment in segments for r in [segment.root.r, segment.end.r])

    top_left = HexCoord(min_q, min_r)
    offset = HexCoord.origin() - top_left

    return frozenset(segment.shifted_by(offset) for segment in segments)
