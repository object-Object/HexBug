from __future__ import annotations

import re
from itertools import pairwise
from typing import Any

from lark import Token
from pydantic import Field, field_validator, model_validator
from pydantic.dataclasses import dataclass

from .hex_math import Direction

localize_regex = re.compile(r"((?:number|mask))(: .+)")


@dataclass
class BaseIota:
    @field_validator("*", mode="before")
    @classmethod
    def _stringify_tokens(cls, value: Any):
        match value:
            case Token():
                return value.value
            case _:
                return value


@dataclass
class PatternIota(BaseIota):
    direction: Direction
    pattern: str = ""

    def __str__(self) -> str:
        return f"<{self.direction.name},{self.pattern}>"


@dataclass
class VectorIota(BaseIota):
    x: float
    y: float
    z: float

    def __str__(self) -> str:
        return f"({self.x}, {self.y}, {self.z})"


@dataclass
class MatrixIota(BaseIota):
    rows: int
    """m"""
    columns: int
    """n"""
    data: list[list[float]] = Field(default_factory=list)
    """rows"""

    @classmethod
    def from_rows(cls, *data: list[float]):
        return cls(
            rows=len(data),
            columns=len(data[0]) if data else 0,
            data=list(data),
        )

    @model_validator(mode="after")
    def _validate_dimensions(self):
        if len(self.data) != self.rows:
            raise ValueError(
                f"Invalid number of rows (expected {self.rows}, got {len(self.data)}): {self.data}"
            )

        for row in self.data:
            if len(row) != self.columns:
                raise ValueError(
                    f"Invalid number of columns (expected {self.columns}, got {len(row)}): {row}"
                )

        return self

    def __str__(self) -> str:
        shape = f"({self.rows}, {self.columns})"
        if not self.data:
            return f"[{shape}]"

        values = "; ".join(", ".join(str(v) for v in row) for row in self.data)
        return f"[{shape} | {values}]"


@dataclass
class NullIota(BaseIota):
    def __str__(self) -> str:
        return "NULL"


Iota = (
    list["Iota"] | PatternIota | VectorIota | MatrixIota | NullIota | float | bool | str
)


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
