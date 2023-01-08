from io import BytesIO

import discord
from discord import app_commands
from discord.ext import commands

from hexdecode.buildpatterns import MAX_PREGEN_NUMBER
from hexdecode.hex_math import Angle, Direction
from hexdecode.hexast import Registry, UnknownPattern, _parse_unknown_pattern, generate_bookkeeper
from hexdecode.registry import SpecialHandlerPatternInfo
from utils.align_horizontal import align_horizontal
from utils.buttons import buildShowOrDeleteButton
from utils.commands import HexBugBot, build_autocomplete
from utils.generate_image import Palette, Theme, generate_image
from utils.mods import APIWithoutBookModInfo

DEFAULT_LINE_SCALE = 6
DEFAULT_ARROW_SCALE = 2
SCALE_RANGE = app_commands.Range[float, 0.1, 1000.0]


def parse_mask(translation: str) -> str | None:
    mask = translation.removeprefix("Bookkeeper's Gambit:").lstrip().lower()
    if not all(c in "v-" for c in mask):
        return None
    return mask


async def send_pattern(
    registry: Registry,
    interaction: discord.Interaction,
    name: str,
    translation: str,
    direction: Direction | None,
    pattern: str | None,
    image: BytesIO,
    show_to_everyone: bool,
):
    info = registry.from_name.get(name)
    mod_info = info and info.mod.value

    book_url = None
    if info and mod_info and not isinstance(mod_info, APIWithoutBookModInfo) and info.book_url is not None:
        book_url = mod_info.build_book_url(info.book_url, False, False)

    embed = discord.Embed(
        title=translation,
        url=book_url,
        description=info and info.args,
    ).set_image(url="attachment://pattern.png")
    if mod_info:
        embed.set_author(name=mod_info.name, icon_url=mod_info.icon_url, url=mod_info.mod_url)
    if direction is not None and pattern is not None:
        embed.set_footer(text=f"{direction.name} {pattern}")

    file = discord.File(image, filename="pattern.png")

    await interaction.response.send_message(
        embed=embed,
        file=file,
        view=buildShowOrDeleteButton(show_to_everyone, interaction, embed=embed, file=file),
        ephemeral=not show_to_everyone,
    )


class PatternCog(commands.GroupCog, name="pattern"):
    def __init__(self, bot: HexBugBot) -> None:
        self.bot = bot
        self.registry = bot.registry

        initial_choices: list[tuple[app_commands.Choice[str], list[str]]] = []
        for info in self.registry.patterns:
            if isinstance(info, SpecialHandlerPatternInfo):
                continue
            initial_choices.append((app_commands.Choice(name=info.display_name, value=info.display_name), [info.name]))

        self.autocomplete = build_autocomplete(initial_choices)

        super().__init__()

    @app_commands.command()
    @app_commands.describe(
        direction="The starting direction of the pattern",
        pattern='The angle signature of the pattern (eg. aqaawde) — type "-" to leave blank',
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
        hide_stroke_order="Whether or not to hide the stroke order (like with great spells)",
        palette="The color palette to use for the lines (has no effect if hide_stroke_order is True)",
        theme="Whether the pattern should be rendered for light or dark theme",
        line_scale="The scale of the lines and dots in the image",
        arrow_scale="The scale of the arrows in the image",
    )
    async def raw(
        self,
        interaction: discord.Interaction,
        direction: Direction,
        pattern: app_commands.Range[str, 1, 256],
        show_to_everyone: bool = False,
        hide_stroke_order: bool = False,
        palette: Palette = Palette.Classic,
        theme: Theme = Theme.Dark,
        line_scale: SCALE_RANGE = DEFAULT_LINE_SCALE,
        arrow_scale: SCALE_RANGE = DEFAULT_ARROW_SCALE,
    ) -> None:
        """Display the stroke order of a pattern from its direction and angle signature"""
        if pattern in ["-", '"-"']:
            pattern = ""
        elif not all(c in "aqwed" for c in pattern):
            return await interaction.response.send_message(
                "❌ Invalid angle signature, must only contain the characters `aqwed`.",
                ephemeral=True,
            )

        pattern_iota, name = _parse_unknown_pattern(UnknownPattern(direction, pattern), self.registry)
        translation = (
            "Unknown" if isinstance(pattern_iota, UnknownPattern) else pattern_iota.localize_pattern_name(self.registry)
        )

        image, _ = generate_image(
            direction=direction,
            pattern=pattern,
            is_great=hide_stroke_order,
            palette=palette,
            theme=theme,
            line_scale=line_scale,
            arrow_scale=arrow_scale,
        )

        await send_pattern(
            registry=self.registry,
            interaction=interaction,
            name=name,
            translation=translation,
            direction=None if hide_stroke_order else direction,
            pattern=None if hide_stroke_order else pattern,
            image=image,
            show_to_everyone=show_to_everyone,
        )

    @app_commands.command()
    @app_commands.describe(
        translation="The name of the pattern",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
        palette="The color palette to use for the lines (has no effect for great spells)",
        theme="Whether the pattern should be rendered for light or dark theme",
        line_scale="The scale of the lines and dots in the image",
        arrow_scale="The scale of the arrows in the image",
    )
    @app_commands.rename(translation="name")
    async def name(
        self,
        interaction: discord.Interaction,
        translation: str,
        show_to_everyone: bool = False,
        palette: Palette = Palette.Classic,
        theme: Theme = Theme.Dark,
        line_scale: SCALE_RANGE = DEFAULT_LINE_SCALE,
        arrow_scale: SCALE_RANGE = DEFAULT_ARROW_SCALE,
    ) -> None:
        """Display the stroke order of a pattern from its name"""
        info = self.registry.from_display_name.get(translation)
        if info is None:
            return await interaction.response.send_message("❌ Unknown pattern.", ephemeral=True)
        elif isinstance(info, SpecialHandlerPatternInfo):
            return await interaction.response.send_message("❌ Use `/pattern special`.", ephemeral=True)

        image, _ = generate_image(
            direction=info.direction,
            pattern=info.pattern,
            is_great=info.is_great,
            palette=palette,
            theme=theme,
            line_scale=line_scale,
            arrow_scale=arrow_scale,
        )

        await send_pattern(
            registry=self.registry,
            interaction=interaction,
            name=info.name,
            translation=translation,
            direction=None if info.is_great else info.direction,
            pattern=None if info.is_great else info.pattern,
            image=image,
            show_to_everyone=show_to_everyone,
        )

    @name.autocomplete("translation")
    async def name_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
        return self.autocomplete.get(current.lower(), [])[:25]

    special = app_commands.Group(name="special", description="Patterns with special handlers")

    @special.command()
    @app_commands.describe(
        bookkeeper="The Bookkeeper's Gambit to generate (eg. v-vv--)",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
        palette="The color palette to use for the lines (has no effect for great spells)",
        theme="Whether the pattern should be rendered for light or dark theme",
        line_scale="The scale of the lines and dots in the image",
        arrow_scale="The scale of the arrows in the image",
    )
    async def bookkeepers_gambit(
        self,
        interaction: discord.Interaction,
        bookkeeper: str,
        show_to_everyone: bool = False,
        palette: Palette = Palette.Classic,
        theme: Theme = Theme.Dark,
        line_scale: SCALE_RANGE = DEFAULT_LINE_SCALE,
        arrow_scale: SCALE_RANGE = DEFAULT_ARROW_SCALE,
    ) -> None:
        """Generate and display a Bookkeeper's Gambit pattern"""
        mask = parse_mask(bookkeeper)
        if not mask:
            return await interaction.response.send_message(
                "❌ Invalid Bookkeeper's Gambit, must not be empty and only contain the characters `v-`.",
                ephemeral=True,
            )

        info = self.registry.from_name["mask"]
        direction, pattern = generate_bookkeeper(mask)

        image, _ = generate_image(
            direction=direction,
            pattern=pattern,
            is_great=info.is_great,
            palette=palette,
            theme=theme,
            line_scale=line_scale,
            arrow_scale=arrow_scale,
        )

        await send_pattern(
            registry=self.registry,
            interaction=interaction,
            name=info.name,
            translation=f"{info.display_name}: {mask}",
            direction=direction,
            pattern=pattern,
            image=image,
            show_to_everyone=show_to_everyone,
        )

    @special.command()
    @app_commands.describe(
        number="The number to generate a literal for",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
        should_align_horizontal="Whether the result should be rotated to minimize height, or use the standard start orientation",
        palette="The color palette to use for the lines (has no effect for great spells)",
        theme="Whether the pattern should be rendered for light or dark theme",
        line_scale="The scale of the lines and dots in the image",
        arrow_scale="The scale of the arrows in the image",
    )
    @app_commands.rename(should_align_horizontal="align_horizontal")
    async def numerical_reflection(
        self,
        interaction: discord.Interaction,
        number: app_commands.Range[int, -MAX_PREGEN_NUMBER, MAX_PREGEN_NUMBER],
        show_to_everyone: bool = False,
        should_align_horizontal: bool = True,
        palette: Palette = Palette.Classic,
        theme: Theme = Theme.Dark,
        line_scale: SCALE_RANGE = DEFAULT_LINE_SCALE,
        arrow_scale: SCALE_RANGE = DEFAULT_ARROW_SCALE,
    ) -> None:
        """Generate and display a Numerical Reflection pattern"""
        if not (gen := self.registry.pregen_numbers.get(number)):
            return await interaction.response.send_message(
                "❌ Failed to generate number literal.",
                ephemeral=True,
            )

        direction, pattern = align_horizontal(*gen) if should_align_horizontal else gen
        info = self.registry.from_name["number"]

        image, _ = generate_image(
            direction=direction,
            pattern=pattern,
            is_great=info.is_great,
            palette=palette,
            theme=theme,
            line_scale=line_scale,
            arrow_scale=arrow_scale,
        )

        await send_pattern(
            registry=self.registry,
            interaction=interaction,
            name=info.name,
            translation=f"{info.display_name}: {number}",
            direction=direction,
            pattern=pattern,
            image=image,
            show_to_everyone=show_to_everyone,
        )


async def setup(bot: HexBugBot) -> None:
    await bot.add_cog(PatternCog(bot))
