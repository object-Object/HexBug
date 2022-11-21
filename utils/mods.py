from dataclasses import dataclass
from typing import Literal

ModName = Literal["Hex Casting", "Hexal", "MoreIotas"]


@dataclass
class ModInfo:
    book_url: str
    mod_url: str | None
    source_url: str
    icon_url: str | None
    uses_talia_registry: bool


MOD_INFO: dict[ModName, ModInfo] = {
    "Hex Casting": ModInfo(
        book_url="https://gamma-delta.github.io/HexMod/",
        mod_url="https://www.curseforge.com/minecraft/mc-mods/hexcasting",
        source_url="https://github.com/gamma-delta/HexMod/",
        icon_url="https://media.forgecdn.net/avatars/thumbnails/535/944/64/64/637857298951404372.png",
        uses_talia_registry=False,
    ),
    "Hexal": ModInfo(
        book_url="https://talia-12.github.io/Hexal/",
        mod_url="https://modrinth.com/mod/hexal",
        source_url="https://github.com/Talia-12/Hexal/",
        icon_url="https://cdn.modrinth.com/data/aBVJ6Q36/e2bfd87a5e333a972c39d12a1c4e55add7616785.jpeg",
        uses_talia_registry=True,
    ),
    "MoreIotas": ModInfo(
        book_url="https://talia-12.github.io/MoreIotas/",
        mod_url="https://github.com/Talia-12/MoreIotas/",
        source_url="https://github.com/Talia-12/MoreIotas/",
        icon_url=None,
        uses_talia_registry=True,
    ),
}
