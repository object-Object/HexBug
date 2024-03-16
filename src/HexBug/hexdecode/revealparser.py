from __future__ import annotations

from typing import Any

import importlib_resources as resources
from lark import Token, v_args
from lark.lark import Lark
from lark.visitors import Transformer

from .hex_math import Direction
from .hexast import (
    Boolean,
    Matrix,
    Null,
    NumberConstant,
    ParsedIota,
    String,
    UnknownPattern,
    Vector,
)

_PARSER_GRAMMAR = (resources.files() / "revealparser.lark").read_text()

_parser = Lark(
    _PARSER_GRAMMAR,
    parser="lalr",
    strict=True,
)


@v_args(inline=True)
class RevealTransformer(Transformer):
    pattern = UnknownPattern
    vector = Vector
    NUMBER = NumberConstant
    BOOLEAN = Boolean
    NULL = Null

    def list(self, *values: Any):
        return list(values)

    def matrix(self, rows: Token, columns: Token, *data: list[NumberConstant]):
        return Matrix(
            rows=int(rows),
            columns=int(columns),
            data=[[float(value._datum) for value in row] for row in data],
        )

    def DIRECTION(self, token: Token):
        direction = Direction.from_shorthand(token.value)
        if direction is None:
            raise ValueError(f"Invalid direction: {token.value}")
        return direction

    def STRING(self, token: Token):
        # remove the leading and trailing quotes
        return String(token[1:-1])


def parse_reveal(text: str) -> ParsedIota:
    tree = _parser.parse(text)
    ast = RevealTransformer().transform(tree)
    return ast.children[0]
