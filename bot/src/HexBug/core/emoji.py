from enum import Enum

from typing_extensions import deprecated

from HexBug.resources import get_resource


class CustomEmoji(Enum):
    apps_icon = "apps_icon.png"
    fabric = "fabric.png"
    forge = "forge.png"
    neoforge = "neoforge.png"
    quilt = "quilt.png"

    def __init__(self, filename: str):
        self.filename = filename

    @property
    @deprecated("Use name or filename instead", category=None)
    def value(self):
        return super().value

    def load_image(self) -> bytes:
        return get_resource(f"emoji/{self.filename}").read_bytes()
