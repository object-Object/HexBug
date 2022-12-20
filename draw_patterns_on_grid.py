from __future__ import annotations

import math
from dataclasses import dataclass, InitVar
from typing import Callable

import matplotlib.pyplot as plt

from hex_interpreter.hex_draw import plot_intersect, Palette, Theme
from hexdecode.hexast import Angle, Coord, Direction


@dataclass
class GridPattern:
    start_direction: Direction
    point_list: InitVar[list[Coord]]
    min_q: int
    max_q: int
    min_r: int
    max_r: int
    min_s: int
    max_s: int

    @classmethod
    def from_pattern(cls, direction: Direction, pattern: str) -> GridPattern:
        compass = direction
        cursor = compass.as_delta()

        points = [Coord.origin(), cursor]
        min_q, max_q = min(0, cursor.q), max(0, cursor.q)
        min_r, max_r = min(0, cursor.r), max(0, cursor.r)
        min_s, max_s = min(0, cursor.s), max(0, cursor.s)

        for c in pattern:
            compass = compass.rotated(Angle[c])
            cursor += compass
            points.append(cursor)
            min_q, max_q = min(min_q, cursor.q), max(max_q, cursor.q)
            min_r, max_r = min(min_r, cursor.r), max(max_r, cursor.r)
            min_s, max_s = min(min_s, cursor.s), max(max_s, cursor.s)

        return cls(direction, points, min_q, max_q, min_r, max_r, min_s, max_s)

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
        return self.start_direction.angle_from(Direction.EAST).deg - 90

    def shift(self, delta_q: int, delta_r: int) -> None:
        delta_s = -delta_q - delta_r
        self.min_q += delta_q
        self.max_q += delta_q
        self.min_r += delta_r
        self.max_r += delta_r
        self.min_s += delta_s
        self.max_s += delta_s
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

    def get_pixels(self) -> tuple[list[float], list[float], float]:
        x_vals: list[float] = []
        y_vals: list[float] = []

        for point in self.points:
            (x, y) = point.pixel(1)
            x_vals.append(x)
            y_vals.append(-y)

        return x_vals, y_vals, self.start_angle


def none_minmax(fn: Callable[[int, int], int], a: int, b: int | None) -> int:
    return fn(a, b) if b is not None else a


pattern_input: list[tuple[Direction, str]] = [
    (Direction.NORTH_EAST, "qaq"),
    (Direction.EAST, "aa"),
    (Direction.NORTH_EAST, "qaq"),
    (Direction.NORTH_EAST, "wa"),
    (Direction.EAST, "weaqa"),
]

patterns: list[GridPattern] = [GridPattern.from_pattern(*p) for p in pattern_input]

for i, pattern in enumerate(patterns):
    delta_r = -pattern.r_midpoint
    if i:
        other = patterns[i - 1]

        # can't combine these because get_max_possible_shift needs the first shift to set up initial conditions
        pattern.shift(other.max_q - pattern.min_q + 1, delta_r)
        pattern.shift_q(pattern.get_max_possible_shift(other))
    else:
        pattern.shift_r(delta_r)

pattern_pixels: list[tuple[list[float], list[float], float]] = []
max_width = max(20, max(p.width for p in patterns))

delta_q = 0
delta_r = 0
current_width = 0
current_height = 0

min_q, max_q = None, None
min_r, max_r = None, None
min_s, max_s = None, None
min_x, max_x = math.inf, -math.inf
min_y, max_y = math.inf, -math.inf

for pattern in patterns:
    if current_width + pattern.width > max_width:
        delta_q -= current_width
        delta_r += current_height + 1
        current_width = 0
        current_height = 0

    current_width += pattern.width
    current_height = max(pattern.height, current_height)
    pattern.shift(delta_q, delta_r)

    min_q, max_q = none_minmax(min, pattern.min_q, min_q), none_minmax(max, pattern.max_q, max_q)
    min_r, max_r = none_minmax(min, pattern.min_r, min_r), none_minmax(max, pattern.max_r, max_r)
    min_s, max_s = none_minmax(min, pattern.min_s, min_s), none_minmax(max, pattern.max_s, max_s)

    data = pattern.get_pixels()

    x_vals, y_vals, _ = data
    min_x, max_x = min(min_x, *x_vals), max(max_x, *x_vals)
    min_y, max_y = min(min_y, *y_vals), max(max_y, *y_vals)

    pattern_pixels.append(data)

assert min_q is not None and max_q is not None
assert min_r is not None and max_r is not None
assert min_s is not None and max_s is not None

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

background_point_styles = {"color": theme.value, "marker": "o", "ms": scale / 1.5}
for r in range(min_r, max_r + 1):
    for q in range(min_q, max_q + 1):
        x, y = Coord(q, r).pixel(1)
        plt.plot(x, -y, **background_point_styles)
    for s in range(min_s, max_s + 1):
        q = -s - r
        x, y = Coord(q, r).pixel(1)
        plt.plot(x, -y, **background_point_styles)

for x_vals, y_vals, start_angle in pattern_pixels:
    plot_intersect(
        x_vals=x_vals,
        y_vals=y_vals,
        scale=scale,
        arrow_scale=arrow_scale,
        start_angle=start_angle,
        palette=palette,
        theme=theme,
    )

x0, x1, y0, y1 = plt.axis()
plt.axis((x0 - 0.1, x1 + 0.1, y0 - 0.1, y1 + 0.1))

plt.show()
plt.close(fig)
