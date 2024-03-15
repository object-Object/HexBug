import pytest
from HexBug.hexdecode.hex_math import Direction
from HexBug.hexdecode.hexast import (
    Boolean,
    Null,
    NumberConstant,
    UnknownPattern,
    Vector,
)
from HexBug.hexdecode.revealparser import ParsedIota, parse_reveal


@pytest.mark.parametrize(
    ["text", "want"],
    [
        # numbers
        ("0", NumberConstant(0)),
        ("1", NumberConstant(1)),
        ("-1", NumberConstant(-1)),
        ("23.45", NumberConstant(23.45)),
        ("-23.45", NumberConstant(-23.45)),
        # vectors
        (
            "(0, 1, -2.5)",
            Vector(NumberConstant(0), NumberConstant(1), NumberConstant(-2.5)),
        ),
        # true/false/null
        ("True", Boolean("True")),
        ("False", Boolean("False")),
        ("Null", Null("Null")),
        ("NULL", Null("NULL")),
        # default patterns
        ("HexPattern(EAST)", UnknownPattern(Direction.EAST)),
        ("HexPattern(EAST aqweds)", UnknownPattern(Direction.EAST, "aqweds")),
        # Hex Gloop patterns
        ("<east,>", UnknownPattern(Direction.EAST)),
        ("<east,w>", UnknownPattern(Direction.EAST, "w")),
        ("<east w>", UnknownPattern(Direction.EAST, "w")),
        # lists
        ("[]", []),
        ("[1]", [NumberConstant(1)]),
        ("[1,]", [NumberConstant(1)]),
        ("[1, 2]", [NumberConstant(1), NumberConstant(2)]),
        # latest.log
        (
            "[HexPattern(EAST), HexPattern(SOUTH_WEST w), 0.00]",
            [
                UnknownPattern(Direction.EAST),
                UnknownPattern(Direction.SOUTH_WEST, "w"),
                NumberConstant(0),
            ],
        ),
        # latest.log (Hex Gloop)
        (
            "[HexPattern(EAST) HexPattern(SOUTH_WEST w), 0.00]",
            [
                UnknownPattern(Direction.EAST),
                UnknownPattern(Direction.SOUTH_WEST, "w"),
                NumberConstant(0),
            ],
        ),
        # latest.log (older Hex Gloop versions)
        (
            "[HexPattern(EAST) HexPattern(SOUTH_WEST w), 0.00]",
            [
                UnknownPattern(Direction.EAST),
                UnknownPattern(Direction.SOUTH_WEST, "w"),
                NumberConstant(0),
            ],
        ),
        # list copied from chat (Hex Gloop)
        (
            "[<east,>, <southwest,w>, 0.00]",
            [
                UnknownPattern(Direction.EAST),
                UnknownPattern(Direction.SOUTH_WEST, "w"),
                NumberConstant(0),
            ],
        ),
    ],
)
def test_parser(text: str, want: ParsedIota):
    got = parse_reveal(text)
    assert want == got
