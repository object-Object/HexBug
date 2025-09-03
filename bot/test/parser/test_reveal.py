import pytest

from HexBug.data.hex_math import HexDir
from HexBug.parser.ast import (
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
from HexBug.parser.reveal import parse


@pytest.mark.parametrize(
    ["text", "want"],
    [
        ("0", NumberIota(0)),
        ("1", NumberIota(1)),
        ("-1", NumberIota(-1)),
        ("23.45", NumberIota(23.45)),
        ("-23.45", NumberIota(-23.45)),
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
        ("True", BooleanIota(True)),
        ("False", BooleanIota(False)),
        ("Null", NullIota()),
        ("NULL", NullIota()),
    ],
)
def test_bool_null(text: str, want: Iota):
    assert want == parse(text)


@pytest.mark.parametrize(
    ["text", "want"],
    [
        ('""', StringIota("")),
        ('"foo"', StringIota("foo")),
        ('"\\"', StringIota("\\")),
        ('"\\n"', StringIota("\\n")),
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
        ("HexPattern(EAST)", PatternIota(HexDir.EAST)),
        ("HexPattern(EAST aqweds)", PatternIota(HexDir.EAST, "aqweds")),
        # Hex Gloop
        ("<east,>", PatternIota(HexDir.EAST)),
        ("<east,w>", PatternIota(HexDir.EAST, "w")),
        ("<east w>", PatternIota(HexDir.EAST, "w")),
        # Hex 0.11.2
        ("HexPattern[EAST, ]", PatternIota(HexDir.EAST)),
        ("HexPattern[EAST, w]", PatternIota(HexDir.EAST, "w")),
        ("HexPattern[EAST, aqweds]", PatternIota(HexDir.EAST, "aqweds")),
    ],
)
def test_pattern(text: str, want: Iota):
    assert want == parse(text)


@pytest.mark.parametrize(
    ["text", "want"],
    [
        ("[]", ListIota([])),
        ("[1]", ListIota([NumberIota(1)])),
        ("[1, 2]", ListIota([NumberIota(1), NumberIota(2)])),
        # latest.log
        (
            "[HexPattern(EAST), HexPattern(SOUTH_WEST w), 0.00]",
            ListIota([
                PatternIota(HexDir.EAST),
                PatternIota(HexDir.SOUTH_WEST, "w"),
                NumberIota(0),
            ]),
        ),
        # latest.log (Hex Gloop)
        (
            "[HexPattern(EAST) HexPattern(SOUTH_WEST w), 0.00]",
            ListIota([
                PatternIota(HexDir.EAST),
                PatternIota(HexDir.SOUTH_WEST, "w"),
                NumberIota(0),
            ]),
        ),
        # latest.log (older Hex Gloop versions)
        (
            "[HexPattern(EAST) HexPattern(SOUTH_WEST w), 0.00]",
            ListIota([
                PatternIota(HexDir.EAST),
                PatternIota(HexDir.SOUTH_WEST, "w"),
                NumberIota(0),
            ]),
        ),
        # list copied from chat (Hex Gloop)
        (
            "[<east,>, <southwest,w>, 0.00]",
            ListIota([
                PatternIota(HexDir.EAST),
                PatternIota(HexDir.SOUTH_WEST, "w"),
                NumberIota(0),
            ]),
        ),
        # latest.log (Hex 0.11.2)
        (
            "[HexPattern[EAST, ]HexPattern[SOUTH_WEST, w], 0.00]",
            ListIota([
                PatternIota(HexDir.EAST),
                PatternIota(HexDir.SOUTH_WEST, "w"),
                NumberIota(0),
            ]),
        ),
        (
            "[HexPattern[EAST, ]HexPattern[EAST, w]HexPattern[NORTH_EAST, qaq]HexPattern[WEST, qqqaw]]",
            ListIota([
                PatternIota(HexDir.EAST),
                PatternIota(HexDir.EAST, "w"),
                PatternIota(HexDir.NORTH_EAST, "qaq"),
                PatternIota(HexDir.WEST, "qqqaw"),
            ]),
        ),
        (
            "[0.00, HexPattern[EAST, ], [HexPattern[NORTH_EAST, qaq]HexPattern[EAST, aa]]]",
            ListIota([
                NumberIota(0),
                PatternIota(HexDir.EAST),
                ListIota([
                    PatternIota(HexDir.NORTH_EAST, "qaq"),
                    PatternIota(HexDir.EAST, "aa"),
                ]),
            ]),
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
            ListIota([
                PatternIota(HexDir.EAST, "w"),
                UnknownIota("Player"),
                NumberIota(0),
            ]),
        ),
    ],
)
def test_unknown(text: str, want: Iota):
    assert want == parse(text)


@pytest.mark.parametrize(
    ["text", "want"],
    [
        ("[Jump]", JumpIota([])),
        ("[Jump -> ()]", JumpIota([])),
        ("[Jump -> (Evaluate)]", JumpIota(["Evaluate"])),
        ("[Jump -> (Evaluate*)]", JumpIota(["Evaluate*"])),
        ("[Jump -> (Evaluate, FinishEval)]", JumpIota(["Evaluate", "FinishEval"])),
        ("[Jump -> (Evaluate*, FinishEval)]", JumpIota(["Evaluate*", "FinishEval"])),
    ],
)
def test_jump(text: str, want: Iota):
    assert want == parse(text)


@pytest.mark.parametrize(
    ["text", "want"],
    [
        ("[Call -> ()]", CallIota([])),
        ("[Call -> (Evaluate)]", CallIota(["Evaluate"])),
        ("[Call -> (Evaluate*)]", CallIota(["Evaluate*"])),
        ("[Call -> (Evaluate, FinishEval)]", CallIota(["Evaluate", "FinishEval"])),
        ("[Call -> (Evaluate*, FinishEval)]", CallIota(["Evaluate*", "FinishEval"])),
    ],
)
def test_call(text: str, want: Iota):
    assert want == parse(text)
