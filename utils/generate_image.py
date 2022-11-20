import math
from enum import Enum
from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colormaps  # type: ignore

from hex_interpreter.hex_draw import plot_intersect, plot_monochrome
from hexdecode.hexast import Angle, Coord, Direction


class Palette(Enum):
    Classic = ["#ff6bff", "#a81ee3", "#6490ed", "#b189c7"]
    Turbo = [colormaps["turbo"](x) for x in np.linspace(0.06, 1, 8)]
    Dark2 = [colormaps["Dark2"](x) for x in np.linspace(0, 1, 8)]
    Tab10 = [colormaps["tab10"](x) for x in np.linspace(0, 1, 10)]


def get_points(direction: Direction, pattern: str) -> list[Coord]:
    compass = direction
    cursor = compass.as_delta()

    points = [Coord.origin(), cursor]

    for c in pattern:
        compass = compass.rotated(Angle[c])
        cursor += compass
        points.append(cursor)

    return points


def generate_image(
    direction: Direction,
    pattern: str,
    is_great: bool,
    palette: Palette,
    line_scale: float,
    arrow_scale: float,
) -> BytesIO:
    points = get_points(direction, pattern)
    x_vals: list[float] = []
    y_vals: list[float] = []
    for point in points:
        (x, y) = point.pixel(1)
        x_vals.append(x)
        y_vals.append(-y)

    width = max(x_vals) - min(x_vals)
    height = max(y_vals) - min(y_vals)
    max_width = max(width, height, 1.25)
    scale = line_scale / math.log(max_width, 1.5) + 1.1

    fig = plt.figure(figsize=(4, 4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_aspect("equal")
    ax.axis("off")

    settings = {
        "intersect_colors": palette.value,
        "arrow_scale": arrow_scale,
    }
    start_angle = direction.angle_from(Direction.EAST).deg - 90
    pattern_info = (x_vals, y_vals, scale, start_angle)

    if is_great:
        plot_monochrome(pattern_info, "#a81ee3")
    else:
        plot_intersect(pattern_info, settings)

    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)
    return buf
