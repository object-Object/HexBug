from enum import Enum, StrEnum

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colormaps  # type: ignore


class Theme(StrEnum):
    Light = "k"
    Dark = "w"


class Palette(Enum):
    Classic = ["#ff6bff", "#a81ee3", "#6490ed", "#b189c7"]
    Turbo = [colormaps["turbo"](x) for x in np.linspace(0.06, 1, 8)]
    Dark2 = [colormaps["Dark2"](x) for x in np.linspace(0, 1, 8)]
    Tab10 = [colormaps["tab10"](x) for x in np.linspace(0, 1, 10)]


def plot_monochrome(
    x_vals: list[float],
    y_vals: list[float],
    scale: float,
    monochrome_color: str,
    theme: Theme,
):
    point_style = theme.value + "o"
    for i in range(len(x_vals) - 1):
        plt.plot(x_vals[i : i + 2], y_vals[i : i + 2], color=monochrome_color, lw=scale)
        plt.plot(x_vals[i], y_vals[i], point_style, ms=2 * scale)
    plt.plot(x_vals[-1], y_vals[-1], point_style, ms=2 * scale)


def plot_intersect(
    x_vals: list[float],
    y_vals: list[float],
    scale: float,
    arrow_scale: float,
    start_angle: float,
    palette: Palette,
    theme: Theme,
):
    line_count = len(x_vals) - 1
    used_points = []
    colors = palette.value
    color_index = 0
    point_style = theme.value + "o"

    # plot start-direction triangle
    plt.plot(
        x_vals[1] / 2.15,
        y_vals[1] / 2.15,
        color=colors[0],
        marker=(3, 0, start_angle),
        ms=2.9 * arrow_scale * scale,
    )

    for i in range(line_count + 1):
        point = [x_vals[i], y_vals[i], color_index]
        repeats = False

        # check if we've already been to this point, with this line color
        # doing this with if(j==point) doesn't work because of floating-point jank
        for j in used_points:
            same_color = color_index == j[2] or (3 - color_index % 3 == j[2] and color_index > 3)
            if abs(point[0] - j[0]) < 0.1 and abs(point[1] - j[1]) < 0.1 and same_color:
                repeats = True
                used_points[used_points.index(j)][2] += 1

        # if the condition is true, cycle the line color to the next option
        # then draw a half-line backwards to mark the beginning of the new segment
        if repeats:
            color_index += 1
            color_index %= len(colors)
            back_half = ((x_vals[i - 1] + point[0]) / 2, (y_vals[i - 1] + point[1]) / 2)
            plt.plot((point[0], back_half[0]), (point[1], back_half[1]), color=colors[color_index], lw=scale)

            # draw a triangle to mark the direction of the new color
            if abs(y_vals[i] - y_vals[i - 1]) < 0.1:
                if x_vals[i] > x_vals[i - 1]:
                    angle = 270
                else:
                    angle = 90
            elif y_vals[i] > y_vals[i - 1]:
                if x_vals[i] > x_vals[i - 1]:
                    angle = 330
                else:
                    angle = 30
            else:
                if x_vals[i] > x_vals[i - 1]:
                    angle = 210
                else:
                    angle = 150
            plt.plot(
                back_half[0],
                back_half[1],
                marker=(3, 0, angle),
                color=colors[color_index],
                ms=2 * arrow_scale * scale,
            )
        else:
            used_points.append(point)

        # only draw point+line if we're not at the end
        if i != line_count:
            plt.plot(x_vals[i : i + 2], y_vals[i : i + 2], color=colors[color_index], lw=scale)
            plt.plot(point[0], point[1], point_style, ms=2 * scale)

    # mark the last point
    plt.plot(x_vals[-1], y_vals[-1], point_style, ms=3.5 * scale)
    plt.plot(x_vals[-1], y_vals[-1], color=colors[color_index], marker="o", ms=2 * scale)

    # mark the first point
    plt.plot(x_vals[0], y_vals[0], point_style, ms=3.5 * scale)
    plt.plot(x_vals[0], y_vals[0], color=colors[0], marker="o", ms=2 * scale)
