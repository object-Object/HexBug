import math
from textwrap import dedent
from typing import Any, Callable

import discord
import matplotlib.colors
from discord import app_commands
from discord.ext import commands

from ..hex_interpreter.hex_draw import Palette, PaletteColor, Theme
from ..hexdecode.hex_math import Direction
from ..utils.buttons import build_show_or_delete_button
from ..utils.commands import HexBugBot
from ..utils.generate_image import draw_single_pattern
from .pattern import DEFAULT_ARROW_SCALE, DEFAULT_LINE_SCALE, SCALE_RANGE


def _make_palette_showcase(num_colors: int) -> tuple[Direction, str]:
    """Returns a pattern which will contain at least the given amount of colours + 1."""
    # do at least 2 "hourglass" shapes so we can show the overlap colour without too much effort
    num_repeats = max(math.ceil(num_colors / 2), 2)
    return (
        Direction.NORTH_WEST,
        "da".join(["ddwaa"] * num_repeats) + "q" + "w" * (num_repeats - 2),
    )


# FIXME: type errors because of indeterminate tuple length
def _color_to_rgb(color: PaletteColor) -> tuple[int, int, int]:
    if isinstance(color, str):
        color = matplotlib.colors.to_rgb(color)  # type: ignore

    return tuple(math.floor(v * 255) for v in color)  # type: ignore


def _color_to_int(color: PaletteColor) -> int:
    r, g, b = _color_to_rgb(color)
    return (r << 16) + (g << 8) + b


def _color_to_hex(color: PaletteColor) -> str:
    return matplotlib.colors.to_hex(color)


def _format_colors(palette: Palette, transform: Callable[[PaletteColor], Any]) -> str:
    colors = "\n".join(f"`{transform(c)}`" for c in palette.colors)
    return dedent(
        f"""\
        Colors:
        {colors}

        Overlap:
        `{transform(palette.overlap_color)}`"""
    )


class PaletteCog(commands.Cog):
    def __init__(self, bot: HexBugBot) -> None:
        self.bot = bot

    @app_commands.command()
    @app_commands.describe(
        palette="The color palette to show",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
        theme="Whether the pattern should be rendered for light or dark theme",
        line_scale="The scale of the lines and dots in the image",
        arrow_scale="The scale of the arrows in the image",
    )
    async def palette(
        self,
        interaction: discord.Interaction,
        palette: Palette,
        show_to_everyone: bool = False,
        theme: Theme = Theme.Dark,
        line_scale: SCALE_RANGE = DEFAULT_LINE_SCALE,
        arrow_scale: SCALE_RANGE = DEFAULT_ARROW_SCALE,
    ):
        """Show one of the bot's color palettes."""

        embed = (
            discord.Embed(
                title=palette.name,
                color=discord.Colour(_color_to_int(palette.colors[0])),
            )
            .add_field(name="RGB", value=_format_colors(palette, _color_to_rgb), inline=True)
            .add_field(name="Hex", value=_format_colors(palette, _color_to_hex), inline=True)
            .add_field(name="Decimal", value=_format_colors(palette, _color_to_int), inline=True)
            .set_image(url="attachment://pattern.png")
        )

        image, _ = draw_single_pattern(
            *_make_palette_showcase(len(palette.colors)),
            is_great=False,
            palette=palette,
            theme=theme,
            line_scale=line_scale,
            arrow_scale=arrow_scale,
        )
        file = discord.File(image, filename="pattern.png")

        await interaction.response.send_message(
            embed=embed,
            file=file,
            view=build_show_or_delete_button(show_to_everyone, interaction, embed=embed, file=file),
            ephemeral=not show_to_everyone,
        )


async def setup(bot: HexBugBot) -> None:
    await bot.add_cog(PaletteCog(bot))
