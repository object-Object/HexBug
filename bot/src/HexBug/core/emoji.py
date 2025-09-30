from __future__ import annotations

from enum import Enum

from typing_extensions import deprecated

from HexBug.data.mods import Modloader
from HexBug.resources import get_resource


class CustomEmoji(Enum):
    apps_icon = "apps_icon.png"
    fabric = "fabric.png"
    forge = "forge.png"
    neoforge = "neoforge.png"
    quilt = "quilt.png"

    def __init__(self, filename: str):
        self.filename = filename

    @classmethod
    def from_modloader(cls, modloader: Modloader) -> CustomEmoji:
        match modloader:
            case Modloader.FABRIC:
                return cls.fabric
            case Modloader.FORGE:
                return cls.forge
            case Modloader.NEOFORGE:
                return cls.neoforge
            case Modloader.QUILT:
                return cls.quilt

    @property
    @deprecated("Use name or filename instead", category=None)
    def value(self):
        return super().value

    def load_image(self) -> bytes:
        return get_resource(f"emoji/{self.filename}").read_bytes()
