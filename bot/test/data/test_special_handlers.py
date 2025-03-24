import pytest
from hexdoc.core import ResourceLocation

from HexBug.data.hex_math import HexDir, HexPattern
from HexBug.data.special_handlers import MaskSpecialHandler


def describe_MaskSpecialHandler():
    @pytest.fixture
    def special_handler() -> MaskSpecialHandler:
        return MaskSpecialHandler(ResourceLocation("hexcasting", "mask"))

    @pytest.mark.parametrize("direction", HexDir)
    @pytest.mark.parametrize(
        ["signature", "want_value"],
        [
            ("", "-"),
            ("w", "--"),
            ("ww", "---"),
            ("a", "v"),
            ("ada", "vv"),
            ("adada", "vvv"),
            ("ea", "-v"),
            ("ae", "v-"),
            ("eae", "-v-"),
            ("aeea", "v-v"),
            ("wea", "--v"),
            ("aew", "v--"),
            ("eada", "-vv"),
            ("adae", "vv-"),
            ("d", None),
            ("da", None),
            ("dad", None),
            ("eqqe", None),
            ("ed", None),
            ("eaa", None),
            ("eaa", None),
            ("q", None),
            ("d", None),
        ],
        ids=lambda v: f"'{v}'",
    )
    def value(
        special_handler: MaskSpecialHandler,
        direction: HexDir,
        signature: str,
        want_value: str | None,
    ):
        pattern = HexPattern(direction, signature)
        assert special_handler.try_match(pattern) == want_value
