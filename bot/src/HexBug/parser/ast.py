from __future__ import annotations

from abc import ABC
from dataclasses import InitVar
from typing import Any, Self

from lark import Token
from lark.tree import Meta
from pydantic import Field, field_validator, model_validator
from pydantic.dataclasses import dataclass

from HexBug.data.hex_math import HexDir, PatternSignature


@dataclass
class BaseIota(ABC):
    _meta: InitVar[Meta | None] = Field(
        default=None,
        init_var=True,
        kw_only=True,
    )

    def __post_init__(self, meta: Meta | None = None):
        self.meta: Meta | None = meta

    @classmethod
    def parse(cls, meta: Meta, tokens: list[Token]) -> Self:
        return cls(*tokens, _meta=meta)


@dataclass
class PatternIota(BaseIota):
    direction: HexDir
    signature: PatternSignature = ""

    @field_validator("direction", mode="before")
    @classmethod
    def _uppercase_direction(cls, value: str | Any):
        if isinstance(value, str):
            value = value.upper()
            if value.startswith(("NORTH", "SOUTH")) and "_" not in value:
                value = value[:5] + "_" + value[5:]
        return value


@dataclass
class JumpIota(BaseIota):
    frames: list[str]

    @classmethod
    def parse(cls, meta: Meta, tokens: list[Any]) -> Self:
        return cls(tokens, _meta=meta)


@dataclass
class CallIota(BaseIota):
    frames: list[str]

    @classmethod
    def parse(cls, meta: Meta, tokens: list[Any]) -> Self:
        return cls(tokens, _meta=meta)


@dataclass
class ListIota(BaseIota):
    values: list[Iota]

    @classmethod
    def parse(cls, meta: Meta, tokens: list[Any]) -> Self:
        return cls(tokens, _meta=meta)


@dataclass
class VectorIota(BaseIota):
    x: float
    y: float
    z: float


@dataclass
class MatrixIota(BaseIota):
    rows: int
    """m"""
    columns: int
    """n"""
    data: list[list[float]]

    @classmethod
    def parse(cls, meta: Meta, tokens: list[Any]) -> Self:
        if len(tokens) > 2:
            rows, columns, data = tokens
        else:
            rows, columns = tokens
            data = list[Any]()
        return cls(rows, columns, data, _meta=meta)

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


@dataclass
class NumberIota(BaseIota):
    value: float


@dataclass
class BooleanIota(BaseIota):
    value: bool


@dataclass
class NullIota(BaseIota):
    pass


@dataclass
class StringIota(BaseIota):
    value: str

    @field_validator("value", mode="after")
    @classmethod
    def _strip_quotes(cls, value: str) -> str:
        if value and value[0] == value[-1] == '"':
            return value[1:-1]
        return value


@dataclass
class UnknownIota(BaseIota):
    value: str


type Iota = (
    PatternIota
    | JumpIota
    | CallIota
    | ListIota
    | VectorIota
    | MatrixIota
    | NumberIota
    | BooleanIota
    | NullIota
    | StringIota
    | UnknownIota
)
