from __future__ import annotations

import asyncio
import math
import re
from dataclasses import InitVar, dataclass
from typing import Callable

import matplotlib.pyplot as plt
from aiohttp import ClientSession

from hex_interpreter.hex_draw import Palette, Theme, plot_intersect
from hexdecode.buildpatterns import build_registry
from hexdecode.hexast import Angle, Coord, Direction
from hexdecode.registry import SpecialHandlerPatternInfo


def get_offset_col(coord: Coord) -> int:
    return coord.q + coord.r // 2


@dataclass
class GridPattern:
    indent: int
    start_direction: Direction
    point_list: InitVar[list[Coord]]
    min_q_coord: Coord
    max_q: int
    min_r: int
    max_r: int

    @classmethod
    def from_pattern(cls, indent: int, direction: Direction, pattern: str) -> GridPattern:
        compass = direction
        cursor = compass.as_delta()

        points = [Coord.origin(), cursor]
        if cursor.q < 0:
            min_q_coord = cursor
        else:
            min_q_coord = Coord.origin()
        max_q = max(0, cursor.q)
        min_r, max_r = min(0, cursor.r), max(0, cursor.r)

        for c in pattern:
            compass = compass.rotated(Angle[c])
            cursor += compass
            points.append(cursor)

            if cursor.q < min_q_coord.q:
                min_q_coord = cursor
            max_q = max(max_q, cursor.q)
            min_r, max_r = min(min_r, cursor.r), max(max_r, cursor.r)

        return cls(indent, direction, points, min_q_coord, max_q, min_r, max_r)

    def __post_init__(self, point_list: list[Coord]):
        self.set_points(point_list)

    @property
    def points(self) -> list[Coord]:
        return self._points

    # not using a setter to make it clear that this is a somewhat expensive operation
    def set_points(self, new: list[Coord]):
        self._points = new
        self._point_set = set(new)

    @property
    def min_q(self) -> int:
        return self.min_q_coord.q

    @property
    def height(self) -> int:
        return self.max_r - self.min_r

    @property
    def width(self) -> int:
        return self.max_q - self.min_q

    @property
    def r_midpoint(self) -> int:
        return (self.max_r + self.min_r) // 2

    @property
    def start_angle(self) -> float:
        return self.start_direction.as_pyplot_angle()

    def shift(self, delta_q: int, delta_r: int) -> None:
        self.min_q_coord += Coord(delta_q, delta_r)
        self.max_q += delta_q
        self.min_r += delta_r
        self.max_r += delta_r
        self.set_points([p.shifted(Coord(delta_q, delta_r)) for p in self.points])

    def shift_q(self, delta_q: int) -> None:
        self.shift(delta_q, 0)

    def shift_r(self, delta_r: int) -> None:
        self.shift(0, delta_r)

    def get_max_possible_shift(self, other: GridPattern) -> int:
        """initial conditions: self.min_q > other.max_q, self.r_midpoint ~ other.r_midpoint"""
        delta_q = 0
        point_set = self._point_set

        while point_set.isdisjoint(other._point_set):
            delta_q -= 1
            point_set = {p.shifted(Coord(-1, 0)) for p in point_set}

        # if this assertion fails, they were intersecting at the start, which SHOULD never happen (I think)
        assert delta_q != 0
        return delta_q + 1

    def get_pixels(self) -> tuple[list[float], list[float]]:
        x_vals: list[float] = []
        y_vals: list[float] = []

        for point in self.points:
            (x, y) = point.pixel()
            x_vals.append(x)
            y_vals.append(y)

        return x_vals, y_vals


def none_minmax(fn: Callable[[int, int], int], a: int, b: int | None) -> int:
    return fn(a, b) if b is not None else a


# don't use this in production
async def _build_registry():
    async with ClientSession() as session:
        return await build_registry(session)


# also don't use this in production
registry = asyncio.run(_build_registry())

comment_re = re.compile(r"(/\*(?:.|\n)*?\*/|^#.*|//.*)")
patterns: list[GridPattern] = []
indent = 0

filename = "../../Scripts/Hex Casting/Uncapped Counter's Queue II.hexpattern"
with open(filename, "r") as f:
    text = (
        comment_re.sub("", f.read().strip())
        .replace("Consideration: ", "Consideration\n")
        .replace("{", "Introspection")
        .replace("}", "Retrospection")
    )
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        info = registry.from_display_name.get(line) or registry.from_name[line]
        assert not isinstance(info, SpecialHandlerPatternInfo)
        if info.name == "close_paren":
            indent -= 1
        patterns.append(GridPattern.from_pattern(indent, info.direction, info.pattern))
        if info.name == "open_paren":
            indent += 1


for i, pattern in enumerate(patterns):
    delta_r = -pattern.r_midpoint
    if i:
        other = patterns[i - 1]

        # can't combine these because get_max_possible_shift needs the first shift to set up initial conditions
        pattern.shift(other.max_q - pattern.min_q + 1, delta_r)
        pattern.shift_q(pattern.get_max_possible_shift(other))
    else:
        pattern.shift(0 - pattern.min_q, delta_r)


# max_dot_width = max(30, max(p.width for p in patterns))
max_dot_width = None
max_pattern_width = 10

delta_q = 0
delta_r = 0

current_height = 0
current_num_patterns = 0

min_x, max_x = math.inf, -math.inf
min_y, max_y = math.inf, -math.inf

for i, pattern in enumerate(patterns):
    if (
        max_dot_width is not None
        and pattern.max_q + delta_q + delta_r / 2 > max_dot_width
        or max_pattern_width is not None
        and current_num_patterns == max_pattern_width
    ):
        delta_r += current_height + 1
        delta_q = -pattern.min_q - delta_r / 2

        # line the left side up with the origin's column as best as possible
        # this is kind of awful but i really can't think of a better way to do it
        min_col_left, min_col_right = min(
            (
                get_offset_col(p + Coord(math.floor(delta_q - 1), delta_r)),
                get_offset_col(p + Coord(math.floor(delta_q + 1), delta_r)),
            )
            for p in pattern.points
        )
        if min_col_left == 0:
            delta_q -= 1
        elif min_col_right == 0:
            delta_q += 1

        current_height = 0
        current_num_patterns = 0

    current_height = max(pattern.height, current_height)
    current_num_patterns += 1
    pattern.shift(math.floor(delta_q), delta_r)

    # this is kinda gross. but idk if there's a better way
    x_vals, y_vals = pattern.get_pixels()
    min_x, max_x = min(min_x, *x_vals), max(max_x, *x_vals)
    min_y, max_y = min(min_y, *y_vals), max(max_y, *y_vals)


palette = Palette.Classic
theme = Theme.Light
line_scale = 8
arrow_scale = 2
fig_size = 8

width = max_x - min_x
height = max_y - min_y
max_width = max(width, height, 1.25)
scale = line_scale / math.log(max_width, 1.5) + 1.1

fig_width = width
fig_height = (fig_size * height) / width
if fig_height > fig_size:
    fig_width = (fig_size * width) / height
    fig_height = fig_size

fig = plt.figure(figsize=(fig_width, fig_height))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_aspect("equal")
ax.axis("off")

for pattern in patterns:
    plot_intersect(
        points=pattern.points,
        scale=scale,
        arrow_scale=arrow_scale,
        palette=palette,
        theme=theme,
        start_color_index=pattern.indent,
    )

x0, x1, y0, y1 = plt.axis()
plt.axis((x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1))

plt.show()
plt.close(fig)
