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
    StaticModInfo(
        id="hexal",
        name="Hexal",
        description="Adds complex numbers, quaternions, BIT displays, and bubbles.",
        icon_url=URL(
            "https://cdn.modrinth.com/data/aBVJ6Q36/e2bfd87a5e333a972c39d12a1c4e55add7616785.jpeg"
        ),
        curseforge_slug="hexal",
        modrinth_slug="hexal",
        modloaders=[Modloader.FORGE, Modloader.FABRIC, Modloader.QUILT],
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

DISABLED_PATTERNS: set[ResourceLocation] = {
    # commented out, but the regex doesn't account for that
    # https://github.com/vgskye/Hexal/blob/efe2b7df1e/Common/src/main/java/ram/talia/hexal/common/lib/hex/HexalActions.kt#L210
    ResourceLocation("hexal", "gate/mark/num/get"),
    ResourceLocation("hexal", "mote/count/get"),
    ResourceLocation("hexal", "mote/combine"),
}

SPECIAL_HANDLERS: dict[ResourceLocation, SpecialHandler[Any]] = {
    handler.id: handler
    for handler in [
        NumberSpecialHandler(
            id=ResourceLocation("hexcasting", "number"),
        ),
        MaskSpecialHandler(
            id=ResourceLocation("hexcasting", "mask"),
        ),
    ]
}
