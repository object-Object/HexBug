from ..hexdecode.hex_math import Direction
from ..hexdecode.registry import (
    NormalPatternInfo,
    PatternInfo,
    SpecialHandlerPatternInfo,
)
from .mods import HexdocMod, RegistryMod
from .special_handlers import (
    MaskSpecialHandler,
    NumberSpecialHandler,
    TailDepthSpecialHandler,
)

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
                shorthand_names=("{", "intro"),
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
                shorthand_names=("}", "retro"),
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
                handler=NumberSpecialHandler(),
            ),
            SpecialHandlerPatternInfo(
                name="mask",
                translation=name_to_translation.get("mask"),
                mod=RegistryMod.HexCasting,
                path="Common/src/main/java/at/petrak/hexcasting/common/casting/RegisterPatterns.java",
                classname="SpecialHandler",
                class_mod=RegistryMod.HexCasting,
                is_great=False,
                shorthand_names=("book",),
                handler=MaskSpecialHandler(),
            ),
            SpecialHandlerPatternInfo(
                name="nephthys",
                translation=name_to_translation.get("nephthys"),
                mod=HexdocMod.Hexical,
                path="src/main/java/miyucomics/hexical/casting/patterns/eval/OpNephthys.kt",
                classname="OpNephthys",
                class_mod=HexdocMod.Hexical,
                is_great=False,
                handler=TailDepthSpecialHandler(
                    direction=Direction.SOUTH_EAST,
                    prefix="deaqqd",
                    initial_depth=1,
                ),
            ),
            SpecialHandlerPatternInfo(
                name="sekhmet",
                translation=name_to_translation.get("sekhmet"),
                mod=HexdocMod.Hexical,
                path="src/main/java/miyucomics/hexical/casting/patterns/eval/OpSekhmet.kt",
                classname="OpSekhmet",
                class_mod=HexdocMod.Hexical,
                is_great=False,
                handler=TailDepthSpecialHandler(
                    direction=Direction.SOUTH_WEST,
                    prefix="qaqdd",
                    initial_depth=0,
                ),
            ),
        ]
    return _extra_patterns
