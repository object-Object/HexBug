import pytest
from HexBug.hexdecode.hex_math import Direction
from HexBug.hexdecode.hexast import (
    Iota,
    MatrixIota,
    NullIota,
    PatternIota,
    UnknownIota,
    VectorIota,
)
from HexBug.hexdecode.revealparser import parse


@pytest.mark.parametrize(
    ["text", "want"],
    [
        ("0", 0),
        ("1", 1),
        ("-1", -1),
        ("23.45", 23.45),
        ("-23.45", -23.45),
    ],
)
def test_number(text: str, want: Iota):
    assert want == parse(text)


@pytest.mark.parametrize(
    ["text", "want"],
    [
        ("(0, 1, -2.5)", VectorIota(0, 1, -2.5)),
    ],
)
def test_vector(text: str, want: Iota):
    assert want == parse(text)


@pytest.mark.parametrize(
    ["text", "want"],
    [
        ("True", True),
        ("False", False),
        ("Null", NullIota()),
        ("NULL", NullIota()),
    ],
)
def test_bool_null(text: str, want: Iota):
    assert want == parse(text)


@pytest.mark.parametrize(
    ["text", "want"],
    [
        ('""', ""),
        ('"foo"', "foo"),
        ('"\\"', "\\"),
        ('"\\n"', "\\n"),
    ],
)
def test_string(text: str, want: Iota):
    assert want == parse(text)


@pytest.mark.parametrize(
    ["text", "want"],
    [
        ("[(0, 0)]", MatrixIota.from_rows()),
        ("[(1, 1) | 1.00]", MatrixIota.from_rows([1])),
        (
            "[(2, 3) | 0.00, 1.00, 2.00; 3.00, 4.00, 5.00]",
            MatrixIota.from_rows([0, 1, 2], [3, 4, 5]),
        ),
    ],
)
def test_matrix(text: str, want: Iota):
    assert want == parse(text)


@pytest.mark.parametrize(
    ["text", "want"],
    [
        ("HexPattern(EAST)", PatternIota(Direction.EAST)),
        ("HexPattern(EAST aqweds)", PatternIota(Direction.EAST, "aqweds")),
        # Hex Gloop
        ("<east,>", PatternIota(Direction.EAST)),
        ("<east,w>", PatternIota(Direction.EAST, "w")),
        ("<east w>", PatternIota(Direction.EAST, "w")),
        # Hex 0.11.2
        ("HexPattern[EAST, ]", PatternIota(Direction.EAST)),
        ("HexPattern[EAST, w]", PatternIota(Direction.EAST, "w")),
        ("HexPattern[EAST, aqweds]", PatternIota(Direction.EAST, "aqweds")),
    ],
)
def test_pattern(text: str, want: Iota):
    assert want == parse(text)


@pytest.mark.parametrize(
    ["text", "want"],
    [
        ("[]", []),
        ("[1]", [1]),
        ("[1, 2]", [1, 2]),
        # latest.log
        (
            "[HexPattern(EAST), HexPattern(SOUTH_WEST w), 0.00]",
            [
                PatternIota(Direction.EAST),
                PatternIota(Direction.SOUTH_WEST, "w"),
                0,
            ],
        ),
        # latest.log (Hex Gloop)
        (
            "[HexPattern(EAST) HexPattern(SOUTH_WEST w), 0.00]",
            [
                PatternIota(Direction.EAST),
                PatternIota(Direction.SOUTH_WEST, "w"),
                0,
            ],
        ),
        # latest.log (older Hex Gloop versions)
        (
            "[HexPattern(EAST) HexPattern(SOUTH_WEST w), 0.00]",
            [
                PatternIota(Direction.EAST),
                PatternIota(Direction.SOUTH_WEST, "w"),
                0,
            ],
        ),
        # list copied from chat (Hex Gloop)
        (
            "[<east,>, <southwest,w>, 0.00]",
            [
                PatternIota(Direction.EAST),
                PatternIota(Direction.SOUTH_WEST, "w"),
                0,
            ],
        ),
        # latest.log (Hex 0.11.2)
        (
            "[HexPattern[EAST, ]HexPattern[SOUTH_WEST, w], 0.00]",
            [
                PatternIota(Direction.EAST),
                PatternIota(Direction.SOUTH_WEST, "w"),
                0,
            ],
        ),
        (
            "[HexPattern[EAST, ]HexPattern[EAST, w]HexPattern[NORTH_EAST, qaq]HexPattern[WEST, qqqaw]]",
            [
                PatternIota(Direction.EAST),
                PatternIota(Direction.EAST, "w"),
                PatternIota(Direction.NORTH_EAST, "qaq"),
                PatternIota(Direction.WEST, "qqqaw"),
            ],
        ),
        (
            "[0.00, HexPattern[EAST, ], [HexPattern[NORTH_EAST, qaq]HexPattern[EAST, aa]]]",
            [
                0,
                PatternIota(Direction.EAST),
                [
                    PatternIota(Direction.NORTH_EAST, "qaq"),
                    PatternIota(Direction.EAST, "aa"),
                ],
            ],
        ),
    ],
)
def test_list(text: str, want: Iota):
    assert want == parse(text)


@pytest.mark.parametrize(
    ["text", "want"],
    [
        ("Player", UnknownIota("Player")),
        (
            "[<east,w>, Player, 0.00]",
            [
                PatternIota(Direction.EAST, "w"),
                UnknownIota("Player"),
                0,
            ],
        ),
    ],
)
def test_unknown(text: str, want: Iota):
    assert want == parse(text)
