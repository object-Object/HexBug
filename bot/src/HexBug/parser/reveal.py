from importlib import resources
from typing import Any

from lark import Lark, Token, Transformer

from .ast import (
    BooleanIota,
    CallIota,
    Iota,
    JumpIota,
    ListIota,
    MatrixIota,
    NullIota,
    NumberIota,
    PatternIota,
    StringIota,
    UnknownIota,
    VectorIota,
)
from .helpers import v_args

_parser: Lark | None = None


@v_args(meta=True)
class RevealTransformer(Transformer[Token, Iota]):
    @v_args(inline=True)
    def start(self, iota: Iota):
        return iota

    @v_args()
    def matrix_rows(self, values: list[Any]):
        return values

    @v_args()
    def matrix_row(self, values: list[Any]):
        return values

    pattern = PatternIota.parse
    jump = JumpIota.parse
    call = CallIota.parse
    list = ListIota.parse
    vector = VectorIota.parse
    matrix = MatrixIota.parse
    number = NumberIota.parse
    boolean = BooleanIota.parse
    null = NullIota.parse
    string = StringIota.parse
    unknown = UnknownIota.parse


def load_reveal_parser() -> Lark:
    global _parser
    if _parser is None:
        grammar = (resources.files() / "reveal.lark").read_text("utf-8")
        _parser = Lark(
            grammar,
            parser="lalr",
            strict=True,
        )
    return _parser


def parse_reveal(text: str) -> Iota:
    tree = load_reveal_parser().parse(text)
    return RevealTransformer().transform(tree)
