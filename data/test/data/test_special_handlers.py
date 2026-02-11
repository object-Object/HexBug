from typing import cast

import pytest
from hexdoc.core import ResourceLocation

from HexBug.data.hex_math import HexDir, HexPattern
from HexBug.data.registry import HexBugRegistry
from HexBug.data.special_handlers import (
    HexFlowCopyMaskSpecialHandler,
    MaskSpecialHandler,
)


def describe_MaskSpecialHandler():
    @pytest.fixture()
    def special_handler() -> MaskSpecialHandler:
        return MaskSpecialHandler(ResourceLocation("hexcasting", "mask"))

    patterns = [
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
    ]

    @pytest.mark.parametrize("direction", HexDir)
    @pytest.mark.parametrize(
        ["signature", "want_value"],
        [
            *patterns,
            ("d", None),
            ("da", None),
            ("dad", None),
            ("eqqe", None),
            ("ed", None),
            ("eaa", None),
            ("eaa", None),
            ("q", None),
            ("d", None),
            ("e", None),
        ],
        ids=lambda v: f"'{v}'",
    )
    def try_match(
        special_handler: MaskSpecialHandler,
        direction: HexDir,
        signature: str,
        want_value: str | None,
    ):
        pattern = HexPattern(direction, signature)
        assert special_handler.try_match(pattern) == want_value

    @pytest.mark.parametrize(
        ["value", "want_signature"],
        [(value, signature) for (signature, value) in patterns],
    )
    def generate_pattern(
        special_handler: MaskSpecialHandler,
        value: str,
        want_signature: str,
    ):
        registry = cast(HexBugRegistry, None)  # lie
        _, pattern = special_handler.generate_pattern(registry, value)
        assert pattern.signature == want_signature


def describe_HexFlowCopyMaskSpecialHandler():
    @pytest.fixture()
    def special_handler() -> HexFlowCopyMaskSpecialHandler:
        return HexFlowCopyMaskSpecialHandler(ResourceLocation("hexflow", "copy_mask"))

    patterns = [
        ("aadaqq", "-"),
        ("aadaqqw", "--"),
        ("aadaqqww", "---"),
        ("aadaqad", "n"),
        ("aadaqadad", "nn"),
        ("aadaqadadad", "nnn"),
        ("aadaqqqd", "-n"),
        ("aadaqadq", "n-"),
        ("aadaqqqdq", "-n-"),
        ("aadaqadqqd", "n-n"),
        ("aadaqqwqd", "--n"),
        ("aadaqadqw", "n--"),
        ("aadaqqqdad", "-nn"),
        ("aadaqadadq", "nn-"),
    ]

    @pytest.mark.parametrize("direction", HexDir)
    @pytest.mark.parametrize(
        ["signature", "want_value"],
        [
            *patterns,
            ("aadaq", None),
        ],
        ids=lambda v: f"'{v}'",
    )
    def try_match(
        special_handler: HexFlowCopyMaskSpecialHandler,
        direction: HexDir,
        signature: str,
        want_value: str | None,
    ):
        pattern = HexPattern(direction, signature)
        assert special_handler.try_match(pattern) == want_value

    @pytest.mark.parametrize(
        ["value", "want_signature"],
        [(value, signature) for (signature, value) in patterns],
    )
    def generate_pattern(
        special_handler: HexFlowCopyMaskSpecialHandler,
        value: str,
        want_signature: str,
    ):
        registry = cast(HexBugRegistry, None)  # lie
        _, pattern = special_handler.generate_pattern(registry, value)
        assert pattern.signature == want_signature
