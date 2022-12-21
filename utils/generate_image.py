import math
from io import BytesIO

import matplotlib.pyplot as plt
from PIL import Image

from hex_interpreter.hex_draw import Palette, Theme, plot_intersect, plot_monochrome
from hexdecode.hex_math import Angle, Coord, Direction


def get_points(direction: Direction, pattern: str) -> list[Coord]:
    compass = direction
    cursor = compass.as_delta()

    points = [Coord.origin(), cursor]

    for c in pattern:
        compass = compass.rotated(Angle[c])
        cursor += compass
        points.append(cursor)

    return points


def get_xy_bounds(points: list[Coord]) -> tuple[float, float, float, float]:
    """min_x, min_y, max_x, max_y"""
    x_vals: list[float] = []
    y_vals: list[float] = []
    for point in points:
        (x, y) = point.pixel()
        x_vals.append(x)
        y_vals.append(y)
    return min(x_vals), min(y_vals), max(x_vals), max(y_vals)


def save_close_crop(fig) -> tuple[BytesIO, tuple[int, int]]:
    """image, (width, height)"""

    x0, x1, y0, y1 = plt.axis()
    plt.axis((x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1))

    buf = BytesIO()
    fig.savefig(buf, format="png", transparent=True)
    plt.close(fig)

    buf.seek(0)
    im = Image.open(buf)
    im2 = im.crop(im.getbbox())
    size = im2.size

    buf.seek(0)
    buf.truncate()
    im2.save(buf, format="png")
    im2.close()

    buf.seek(0)
    return buf, size


def generate_image(
    direction: Direction,
    pattern: str,
    is_great: bool,
    palette: Palette,
    theme: Theme,
    line_scale: float,
    arrow_scale: float,
) -> tuple[BytesIO, tuple[int, int]]:
    points = get_points(direction, pattern)
    min_x, min_y, max_x, max_y = get_xy_bounds(points)

    width = max_x - min_x
    height = max_y - min_y
    max_width = max(width, height, 1.25)
    scale = line_scale / math.log(max_width, 1.5) + 1.1

    fig = plt.figure(figsize=(4, 4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_aspect("equal")
    ax.axis("off")

    if is_great:
        plot_monochrome(
            points=points,
            scale=scale,
            monochrome_color="#a81ee3",
            theme=theme,
        )
    else:
        plot_intersect(
            points=points,
            scale=scale,
            arrow_scale=arrow_scale,
            palette=palette,
            theme=theme,
        )

    return save_close_crop(fig)
