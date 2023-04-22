from fractions import Fraction
from io import BytesIO

import discord
from discord import app_commands
from discord.ext import commands

from cogs.pattern import DEFAULT_ARROW_SCALE, DEFAULT_LINE_SCALE, SCALE_RANGE
from hexdecode.hex_math import Direction
from hexdecode.hexast import generate_bookkeeper
from hexdecode.registry import RawPatternInfo, SpecialHandlerPatternInfo
from utils.buttons import build_show_or_delete_button
from utils.commands import HexBugBot
from utils.draw_patterns_on_grid import draw_patterns_on_grid
from utils.generate_decomposed_number import generate_decomposed_number
from utils.generate_image import Palette, Theme
from utils.parse_rational import parse_rational
from utils.patterns import parse_mask

WIDTH_RANGE = app_commands.Range[int, 1, 100]


def space_sep(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def stripped_eq(a: str, b: str) -> bool:
    return a.replace(",", "").replace(" ", "") == b.replace(",", "").replace(" ", "")


class PatternsCog(commands.GroupCog, name="patterns"):
    def __init__(self, bot: HexBugBot) -> None:
        self.bot = bot
        self.registry = bot.registry

        super().__init__()

    @app_commands.command()
    @app_commands.describe(
        number="The number to generate patterns for",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
        max_dot_width="Maximum allowed width (in dots) of each row before wrapping",
        max_pattern_width="Maximum allowed number of patterns in each row before wrapping",
        palette="The color palette to use for the lines (has no effect for great spells)",
        theme="Whether the pattern should be rendered for light or dark theme",
        line_scale="The scale of the lines and dots in the image",
        arrow_scale="The scale of the arrows in the image",
    )
    async def smart_number(
        self,
        interaction: discord.Interaction,
        number: str,
        show_to_everyone: bool = False,
        max_dot_width: WIDTH_RANGE = 16,
        max_pattern_width: WIDTH_RANGE = 100,
        palette: Palette = Palette.Classic,
        theme: Theme = Theme.Dark,
        line_scale: SCALE_RANGE = DEFAULT_LINE_SCALE,
        arrow_scale: SCALE_RANGE = DEFAULT_ARROW_SCALE,
    ) -> None:
        """Generate and display a pattern or list of patterns to put almost any number on the stack"""
        await interaction.response.defer(ephemeral=not show_to_everyone, thinking=True)

        if (target := parse_rational(number)) is None:
            return await interaction.followup.send(
                "❌ Invalid number.",
                ephemeral=True,
            )

        if not (result := generate_decomposed_number(self.registry, target)):
            return await interaction.followup.send(
                "❌ Failed to generate number.",
                ephemeral=True,
            )

        patterns, math_ops_str, _ = result

        image, _ = draw_patterns_on_grid(
            patterns=patterns,
            max_dot_width=max_dot_width,
            max_pattern_width=max_pattern_width,
            palette=palette,
            theme=theme,
            line_scale=line_scale,
            arrow_scale=arrow_scale,
        )

        title = (
            space_sep(target)
            if isinstance(target, int)
            else f"{space_sep(target.numerator)} / {space_sep(target.denominator)}"
        )
        if not stripped_eq(number, title):
            title = f"{number} ({title})"

        embed = (
            discord.Embed(
                title=title,
                description=f"```\n{math_ops_str}\n```",
            )
            .set_image(url="attachment://pattern.png")
            .set_footer(text=", ".join(f"{d.name} {p}" for d, p in patterns))
        )

        file = discord.File(image, filename="pattern.png")

        await interaction.followup.send(
            embed=embed,
            file=file,
            view=build_show_or_delete_button(show_to_everyone, interaction, embed=embed, file=file),
            ephemeral=not show_to_everyone,
        )

    @app_commands.command()
    @app_commands.describe(
        all_shorthand="The comma-separated list of patterns to display (shorthand is allowed)",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
        max_dot_width="Maximum allowed width (in dots) of each row before wrapping",
        max_pattern_width="Maximum allowed number of patterns in each row before wrapping",
        palette="The color palette to use for the lines (has no effect for great spells)",
        theme="Whether the pattern should be rendered for light or dark theme",
        line_scale="The scale of the lines and dots in the image",
        arrow_scale="The scale of the arrows in the image",
    )
    @app_commands.rename(all_shorthand="patterns")
    async def hex(
        self,
        interaction: discord.Interaction,
        all_shorthand: app_commands.Range[str, 1, 2000],
        show_to_everyone: bool = False,
        max_dot_width: WIDTH_RANGE = 16,
        max_pattern_width: WIDTH_RANGE = 100,
        palette: Palette = Palette.Classic,
        theme: Theme = Theme.Dark,
        line_scale: SCALE_RANGE = DEFAULT_LINE_SCALE,
        arrow_scale: SCALE_RANGE = DEFAULT_ARROW_SCALE,
    ) -> None:
        """Display a list of patterns on the staff grid"""
        await interaction.response.defer(ephemeral=not show_to_everyone, thinking=True)

        pattern_infos, unknown, pretty_shorthand = self.registry.from_shorthand_list(all_shorthand)

        patterns: list[tuple[Direction, str]] = []

        for info, arg in pattern_infos:
            match info:
                case RawPatternInfo():
                    patterns.append((info.direction, info.pattern))

                case SpecialHandlerPatternInfo():
                    match info.name:
                        case "mask":
                            if not isinstance(arg, str):
                                unknown.append(info.display_name)
                                continue

                            patterns.append(generate_bookkeeper(arg))

                        case "number":
                            if not isinstance(arg, (Fraction, int)):
                                unknown.append(info.display_name)
                                continue

                            if (result := generate_decomposed_number(self.registry, arg)) is None:
                                unknown.append(f"{info.display_name}: {arg}")
                                continue

                            new_patterns, _, _ = result
                            patterns.extend(new_patterns)

                        case name:
                            return await interaction.followup.send(
                                f"❌ Internal error: Unhandled pattern `{name}`.",
                                ephemeral=True,
                            )

                case _:
                    patterns.append((info.direction, info.pattern))

        if unknown:
            return await interaction.followup.send(
                "❌ Unknown patterns: ```\n" + "\n".join(unknown) + "\n```",
                ephemeral=True,
            )
        elif not patterns:
            return await interaction.followup.send(
                "❌ No patterns found.",
                ephemeral=True,
            )
        elif len(patterns) > 64:
            # this is why we can't have nice things
            return await interaction.followup.send(
                "❌ Too many patterns (max of 64).",
                ephemeral=True,
            )
        elif sum(len(pattern) for _, pattern in patterns) > 512:
            # fine i'm taking away your toys since you can't play nice
            return await interaction.followup.send(
                "❌ Too many angles (max of 512).",
                ephemeral=True,
            )

        image, _ = draw_patterns_on_grid(
            patterns=patterns,
            max_dot_width=max_dot_width,
            max_pattern_width=max_pattern_width,
            palette=palette,
            theme=theme,
            line_scale=line_scale,
            arrow_scale=arrow_scale,
        )

        embed = discord.Embed().set_image(url="attachment://patterns.png")
        files = [discord.File(image, filename="patterns.png")]

        description = f"```\n{pretty_shorthand}\n```"
        footer = ", ".join(f"{d.name} {p}" for d, p in patterns)

        if len(footer) > 2048 or len(description) + len(footer) > 6000:
            files.append(discord.File(BytesIO(footer.encode("utf-8")), filename="angles.txt"))
        else:
            embed.set_footer(text=footer)

        if len(description) > 4096 or len(description) + len(embed.footer.text or "") > 6000:
            files.append(discord.File(BytesIO(pretty_shorthand.encode("utf-8")), filename="names.txt"))
        else:
            embed.description = description

        # put names before angles if both are present
        if len(files) == 3:
            files.reverse()

        await interaction.followup.send(
            embed=embed,
            files=files,
            view=build_show_or_delete_button(show_to_everyone, interaction, embed=embed, files=files),
            ephemeral=not show_to_everyone,
        )


async def setup(bot: HexBugBot) -> None:
    await bot.add_cog(PatternsCog(bot))
