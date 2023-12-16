import math
from io import BytesIO

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from PIL import Image

from ..hex_interpreter.hex_draw import Palette, Theme, plot_intersect, plot_monochrome
from ..hexdecode.hex_math import Coord, Direction, get_pattern_points


def get_xy_bounds(
    points: list[Coord],
) -> tuple[tuple[float, float], tuple[float, float]]:
    """(min_x, min_y), (max_x, max_y)"""
    x_vals: list[float] = []
    y_vals: list[float] = []
    for point in points:
        (x, y) = point.pixel()
        x_vals.append(x)
        y_vals.append(y)
    return (min(x_vals), min(y_vals)), (max(x_vals), max(y_vals))


def get_width_and_height(points: list[Coord]) -> tuple[float, float]:
    (min_x, min_y), (max_x, max_y) = get_xy_bounds(points)
    return max_x - min_x, max_y - min_y


def save_close_crop(fig) -> tuple[BytesIO, tuple[int, int]]:
    """image, (width, height)"""

    x0, x1, y0, y1 = plt.axis()
    plt.axis((x0 - 0.4, x1 + 0.4, y0 - 0.4, y1 + 0.4))

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


def get_scale(width: float, height: float, line_scale: float) -> float:
    max_width = max(width, height, 1.25)
    return line_scale / math.log(max_width, 1.5) + 1.1


def prepare_fig(
    width: float,
    height: float,
    fig_size: float,
) -> Figure:
    if width and height:
        fig_width = width
        fig_height = (fig_size * height) / width
        if fig_height > fig_size:
            fig_width = (fig_size * width) / height
            fig_height = fig_size
    else:
        fig_width, fig_height = fig_size, fig_size

    fig = plt.figure(figsize=(fig_width, fig_height))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_aspect("equal")
    ax.axis("off")

    return fig


def draw_single_pattern(
    direction: Direction,
    pattern: str,
    is_great: bool,
    palette: Palette,
    theme: Theme,
    line_scale: float,
    arrow_scale: float,
) -> tuple[BytesIO, tuple[int, int]]:
    points = list(get_pattern_points(direction, pattern))
    width, height = get_width_and_height(points)

    scale = get_scale(width, height, line_scale)
    fig = prepare_fig(width, height, fig_size=4)

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
