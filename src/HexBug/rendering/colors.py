import discord
import numpy as np
from hex_renderer_py import Color
from matplotlib import colormaps  # pyright: ignore[reportGeneralTypeIssues]


def hex_to_colors(*values: str) -> list[Color]:
    return [hex_to_color(v) for v in values]


def hex_to_color(value: str) -> Color:
    color = discord.Color.from_str(value)
    return Color(color.r, color.g, color.b, 255)


def colormap_to_colors(name: str, start: float, stop: float, num: int) -> list[Color]:
    return [
        Color(*(int(x * 255) for x in colormaps[name](i)))
        for i in np.linspace(start, stop, num)
    ]
