from io import BytesIO
from typing import Iterable

from discord import File
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
from pydantic import BaseModel

from HexBug.data.hex_math import HexPattern

from .types import Palette, Theme

DEFAULT_SCALE = 128.0
DEFAULT_LINE_WIDTH = 0.08
DEFAULT_MAX_OVERLAPS = 3
DEFAULT_MAX_GRID_WIDTH = 50


class PatternRenderingOptions(BaseModel):
    model_config = {
        "validate_assignment": True,
    }

    palette: Palette = Palette.Classic
    theme: Theme = Theme.Dark
    line_width: float = DEFAULT_LINE_WIDTH
    point_radius: float | None = None
    arrow_radius: float | None = None
    max_overlaps: int = DEFAULT_MAX_OVERLAPS
    scale: float = DEFAULT_SCALE
    max_grid_width: int = DEFAULT_MAX_GRID_WIDTH

    def render_discord_file(
        self,
        patterns: HexPattern | Iterable[HexPattern],
        hide_stroke_order: bool,
        filename: str,
    ):
        image = self.render_image(patterns, hide_stroke_order)
        return File(image_to_buffer(image), filename)

    def render_image(
        self,
        patterns: HexPattern | Iterable[HexPattern],
        hide_stroke_order: bool,
    ):
        return draw_patterns(
            patterns,
            self.get_grid_options(hide_stroke_order),
            scale=self.scale,
            max_grid_width=self.max_grid_width,
        )

    def get_grid_options(self, hide_stroke_order: bool):
        if (point_radius := self.point_radius) is None:
            point_radius = self.line_width

        if (arrow_radius := self.arrow_radius) is None:
            arrow_radius = self.line_width * 2

        point = Point.Single(
            marker=Marker(
                color=self.theme.marker_color,
                radius=point_radius,
            ),
        )

        if hide_stroke_order:
            intersections = Intersections.UniformPoints(
                point=point,
            )

            lines = Lines.Monocolor(
                color=self.palette.per_world_color,
                bent=False,
            )

        else:
            start_point = EndPoint.BorderedMatch(
                match_radius=point_radius,
                border=Marker(
                    color=self.theme.marker_color,
                    radius=point_radius * 1.5,
                ),
            )

            intersections = Intersections.EndsAndMiddle(
                start=start_point,
                middle=point,
                end=start_point,
            )

            lines = Lines.SegmentColors(
                colors=self.palette.line_colors,
                triangles=Triangle.BorderStartMatch(
                    match_radius=arrow_radius,
                    border=Marker(
                        color=self.theme.marker_color,
                        radius=arrow_radius * 1.5,
                    ),
                ),
                # TODO: it draws dashes when there are 3 overlaps???
                collisions=CollisionOption.OverloadedParallel(
                    max_line=self.max_overlaps,
                    overload=OverloadOptions.Dashes(
                        color=self.palette.collision_color,
                    ),
                ),
            )

        return GridOptions(
            line_thickness=self.line_width,
            pattern_options=GridPatternOptions.Uniform(
                intersections=intersections,
                lines=lines,
            ),
            center_dot=Point.None_(),
        )


def draw_patterns(
    patterns: HexPattern | Iterable[HexPattern],
    options: GridOptions,
    *,
    scale: float | None = DEFAULT_SCALE,
    max_size: int | tuple[int, int] = 4096,
    max_grid_width: int = DEFAULT_MAX_GRID_WIDTH,
    trim_padding: bool = True,
) -> Image.Image:
    if isinstance(patterns, HexPattern):
        patterns = [patterns]

    grid = HexGrid(
        [PatternVariant(p.direction.name, p.signature) for p in patterns],
        max_grid_width,
    )

    if isinstance(max_size, int):
        max_size = (max_size, max_size)

    max_scale = grid.get_bound_scale(max_size, options)
    scale = max_scale if scale is None else min(max_scale, scale)

    data = grid.draw_png(scale, options)

    with BytesIO(bytes(data)) as buf:
        im = Image.open(buf, formats=["png"])
        im.load()  # pyright: ignore[reportUnknownMemberType]
        if trim_padding:
            im = im.crop(im.getbbox())
        return im


def image_to_buffer(im: Image.Image):
    buf = BytesIO()
    im.save(buf, format="png")
    buf.seek(0)
    return buf
