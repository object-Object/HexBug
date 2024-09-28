import discord
import matplotlib.colors
import numpy as np
from hex_renderer_py import Color
from matplotlib import colormaps


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


def color_to_rgb(color: Color) -> tuple[int, int, int]:
    return color.r, color.g, color.b


def color_to_int(color: Color) -> int:
    return (color.r << 16) + (color.g << 8) + color.b


def color_to_hex(color: Color) -> str:
    return matplotlib.colors.to_hex((color.r / 255, color.g / 255, color.b / 255))
