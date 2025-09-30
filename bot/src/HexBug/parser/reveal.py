from importlib import resources
from typing import TYPE_CHECKING, Any, Callable

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

if TYPE_CHECKING:

    def v_args[T](
        inline: bool = False,
        meta: bool = False,
        tree: bool = False,
    ) -> Callable[[T], T]: ...

else:
    from lark import v_args

GRAMMAR = (resources.files() / "reveal.lark").read_text("utf-8")

PARSER = Lark(
    GRAMMAR,
    parser="lalr",
    strict=True,
)


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


def parse_reveal(text: str) -> Iota:
    tree = PARSER.parse(text)
    return RevealTransformer().transform(tree)
