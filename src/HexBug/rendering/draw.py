from io import BytesIO
from typing import Iterable

from hex_renderer_py import (
    CollisionOption,
    EndPoint,
    GridOptions,
    GridPatternOptions,
    HexGrid,
    Intersections,
    Lines,
    Marker,
    OverloadOptions,
    PatternVariant,
    Point,
    Triangle,
)
from PIL import Image

from HexBug.hexdecode.hex_math import Direction, Pattern

from .types import Palette, Theme


def draw_patterns(
    patterns: Pattern | Iterable[Pattern],
    options: GridOptions,
    *,
    max_size: int | tuple[int, int] = 256,
    max_dot_width: int = 50,
    trim_padding: bool = True,
) -> Image.Image:
    match patterns:
        case (Direction(), str()):
            patterns = [patterns]
        case _:
            pass

    if isinstance(max_size, int):
        max_size = (max_size, max_size)

    grid = HexGrid(
        [PatternVariant(direction.name, sig) for direction, sig in patterns],
        max_dot_width,
    )
    scale = grid.get_bound_scale(max_size, options)
    data = grid.draw_png(scale, options)

    im = Image.open(BytesIO(bytes(data)))
    if trim_padding:
        im = im.crop(im.getbbox())
    return im


def get_grid_options(
    palette: Palette,
    theme: Theme,
    *,
    line_width: float = 0.08,
    point_radius: float | None = None,
    arrow_radius: float | None = None,
    max_overlaps: int = 3,
) -> GridOptions:
    if point_radius is None:
        point_radius = line_width

    if arrow_radius is None:
        arrow_radius = line_width * 2

    start_point = EndPoint.BorderedMatch(
        match_radius=point_radius,
        border=Marker(
            color=theme.marker_color,
            radius=point_radius * 1.5,
        ),
    )

    return GridOptions(
        line_thickness=line_width,
        pattern_options=GridPatternOptions.Uniform(
            intersections=Intersections.EndsAndMiddle(
                start=start_point,
                middle=Point.Single(
                    marker=Marker(
                        color=theme.marker_color,
                        radius=point_radius,
                    ),
                ),
                end=start_point,
            ),
            lines=Lines.SegmentColors(
                colors=palette.line_colors,
                triangles=Triangle.BorderStartMatch(
                    match_radius=arrow_radius,
                    border=Marker(
                        color=theme.marker_color,
                        radius=arrow_radius * 1.5,
                    ),
                ),
                # TODO: it draws dashes when there are 3 overlaps???
                collisions=CollisionOption.OverloadedParallel(
                    max_line=max_overlaps,
                    overload=OverloadOptions.Dashes(
                        color=palette.collision_color,
                    ),
                ),
            ),
        ),
        center_dot=Point.None_(),
    )
