from dataclasses import dataclass, field
from enum import Enum

from hex_renderer_py import Color

from .colors import colormap_to_colors, hex_to_color, hex_to_colors

# palette


@dataclass(frozen=True)
class _PaletteData:
    line_colors: list[Color]
    collision_color: Color
    per_world_color: Color = field(default_factory=lambda: hex_to_color("#a81ee3"))


class Palette(_PaletteData, Enum):
    Classic = (
        hex_to_colors("#ff6bff", "#a81ee3", "#6490ed", "#b189c7"),
        hex_to_color("#dd0000"),
    )
    Turbo = (
        colormap_to_colors("turbo", 0.06, 1, 8),
        hex_to_color("#d834eb"),
    )
    Dark2 = (
        colormap_to_colors("Dark2", 0, 1, 8),
        hex_to_color("#dd0000"),
    )
    Tab10 = (
        colormap_to_colors("tab10", 0, 1, 10),
        hex_to_color("#d834eb"),
    )

    @property
    def value(self):
        return self.name


# theme


@dataclass(frozen=True)
class _ThemeData:
    marker_color: Color


class Theme(_ThemeData, Enum):
    Light = Color(0, 0, 0, 255)
    Dark = Color(255, 255, 255, 255)

    @property
    def value(self):
        return self.name
