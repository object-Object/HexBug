from ..hexdecode.hex_math import Direction
from ..hexdecode.registry import (
    NormalPatternInfo,
    PatternInfo,
    SpecialHandlerPatternInfo,
)
from .mods import RegistryMod

_extra_patterns: list[PatternInfo] | None = None


# this is here and not in mods because otherwise registry and mods would depend on each other
def build_extra_patterns(name_to_translation: dict[str, str]) -> list[PatternInfo]:
    # cache the list so that if this function is called multiple times, it returns the same references
    global _extra_patterns
    if not _extra_patterns:
        _extra_patterns = [
            # https://github.com/gamma-delta/HexMod/blob/main/Common/src/main/java/at/petrak/hexcasting/api/spell/casting/SpecialPatterns.java
            # https://github.com/gamma-delta/HexMod/blob/main/Common/src/main/java/at/petrak/hexcasting/api/utils/PatternNameHelper.java
            NormalPatternInfo(
                name="open_paren",
                translation=name_to_translation.get("open_paren"),
                mod=RegistryMod.HexCasting,
                path="Common/src/main/java/at/petrak/hexcasting/api/spell/casting/CastingHarness.kt",
                classname="INTROSPECTION",
                class_mod=RegistryMod.HexCasting,
                is_great=False,
                direction=Direction.WEST,
                pattern="qqq",
            ),
            NormalPatternInfo(
                name="close_paren",
                translation=name_to_translation.get("close_paren"),
                mod=RegistryMod.HexCasting,
                path="Common/src/main/java/at/petrak/hexcasting/api/spell/casting/CastingHarness.kt",
                classname="RETROSPECTION",
                class_mod=RegistryMod.HexCasting,
                is_great=False,
                direction=Direction.EAST,
                pattern="eee",
            ),
            NormalPatternInfo(
                name="escape",
                translation=name_to_translation.get("escape"),
                mod=RegistryMod.HexCasting,
                path="Common/src/main/java/at/petrak/hexcasting/api/spell/casting/CastingHarness.kt",
                classname="CONSIDERATION",
                class_mod=RegistryMod.HexCasting,
                is_great=False,
                direction=Direction.WEST,
                pattern="qqqaw",
            ),
            SpecialHandlerPatternInfo(
                name="number",
                translation=name_to_translation.get("number"),
                mod=RegistryMod.HexCasting,
                path="Common/src/main/java/at/petrak/hexcasting/common/casting/RegisterPatterns.java",
                classname="SpecialHandler",
                class_mod=RegistryMod.HexCasting,
                is_great=False,
            ),
            SpecialHandlerPatternInfo(
                name="mask",
                translation=name_to_translation.get("mask"),
                mod=RegistryMod.HexCasting,
                path="Common/src/main/java/at/petrak/hexcasting/common/casting/RegisterPatterns.java",
                classname="SpecialHandler",
                class_mod=RegistryMod.HexCasting,
                is_great=False,
            ),
        ]
    return _extra_patterns
