from typing import Any

from hexdoc.core import ResourceLocation
from yarl import URL

from .hex_math import HexDir
from .mods import Modloader, StaticModInfo
from .patterns import StaticPatternInfo
from .special_handlers import MaskSpecialHandler, NumberSpecialHandler, SpecialHandler

MODS: list[StaticModInfo] = [
    StaticModInfo(
        id="hexcasting",
        name="Hex Casting",
        description="A mod for Forge and Fabric adding stack-based programmable spellcasting, inspired by Psi.",
        icon_url=URL(
            "https://media.forgecdn.net/avatars/thumbnails/535/944/64/64/637857298951404372.png"
        ),
        curseforge_slug="hexcasting",
        modrinth_slug="hex-casting",
        modloaders=[Modloader.FABRIC, Modloader.FORGE, Modloader.QUILT],
    ),
]

EXTRA_PATTERNS: list[StaticPatternInfo] = [
    StaticPatternInfo(
        id=ResourceLocation("hexcasting", "escape"),
        startdir=HexDir.WEST,
        signature="qqqaw",
    ),
    StaticPatternInfo(
        id=ResourceLocation("hexcasting", "open_paren"),
        startdir=HexDir.WEST,
        signature="qqq",
    ),
    StaticPatternInfo(
        id=ResourceLocation("hexcasting", "close_paren"),
        startdir=HexDir.WEST,
        signature="eee",
    ),
    StaticPatternInfo(
        id=ResourceLocation("hexcasting", "undo"),
        startdir=HexDir.WEST,
        signature="eeedw",
    ),
]

SPECIAL_HANDLERS: list[SpecialHandler[Any]] = [
    NumberSpecialHandler(
        id=ResourceLocation("hexcasting", "number"),
    ),
    MaskSpecialHandler(
        id=ResourceLocation("hexcasting", "mask"),
    ),
]
