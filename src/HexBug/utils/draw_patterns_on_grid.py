from __future__ import annotations

import asyncio
import math
import re
from dataclasses import InitVar, dataclass
from typing import Callable

import matplotlib.pyplot as plt
from aiohttp import ClientSession

from ..hex_interpreter.hex_draw import Palette, Theme, plot_intersect
from ..hexdecode.buildpatterns import build_registry
from ..hexdecode.hex_math import Angle, Coord, Direction
from ..hexdecode.registry import SpecialHandlerPatternInfo
from .generate_image import get_scale, get_xy_bounds, prepare_fig, save_close_crop


def _get_offset_col(coord: Coord) -> int:
    return coord.q + coord.r // 2


@dataclass
class _GridPattern:
    start_direction: Direction
    point_list: InitVar[list[Coord]]
    min_q: int
    max_q: int
    min_r: int
    max_r: int

    @classmethod
    def from_pattern(cls, direction: Direction, pattern: str) -> _GridPattern:
        compass = direction
        cursor = compass.as_delta()

        points = [Coord.origin(), cursor]
        min_q, max_q = min(0, cursor.q), max(0, cursor.q)
        min_r, max_r = min(0, cursor.r), max(0, cursor.r)

        for c in pattern:
            compass = compass.rotated(Angle[c])
            cursor += compass
            points.append(cursor)

            min_q, max_q = min(min_q, cursor.q), max(max_q, cursor.q)
            min_r, max_r = min(min_r, cursor.r), max(max_r, cursor.r)

        return cls(direction, points, min_q, max_q, min_r, max_r)

    def __post_init__(self, point_list: list[Coord]):
        self.set_points(point_list)

    @property
    def points(self) -> list[Coord]:
        return self._points

    # not using a setter to make it clear that this is a somewhat expensive operation
    def set_points(self, new: list[Coord]):
        self._points = new
        self.point_set = set(new)

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
        self.min_q += delta_q
        self.max_q += delta_q
        self.min_r += delta_r
        self.max_r += delta_r
        self.set_points([p.shifted(Coord(delta_q, delta_r)) for p in self.points])

    def shift_q(self, delta_q: int) -> None:
        self.shift(delta_q, 0)

    def shift_r(self, delta_r: int) -> None:
        self.shift(0, delta_r)

    def get_max_possible_shift(self, existing_points: set[Coord]) -> int:
        """initial conditions: self.min_q > other.max_q, self.r_midpoint ~ other.r_midpoint"""
        delta_q = 0
        point_set = self.point_set

        while point_set.isdisjoint(existing_points):
            delta_q -= 1
            point_set = {p.shifted(Coord(-1, 0)) for p in point_set}

        # if this assertion fails, they were intersecting at the start, which SHOULD never happen (I think)
        assert delta_q != 0
        return delta_q + 1


def draw_patterns_on_grid(
    patterns: list[tuple[Direction, str]],
    max_dot_width: int | None,
    max_pattern_width: int | None,
    palette: Palette,
    theme: Theme,
    line_scale: float,
    arrow_scale: float,
):
    grid_patterns = [_GridPattern.from_pattern(d, p) for d, p in patterns]
    existing_points = set()

    for i, pattern in enumerate(grid_patterns):
        delta_r = -pattern.r_midpoint
        if i:
            other = grid_patterns[i - 1]

            # can't combine these because get_max_possible_shift needs the first shift to set up initial conditions
            pattern.shift(other.max_q - pattern.min_q + 1, delta_r)
            pattern.shift_q(pattern.get_max_possible_shift(existing_points))
        else:
            pattern.shift(0 - pattern.min_q, delta_r)
        existing_points.update(pattern.point_set)

    delta_q = 0
    delta_r = 0

    current_height = 0
    current_num_patterns = 0

    scales = []
    min_x, max_x = math.inf, -math.inf
    min_y, max_y = math.inf, -math.inf

    widest_dot_width = 0
    widest_num_patterns = 0

    for i, pattern in enumerate(grid_patterns):
        dot_width = pattern.max_q + delta_q + delta_r / 2
        widest_dot_width = max(widest_dot_width, dot_width)

        if (
            max_dot_width is not None
            and dot_width > max_dot_width
            or max_pattern_width is not None
            and current_num_patterns == max_pattern_width
        ):
            delta_r += current_height + 1
            delta_q = -pattern.min_q - delta_r / 2

            # line the left side up with the origin's column as best as possible
            # this is kind of awful but i really can't think of a better way to do it
            min_col_left, min_col_right = min(
                (
                    _get_offset_col(p + Coord(math.floor(delta_q - 1), delta_r)),
                    _get_offset_col(p + Coord(math.floor(delta_q + 1), delta_r)),
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
        widest_num_patterns = max(widest_num_patterns, current_num_patterns)
        pattern.shift(math.floor(delta_q), delta_r)

        # this is kinda gross. but idk if there's a better way
        (pattern_min_x, pattern_min_y), (pattern_max_x, pattern_max_y) = get_xy_bounds(pattern.points)

        scales.append(
            get_scale(
                width=pattern_max_x - pattern_min_x,
                height=pattern_max_y - pattern_min_y,
                line_scale=line_scale,
            )
        )

        min_x, max_x = min(min_x, pattern_min_x), max(max_x, pattern_max_x)
        min_y, max_y = min(min_y, pattern_min_y), max(max_y, pattern_max_y)

    scale = sum(scales) / len(scales)
    fig = prepare_fig(
        width=max_x - min_x,
        height=max_y - min_y,
        fig_size=max(4, 2 * widest_num_patterns),
    )

    for pattern in grid_patterns:
        plot_intersect(
            points=pattern.points,
            scale=scale,
            arrow_scale=arrow_scale,
            palette=palette,
            theme=theme,
        )

    return save_close_crop(fig)
