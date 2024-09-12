import math
from textwrap import dedent
from typing import Any, Callable

import discord
from discord import app_commands
from discord.ext import commands
from hex_renderer_py import Color

from ..hexdecode.hex_math import Direction
from ..rendering import (
    DEFAULT_LINE_WIDTH,
    DEFAULT_MAX_OVERLAPS,
    DEFAULT_SCALE,
    Palette,
    Theme,
    draw_patterns,
    get_grid_options,
    image_to_buffer,
)
from ..rendering.colors import color_to_hex, color_to_int, color_to_rgb
from ..utils.buttons import build_show_or_delete_button
from ..utils.commands import HexBugBot
from .pattern import MAX_OVERLAPS_RANGE, SCALE_RANGE, WIDTH_RANGE


def _make_palette_showcase(num_colors: int) -> tuple[Direction, str]:
    """Returns a pattern which will contain at least the given amount of colours + 1."""
    # do at least 2 "hourglass" shapes so we can show the overlap colour without too much effort
    num_repeats = max(math.ceil(num_colors / 2), 2)
    return (
        Direction.NORTH_WEST,
        "da".join(["ddwaa"] * num_repeats) + "q" + "w" * (num_repeats - 2),
    )


def _format_colors(palette: Palette, transform: Callable[[Color], Any]) -> str:
    colors = "\n".join(f"`{transform(c)}`" for c in palette.line_colors)
    return dedent(
        f"""\
        Colors:
        {colors}

        Overlap:
        `{transform(palette.collision_color)}`"""
    )


class PaletteCog(commands.Cog):
    def __init__(self, bot: HexBugBot) -> None:
        self.bot = bot

    @app_commands.command()
    @app_commands.describe(
        palette="The color palette to show",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
        theme="Whether the pattern should be rendered for light or dark theme",
    )
    async def palette(
        self,
        interaction: discord.Interaction,
        palette: Palette,
        show_to_everyone: bool = False,
        theme: Theme = Theme.Dark,
        line_width: WIDTH_RANGE = DEFAULT_LINE_WIDTH,
        point_radius: WIDTH_RANGE | None = None,
        arrow_radius: WIDTH_RANGE | None = None,
        max_overlaps: MAX_OVERLAPS_RANGE = DEFAULT_MAX_OVERLAPS,
        scale: SCALE_RANGE = DEFAULT_SCALE,
    ):
        """Show one of the bot's color palettes."""

        embed = (
            discord.Embed(
                title=palette.name,
                color=discord.Colour(color_to_int(palette.line_colors[0])),
            )
            .add_field(
                name="RGB", value=_format_colors(palette, color_to_rgb), inline=True
            )
            .add_field(
                name="Hex", value=_format_colors(palette, color_to_hex), inline=True
            )
            .add_field(
                name="Decimal",
                value=_format_colors(palette, color_to_int),
                inline=True,
            )
            .set_image(url="attachment://pattern.png")
        )

        options = get_grid_options(
            palette,
            theme,
            line_width=line_width,
            point_radius=point_radius,
            arrow_radius=arrow_radius,
            max_overlaps=max_overlaps,
        )
        image = draw_patterns(
            _make_palette_showcase(len(palette.line_colors)),
            options,
            scale=scale,
        )
        file = discord.File(image_to_buffer(image), filename="pattern.png")

        await interaction.response.send_message(
            embed=embed,
            file=file,
            view=build_show_or_delete_button(
                show_to_everyone, interaction, embed=embed, file=file
            ),
            ephemeral=not show_to_everyone,
        )


async def setup(bot: HexBugBot) -> None:
    await bot.add_cog(PaletteCog(bot))
