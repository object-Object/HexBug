from __future__ import annotations

import math
from typing import Callable

import hex_renderer_py
from discord import Color, Embed, Interaction, app_commands
from discord.app_commands.transformers import EnumNameTransformer, Transform

from HexBug.core.cog import HexBugCog
from HexBug.data.hex_math import HexDir, HexPattern
from HexBug.rendering.colors import color_to_hex, color_to_int, color_to_rgb
from HexBug.rendering.draw import PatternRenderingOptions
from HexBug.rendering.types import Palette
from HexBug.ui.views.patterns import EmbedPatternView
from HexBug.utils.discord.translation import translate_command_text
from HexBug.utils.discord.visibility import Visibility, VisibilityOption


class PaletteCog(HexBugCog):
    @app_commands.command()
    async def palette(
        self,
        interaction: Interaction,
        palette: Transform[Palette, EnumNameTransformer(Palette)],
        hide_stroke_order: bool = False,
        visibility: VisibilityOption = Visibility.PRIVATE,
    ):
        embed = (
            Embed(
                title=palette.name,
                color=Color(color_to_int(palette.line_colors[0])),
            )
            .add_field(
                name=await translate_command_text(interaction, "rgb"),
                value=await _format_colors(interaction, palette, color_to_rgb),
                inline=True,
            )
            .add_field(
                name=await translate_command_text(interaction, "hex"),
                value=await _format_colors(interaction, palette, color_to_hex),
                inline=True,
            )
            .add_field(
                name=await translate_command_text(interaction, "int"),
                value=await _format_colors(interaction, palette, color_to_int),
                inline=True,
            )
        )

        await EmbedPatternView(
            interaction=interaction,
            pattern=_make_palette_showcase(len(palette.line_colors)),
            options=PatternRenderingOptions(
                palette=palette,
                freeze_palette=True,
                max_overlaps=0,
            ),
            hide_stroke_order=hide_stroke_order,
            embed=embed,
        ).send(interaction, visibility)


def _make_palette_showcase(num_colors: int) -> HexPattern:
    """Returns a pattern which will contain at least the given amount of colors + 1."""

    # do at least 2 "hourglass" shapes so we can show the overlap color without too much effort
    num_repeats = max(math.ceil(num_colors / 2), 2)
    return HexPattern(
        HexDir.NORTH_WEST,
        "da".join(["ddwaa"] * num_repeats) + "q" + "w" * (num_repeats - 2),
    )


async def _format_colors(
    interaction: Interaction,
    palette: Palette,
    transform: Callable[[hex_renderer_py.Color], str | int | tuple[int, int, int]],
) -> str:
    return await translate_command_text(
        interaction,
        "colors",
        colors="\n".join(f"`{transform(c)}`" for c in palette.line_colors),
        overlap=f"`{transform(palette.collision_color)}`",
        per_world=f"`{transform(palette.per_world_color)}`",
    )
