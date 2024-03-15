from __future__ import annotations

import importlib_resources as resources
from lark import Token
from lark.lark import Lark
from lark.visitors import Transformer

from .hex_math import Direction
from .hexast import Boolean, Null, NumberConstant, ParsedIota, UnknownPattern, Vector

_PARSER_GRAMMAR = (resources.files() / "revealparser.lark").read_text()

_parser = Lark(
    _PARSER_GRAMMAR,
    parser="lalr",
    strict=True,
)


class RevealTransformer(Transformer):
    # rules

    list = list

    def pattern(self, args: tuple[Direction] | tuple[Direction, Token]):
        match args:
            case (direction, angles):
                return UnknownPattern(direction, angles)
            case (direction,):
                return UnknownPattern(direction)

    def vector(self, args: list[NumberConstant]) -> Vector:
        return Vector(*args)

    # terminals

    def DIRECTION(self, token: Token):
        direction = Direction.from_shorthand(token.value)
        if direction is None:
            raise ValueError(f"Invalid direction: {token.value}")
        return direction

    def NUMBER(self, token: Token):
        return NumberConstant(float(token))

    def BOOLEAN(self, token: Token):
        return Boolean(token.value)

    NULL = Null


def parse_reveal(text: str) -> ParsedIota:
    tree = _parser.parse(text)
    ast = RevealTransformer().transform(tree)
    return ast.children[0]
