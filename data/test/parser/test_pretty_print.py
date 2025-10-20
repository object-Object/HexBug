from textwrap import dedent
from typing import cast

import pytest

from HexBug.data.hex_math import HexDir
from HexBug.data.parsers.ast import (
    BubbleIota,
    Iota,
    ListIota,
    MatrixIota,
    NumberIota,
    PatternIota,
    VectorIota,
)
from HexBug.data.parsers.pretty_print import IotaPrinter
from HexBug.data.patterns import PatternInfo
from HexBug.data.registry import HexBugRegistry
from HexBug.data.static_data import INTROSPECTION, RETROSPECTION

MOCK_PATTERNS = {
    "w": PatternInfo.model_construct(name="Pattern 1"),
    "ww": PatternInfo.model_construct(name="Pattern 2"),
    "www": PatternInfo.model_construct(id=INTROSPECTION),
    "wwww": PatternInfo.model_construct(id=RETROSPECTION),
}


@pytest.fixture
def registry() -> HexBugRegistry:
    class MockRegistry:
        def try_match_pattern(self, direction: HexDir, signature: str):
            return MOCK_PATTERNS.get(signature)

    return cast(HexBugRegistry, MockRegistry())  # lie


@pytest.mark.parametrize(
    ["iota", "want"],
    [
        (PatternIota(HexDir.EAST, "w"), "Pattern 1"),
        (PatternIota(HexDir.EAST, "www"), "{"),
        (PatternIota(HexDir.EAST, "wwww"), "}"),
        (PatternIota(HexDir.EAST, ""), "HexPattern(EAST)"),
        (PatternIota(HexDir.EAST, "a"), "HexPattern(EAST a)"),
        (
            MatrixIota.from_rows(
                [1, 2.12345, 3],
                [40, 5, 6],
            ),
            dedent(
                """
                [(2, 3) |
                    1  2.1235 3
                    40 5      6
                ]
                """
            ),
        ),
        (
            ListIota([
                PatternIota(HexDir.EAST, "w"),
                PatternIota(HexDir.EAST, "ww"),
                PatternIota(HexDir.EAST, "www"),
                PatternIota(HexDir.EAST, "www"),
                PatternIota(HexDir.EAST, "w"),
                PatternIota(HexDir.EAST, "wwww"),
                PatternIota(HexDir.EAST, "wwww"),
                PatternIota(HexDir.EAST, "wwww"),
                PatternIota(HexDir.EAST, "w"),
                ListIota([
                    NumberIota(0),
                ]),
                PatternIota(HexDir.EAST, "www"),
                PatternIota(HexDir.EAST, "www"),
                BubbleIota(ListIota([VectorIota(1, 2, 3)])),
                PatternIota(HexDir.EAST, "w"),
            ]),
            dedent(
                """
                [
                    Pattern 1
                    Pattern 2
                    {
                        {
                            Pattern 1
                        }
                    }
                    }
                    Pattern 1
                    [
                        0
                    ]
                    {
                    {
                        {[(1, 2, 3)]}
                        Pattern 1
                ]
                """
            ),
        ),
    ],
)
def test_pretty_print(iota: Iota, want: str, registry: HexBugRegistry):
    assert IotaPrinter(registry).pretty_print(iota) == want.strip()


@pytest.mark.parametrize(
    ["iota", "want"],
    [
        (PatternIota(HexDir.EAST, "w"), "Pattern 1"),
        (PatternIota(HexDir.EAST, "www"), "{"),
        (PatternIota(HexDir.EAST, "wwww"), "}"),
        (PatternIota(HexDir.EAST, ""), "HexPattern(EAST)"),
        (PatternIota(HexDir.EAST, "a"), "HexPattern(EAST a)"),
        (
            MatrixIota.from_rows(
                [1, 2.12345, 3],
                [40, 5, 6],
            ),
            dedent(
                """
                [(2, 3) |
                    1  2.1235 3
                    40 5      6
                ]
                """
            ),
        ),
        (
            ListIota([
                NumberIota(0),
                PatternIota(HexDir.EAST, "w"),
                PatternIota(HexDir.EAST, "ww"),
                PatternIota(HexDir.EAST, "www"),
                PatternIota(HexDir.EAST, "www"),
                PatternIota(HexDir.EAST, "w"),
                PatternIota(HexDir.EAST, "wwww"),
                PatternIota(HexDir.EAST, "wwww"),
                PatternIota(HexDir.EAST, "wwww"),
                PatternIota(HexDir.EAST, "w"),
                ListIota([
                    NumberIota(0),
                ]),
                PatternIota(HexDir.EAST, "www"),
                PatternIota(HexDir.EAST, "www"),
                BubbleIota(ListIota([VectorIota(1, 2, 3)])),
                PatternIota(HexDir.EAST, "w"),
            ]),
            dedent(
                """
                <0>
                Pattern 1
                Pattern 2
                {
                    {
                        Pattern 1
                    }
                }
                }
                Pattern 1
                <[
                    0
                ]>
                {
                {
                    <{[(1, 2, 3)]}>
                    Pattern 1
                """
            ),
        ),
    ],
)
def test_pretty_print_flattened(iota: Iota, want: str, registry: HexBugRegistry):
    assert IotaPrinter(registry).pretty_print(iota, flatten_list=True) == want.strip()
