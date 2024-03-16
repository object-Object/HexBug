import pytest
from HexBug.hexdecode.hex_math import Direction
from HexBug.hexdecode.hexast import (
    Boolean,
    Matrix,
    Null,
    NumberConstant,
    ParsedIota,
    String,
    UnknownPattern,
    Vector,
)
from HexBug.hexdecode.revealparser import parse_reveal


@pytest.mark.parametrize(
    ["text", "want"],
    [
        ("0", NumberConstant(0)),
        ("1", NumberConstant(1)),
        ("-1", NumberConstant(-1)),
        ("23.45", NumberConstant(23.45)),
        ("-23.45", NumberConstant(-23.45)),
    ],
)
def test_number(text: str, want: ParsedIota):
    assert want == parse_reveal(text)


@pytest.mark.parametrize(
    ["text", "want"],
    [
        ("(0, 1, -2.5)", Vector.from_raw(0, 1, -2.5)),
    ],
)
def test_vector(text: str, want: ParsedIota):
    assert want == parse_reveal(text)


@pytest.mark.parametrize(
    ["text", "want"],
    [
        ("True", Boolean(True)),
        ("False", Boolean(False)),
        ("Null", Null()),
        ("NULL", Null()),
    ],
)
def test_bool_null(text: str, want: ParsedIota):
    assert want == parse_reveal(text)


@pytest.mark.parametrize(
    ["text", "want"],
    [
        ('""', String("")),
        ('"foo"', String("foo")),
        ('"\\"', String("\\")),
        ('"\\n"', String("\\n")),
    ],
)
def test_string(text: str, want: ParsedIota):
    assert want == parse_reveal(text)


@pytest.mark.parametrize(
    ["text", "want"],
    [
        ("[(0, 0)]", Matrix.from_rows()),
        ("[(1, 1) | 1.00]", Matrix.from_rows([1])),
        (
            "[(2, 3) | 0.00, 1.00, 2.00; 3.00, 4.00, 5.00]",
            Matrix.from_rows([0, 1, 2], [3, 4, 5]),
        ),
    ],
)
def test_matrix(text: str, want: ParsedIota):
    assert want == parse_reveal(text)


@pytest.mark.parametrize(
    ["text", "want"],
    [
        ("HexPattern(EAST)", UnknownPattern(Direction.EAST)),
        ("HexPattern(EAST aqweds)", UnknownPattern(Direction.EAST, "aqweds")),
        # Hex Gloop
        ("<east,>", UnknownPattern(Direction.EAST)),
        ("<east,w>", UnknownPattern(Direction.EAST, "w")),
        ("<east w>", UnknownPattern(Direction.EAST, "w")),
    ],
)
def test_pattern(text: str, want: ParsedIota):
    assert want == parse_reveal(text)


@pytest.mark.parametrize(
    ["text", "want"],
    [
        ("[]", []),
        ("[1]", [NumberConstant(1)]),
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
def test_list(text: str, want: ParsedIota):
    assert want == parse_reveal(text)
