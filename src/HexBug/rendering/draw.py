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

DEFAULT_SCALE = 128.0
DEFAULT_LINE_WIDTH = 0.08
DEFAULT_MAX_OVERLAPS = 3


def draw_patterns(
    patterns: Pattern | Iterable[Pattern],
    options: GridOptions,
    *,
    scale: float | None = DEFAULT_SCALE,
    max_size: int | tuple[int, int] = 4096,
    max_dot_width: int = 50,
    trim_padding: bool = True,
) -> Image.Image:
    match patterns:
        case (Direction(), str()):
            patterns = [patterns]
        case _:
            pass

    grid = HexGrid(
        [PatternVariant(direction.name, sig) for direction, sig in patterns],
        max_dot_width,
    )

    if isinstance(max_size, int):
        max_size = (max_size, max_size)

    max_scale = grid.get_bound_scale(max_size, options)
    scale = max_scale if scale is None else min(max_scale, scale)

    data = grid.draw_png(scale, options)

    with BytesIO(bytes(data)) as buf:
        im = Image.open(buf, formats=["png"])
        im.load()
        if trim_padding:
            im = im.crop(im.getbbox())
        return im


def image_to_buffer(im: Image.Image):
    buf = BytesIO()
    im.save(buf, format="png")
    buf.seek(0)
    return buf


def get_grid_options(
    palette: Palette,
    theme: Theme,
    *,
    per_world: bool = False,
    line_width: float = DEFAULT_LINE_WIDTH,
    point_radius: float | None = None,
    arrow_radius: float | None = None,
    max_overlaps: int = DEFAULT_MAX_OVERLAPS,
) -> GridOptions:
    if point_radius is None:
        point_radius = line_width

    if arrow_radius is None:
        arrow_radius = line_width * 2

    point = Point.Single(
        marker=Marker(
            color=theme.marker_color,
            radius=point_radius,
        ),
    )

    if per_world:
        intersections = Intersections.UniformPoints(
            point=point,
        )

        lines = Lines.Monocolor(
            color=palette.per_world_color,
            bent=False,
        )

    else:
        start_point = EndPoint.BorderedMatch(
            match_radius=point_radius,
            border=Marker(
                color=theme.marker_color,
                radius=point_radius * 1.5,
            ),
        )

        intersections = Intersections.EndsAndMiddle(
            start=start_point,
            middle=point,
            end=start_point,
        )

        lines = Lines.SegmentColors(
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
        )

    return GridOptions(
        line_thickness=line_width,
        pattern_options=GridPatternOptions.Uniform(
            intersections=intersections,
            lines=lines,
        ),
        center_dot=Point.None_(),
    )
