from collections import defaultdict
from enum import Enum, StrEnum
from itertools import pairwise

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colormaps  # type: ignore

from hexdecode.hex_math import Coord


class Theme(StrEnum):
    Light = "k"
    Dark = "w"


class Palette(Enum):
    Classic = (["#ff6bff", "#a81ee3", "#6490ed", "#b189c7"], "#dd0000")
    Turbo = ([colormaps["turbo"](x) for x in np.linspace(0.06, 1, 8)], "#d834eb")
    Dark2 = ([colormaps["Dark2"](x) for x in np.linspace(0, 1, 8)], "#dd0000")
    Tab10 = ([colormaps["tab10"](x) for x in np.linspace(0, 1, 10)], "#d834eb")

    @property
    def value(self) -> tuple[list[str], str]:
        """(colors, overlap_color)"""
        return super().value


def plot_monochrome(
    points: list[Coord],
    scale: float,
    monochrome_color: str,
    theme: Theme,
):
    point_style = theme.value + "o"

    for point, next_point in pairwise(points):
        x, y = point.pixel()
        next_x, next_y = next_point.pixel()

        plt.plot((x, next_x), (y, next_y), color=monochrome_color, lw=scale)
        plt.plot(x, y, point_style, ms=2 * scale)

    # last dot
    plt.plot(*points[-1].pixel(), point_style, ms=2 * scale)


def _plot_fancy_point(x: float, y: float, fmt: str, scale: float, color):
    plt.plot(x, y, fmt, ms=4 * scale)
    plt.plot(x, y, color=color, marker="o", ms=2.5 * scale)


def _plot_arrow(x: float, y: float, angle: float, scale: float, color):
    plt.plot(x, y, color=color, marker=(3, 0, angle), ms=scale)


def plot_intersect(
    points: list[Coord],
    scale: float,
    arrow_scale: float,
    palette: Palette,
    theme: Theme,
    start_color_index=0,
) -> None:
    colors, overlap_color = palette.value
    start_color_index %= len(colors)
    current_color_index = start_color_index
    current_color = colors[current_color_index]

    # we only add to colors_used after moving, so add the color at the first point
    colors_used_by_point: defaultdict[Coord, set[int]] = defaultdict(set)
    colors_used_by_point[points[0]].add(current_color_index)

    # set of frozenset(point, next_point) for overlap checking
    drawn_lines: set[frozenset[Coord]] = set()
    is_overlap = False

    point_fmt = theme.value + "o"
    arrow_scale *= scale

    for i, (point, next_point) in enumerate(pairwise(points)):
        x, y = point.pixel()
        next_x, next_y = next_point.pixel()
        arrow_x, arrow_y = (x + next_x) / 2, (y + next_y) / 2

        direction = point.immediate_delta(next_point)
        assert direction is not None
        arrow_angle = direction.as_pyplot_angle()

        current_color = colors[current_color_index]
        next_point_colors_used = colors_used_by_point[next_point]

        line_pair = frozenset((point, next_point))
        is_overlap = line_pair in drawn_lines
        drawn_lines.add(line_pair)

        if current_color_index in next_point_colors_used:
            # pick the next colour that hasn't been used yet
            # technically this does one extra check but python doesn't have do-while
            # only do this if there are colours left, otherwise it loops forever and kills the bot
            # that happened in production oops
            if len(next_point_colors_used) < len(colors):
                while current_color_index in next_point_colors_used:
                    current_color_index = (current_color_index + 1) % len(colors)

            next_color = colors[current_color_index]

            if not is_overlap:
                # first half, second half, and arrow
                plt.plot((x, arrow_x), (y, arrow_y), color=current_color, lw=scale)
                plt.plot((arrow_x, next_x), (arrow_y, next_y), color=next_color, lw=scale)
                _plot_arrow(arrow_x, arrow_y, arrow_angle, 2 * arrow_scale, next_color)

            current_color = next_color
        elif not is_overlap:
            plt.plot((x, next_x), (y, next_y), color=current_color, lw=scale)

        if is_overlap:
            plt.plot((x, next_x), (y, next_y), color=overlap_color, lw=scale)

        next_point_colors_used.add(current_color_index)

        if not i:
            # start arrow
            _plot_arrow(arrow_x, arrow_y, arrow_angle, 3.5 * arrow_scale, theme.value)
            _plot_arrow(arrow_x, arrow_y, arrow_angle, 2 * arrow_scale, current_color)
        else:
            # normal point
            plt.plot(x, y, point_fmt, ms=2 * scale)

    # end point
    _plot_fancy_point(*points[-1].pixel(), point_fmt, scale, overlap_color if is_overlap else current_color)

    # start point
    _plot_fancy_point(*points[0].pixel(), point_fmt, scale, colors[start_color_index])
