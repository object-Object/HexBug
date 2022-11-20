from io import BytesIO

import discord
from discord import app_commands
from discord.ext import commands

from hexdecode.hexast import MOD_INFO, Direction, Registry, UnknownPattern, _parse_unknown_pattern, generate_bookkeeper
from utils.commands import HexBugBot, build_autocomplete
from utils.generate_image import Palette, generate_image
from utils.links import build_book_url

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
    direction: Direction,
    pattern: str,
    image: BytesIO,
    ephemeral: bool,
):
    mod, book_url = registry.name_to_url.get(name, (None, None))
    book_url = mod and book_url and build_book_url(mod, book_url, False, False)

    embed = (
        discord.Embed(
            title=translation,
            url=book_url,
            description=registry.name_to_args.get(name),
        )
        .set_image(url="attachment://pattern.png")
        .set_footer(text=f"{direction.name} {pattern}")
    )
    if mod:
        mod_info = MOD_INFO[mod]
        embed.set_author(name=mod, icon_url=mod_info.icon_url, url=mod_info.mod_url)

    await interaction.response.send_message(
        embed=embed,
        file=discord.File(image, filename="pattern.png"),
        ephemeral=ephemeral,
    )


class PatternCog(commands.GroupCog, name="pattern"):
    def __init__(self, bot: HexBugBot) -> None:
        self.bot = bot
        self.registry = bot.registry

        initial_choices: list[tuple[app_commands.Choice[str], list[str]]] = []
        for name, translation in self.registry.name_to_translation.items():
            if translation == "Numerical Reflection":
                continue
            if translation == "Bookkeeper's Gambit":
                translation += ": …"
            initial_choices.append((app_commands.Choice(name=translation, value=translation), [name]))

        self.autocomplete = build_autocomplete(initial_choices)

        super().__init__()

    @app_commands.command()
    @app_commands.describe(
        direction="The starting direction of the pattern",
        pattern='The angle signature of the pattern (eg. aqaawde) — type "-" to leave blank',
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
        hide_stroke_order="Whether or not to hide the stroke order (like with great spells)",
        palette="The color palette to use for the lines (has no effect if hide_stroke_order is True)",
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
        translation = "Unknown" if isinstance(pattern_iota, UnknownPattern) else pattern_iota.localize(self.registry)

        await send_pattern(
            self.registry,
            interaction,
            name,
            translation,
            direction,
            pattern,
            generate_image(direction, pattern, hide_stroke_order, palette, line_scale, arrow_scale),
            not show_to_everyone,
        )

    @app_commands.command()
    @app_commands.describe(
        translation="The name of the pattern",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
        palette="The color palette to use for the lines (has no effect for great spells)",
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
        line_scale: SCALE_RANGE = DEFAULT_LINE_SCALE,
        arrow_scale: SCALE_RANGE = DEFAULT_ARROW_SCALE,
    ) -> None:
        """Display the stroke order of a pattern from its name (no number literals, for now)"""
        if translation.startswith("Bookkeeper's Gambit:"):
            mask = parse_mask(translation)
            if not mask:
                return await interaction.response.send_message(
                    "❌ Invalid Bookkeeper's Gambit, must not be empty and only contain the characters `v-`.",
                    ephemeral=True,
                )

            direction, pattern = generate_bookkeeper(mask)
            is_great = False
            name = "mask"
        elif (value := self.registry.translation_to_pattern.get(translation)) is None:
            return await interaction.response.send_message("❌ Unknown pattern.", ephemeral=True)
        else:
            direction, pattern, is_great, name = value

        await send_pattern(
            self.registry,
            interaction,
            name,
            translation,
            direction,
            pattern,
            generate_image(direction, pattern, is_great, palette, line_scale, arrow_scale),
            not show_to_everyone,
        )

    @name.autocomplete("translation")
    async def name_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
        if current.startswith("Bookkeeper's Gambit:"):
            if parse_mask(current) is not None:  # intentionally "allow" blank mask for autocomplete, more intuitive imo
                return [app_commands.Choice(name=current, value=current)]
        return self.autocomplete.get(current.lower(), [])[:25]


async def setup(bot: HexBugBot) -> None:
    await bot.add_cog(PatternCog(bot))
