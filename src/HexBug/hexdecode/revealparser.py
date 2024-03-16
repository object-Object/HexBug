from __future__ import annotations

from typing import Any

import importlib_resources as resources
from lark import Token, v_args
from lark.lark import Lark
from lark.visitors import Transformer
from pydantic import TypeAdapter

from .hex_math import Direction
from .hexast import (
    Iota,
    MatrixIota,
    NullIota,
    PatternIota,
    UnknownIota,
    VectorIota,
)

_PARSER_GRAMMAR = (resources.files() / "revealparser.lark").read_text()

_parser = Lark(
    _PARSER_GRAMMAR,
    parser="lalr",
    strict=True,
)


@v_args(inline=True)
class RevealTransformer(Transformer):
    pattern = PatternIota
    vector = VectorIota
    matrix = MatrixIota
    UNKNOWN = UnknownIota
    NUMBER = TypeAdapter(float).validate_python
    BOOLEAN = TypeAdapter(bool).validate_python

    def list(self, *values: Any):
        return list(values)

    def DIRECTION(self, token: Token):
        direction = Direction.from_shorthand(token.value)
        if direction is None:
            raise ValueError(f"Invalid direction: {token.value}")
        return direction

    def STRING(self, token: Token):
        # remove the leading and trailing quotes
        return token[1:-1]

    def NULL(self, _: Token):
        return NullIota()


def parse(text: str) -> Iota:
    tree = _parser.parse(text)
    ast = RevealTransformer().transform(tree)
    return ast.children[0]
