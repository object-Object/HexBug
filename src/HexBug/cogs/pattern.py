from collections import defaultdict
from dataclasses import dataclass, field

import discord
from discord import Interaction, app_commands, ui
from discord.ext import commands
from PIL import Image

from ..hexdecode.hex_math import Angle, Direction
from ..hexdecode.hexast import generate_bookkeeper
from ..hexdecode.pregen_numbers import MAX_PREGEN_NUMBER
from ..hexdecode.registry import (
    DuplicatePattern,
    PatternInfo,
    Registry,
    SpecialHandlerPatternInfo,
)
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
from ..utils.buttons import (
    DeleteButton,
    build_show_or_delete_button,
    get_user_used_command_message,
)
from ..utils.commands import HexBugBot, build_autocomplete
from ..utils.mods import APIWithoutBookModInfo, ModTransformerHint
from ..utils.patterns import align_horizontal, parse_mask

WIDTH_RANGE = app_commands.Range[float, 0.01]
SCALE_RANGE = app_commands.Range[float, 1.0]
MAX_OVERLAPS_RANGE = app_commands.Range[int, 1]

PATTERN_FILENAME = "pattern.png"


def get_pattern_embed(
    *,
    info: PatternInfo | None,
    translation: str,
    direction: Direction | None,
    pattern: str | None,
):
    mod_info = info and info.mod.value

    book_url = None
    if (
        info
        and mod_info
        and not isinstance(mod_info, APIWithoutBookModInfo)
        and info.book_url is not None
    ):
        book_url = mod_info.build_book_url(info.book_url, False, False)

    # why am i allowed to write code lmao
    description = None
    if info:
        description = "\n".join(v for v in [info.args, info.description] if v)

    embed = discord.Embed(
        title=translation,
        url=book_url,
        description=description,
    ).set_image(url=f"attachment://{PATTERN_FILENAME}")
    if mod_info:
        embed.set_author(
            name=mod_info.name,
            icon_url=mod_info.icon_url,
            url=mod_info.mod_url,
        )
    if direction is not None and pattern is not None:
        embed.set_footer(text=f"{direction.name} {pattern}")

    return embed


async def send_pattern(
    *,
    info: PatternInfo | None,
    interaction: Interaction,
    translation: str,
    direction: Direction | None,
    pattern: str | None,
    image: Image.Image,
    show_to_everyone: bool,
):
    embed = get_pattern_embed(
        info=info,
        translation=translation,
        direction=direction,
        pattern=pattern,
    )

    file = discord.File(image_to_buffer(image), filename=PATTERN_FILENAME)

    await interaction.response.send_message(
        embed=embed,
        file=file,
        view=build_show_or_delete_button(
            show_to_everyone,
            interaction,
            embed=embed,
            file=file,
        ),
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
            initial_choices.append(
                (
                    app_commands.Choice(
                        name=info.display_name, value=info.display_name
                    ),
                    [info.name],
                )
            )

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
    )
    async def raw(
        self,
        interaction: Interaction,
        direction: Direction,
        pattern: str,
        show_to_everyone: bool = False,
        hide_stroke_order: bool = False,
        palette: Palette = Palette.Classic,
        theme: Theme = Theme.Dark,
        line_width: WIDTH_RANGE = DEFAULT_LINE_WIDTH,
        point_radius: WIDTH_RANGE | None = None,
        arrow_radius: WIDTH_RANGE | None = None,
        max_overlaps: MAX_OVERLAPS_RANGE = DEFAULT_MAX_OVERLAPS,
        scale: SCALE_RANGE = DEFAULT_SCALE,
    ) -> None:
        """Display the stroke order of a pattern from its direction and angle signature"""
        if pattern in ["-", '"-"']:
            pattern = ""
        elif not all(c in "aqweds" for c in pattern):
            return await interaction.response.send_message(
                "❌ Invalid angle signature, must only contain the characters `aqweds`.",
                ephemeral=True,
            )

        info = self.registry.parse_unknown_pattern(direction, pattern)

        translation = translate_pattern(info)

        options = get_grid_options(
            palette,
            theme,
            per_world=hide_stroke_order,
            line_width=line_width,
            point_radius=point_radius,
            arrow_radius=arrow_radius,
            max_overlaps=max_overlaps,
        )
        image = draw_patterns(
            (direction, pattern),
            options,
            scale=scale,
        )

        await send_pattern(
            info=info,
            interaction=interaction,
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
    )
    @app_commands.rename(translation="name")
    async def name(
        self,
        interaction: Interaction,
        translation: str,
        show_to_everyone: bool = False,
        palette: Palette = Palette.Classic,
        theme: Theme = Theme.Dark,
        line_width: WIDTH_RANGE = DEFAULT_LINE_WIDTH,
        point_radius: WIDTH_RANGE | None = None,
        arrow_radius: WIDTH_RANGE | None = None,
        max_overlaps: MAX_OVERLAPS_RANGE = DEFAULT_MAX_OVERLAPS,
        scale: SCALE_RANGE = DEFAULT_SCALE,
    ) -> None:
        """Display the stroke order of a pattern from its name"""
        info = self.registry.from_display_name.get(translation)
        if info is None:
            return await interaction.response.send_message(
                "❌ Unknown pattern.", ephemeral=True
            )
        elif isinstance(info, SpecialHandlerPatternInfo):
            return await interaction.response.send_message(
                "❌ Use `/pattern special`.", ephemeral=True
            )

        options = get_grid_options(
            palette,
            theme,
            per_world=info.is_great,
            line_width=line_width,
            point_radius=point_radius,
            arrow_radius=arrow_radius,
            max_overlaps=max_overlaps,
        )
        image = draw_patterns(
            (info.direction, info.pattern),
            options,
            scale=scale,
        )

        await send_pattern(
            info=info,
            interaction=interaction,
            translation=translation,
            direction=None if info.is_great else info.direction,
            pattern=None if info.is_great else info.pattern,
            image=image,
            show_to_everyone=show_to_everyone,
        )

    @name.autocomplete("translation")
    async def name_autocomplete(
        self, interaction: Interaction, current: str
    ) -> list[app_commands.Choice]:
        return self.autocomplete.get(current.lower(), [])[:25]

    @app_commands.command()
    @app_commands.describe(
        translation="The name of the pattern",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
        palette="The color palette to use for the lines (has no effect for great spells)",
        theme="Whether the pattern should be rendered for light or dark theme",
    )
    @app_commands.rename(translation="name")
    async def from_mod(
        self,
        interaction: Interaction,
        mod: ModTransformerHint,
        translation: str,
        show_to_everyone: bool = False,
        palette: Palette = Palette.Classic,
        theme: Theme = Theme.Dark,
        line_width: WIDTH_RANGE = DEFAULT_LINE_WIDTH,
        point_radius: WIDTH_RANGE | None = None,
        arrow_radius: WIDTH_RANGE | None = None,
        max_overlaps: MAX_OVERLAPS_RANGE = DEFAULT_MAX_OVERLAPS,
        scale: SCALE_RANGE = DEFAULT_SCALE,
    ) -> None:
        """Display the stroke order of a pattern from a particular mod given the pattern's name"""
        info = self.registry.from_display_name.get(translation)
        if info is None or info.mod != mod:
            return await interaction.response.send_message(
                "❌ Unknown pattern.", ephemeral=True
            )
        elif isinstance(info, SpecialHandlerPatternInfo):
            return await interaction.response.send_message(
                "❌ Use `/pattern special`.", ephemeral=True
            )

        options = get_grid_options(
            palette,
            theme,
            per_world=info.is_great,
            line_width=line_width,
            point_radius=point_radius,
            arrow_radius=arrow_radius,
            max_overlaps=max_overlaps,
        )
        image = draw_patterns(
            (info.direction, info.pattern),
            options,
            scale=scale,
        )

        await send_pattern(
            info=info,
            interaction=interaction,
            translation=translation,
            direction=None if info.is_great else info.direction,
            pattern=None if info.is_great else info.pattern,
            image=image,
            show_to_everyone=show_to_everyone,
        )

    @from_mod.autocomplete("translation")
    async def from_mod_autocomplete(
        self, interaction: Interaction, current: str
    ) -> list[app_commands.Choice]:
        return [
            c
            for c in self.autocomplete.get(current.lower(), [])
            if self.registry.from_display_name[c.value].mod.name
            == interaction.namespace.mod
        ][:25]

    special = app_commands.Group(
        name="special", description="Patterns with special handlers"
    )

    @special.command()
    @app_commands.describe(
        bookkeeper="The Bookkeeper's Gambit to generate (eg. v-vv--)",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
        palette="The color palette to use for the lines (has no effect for great spells)",
        theme="Whether the pattern should be rendered for light or dark theme",
    )
    async def bookkeepers_gambit(
        self,
        interaction: Interaction,
        bookkeeper: str,
        show_to_everyone: bool = False,
        palette: Palette = Palette.Classic,
        theme: Theme = Theme.Dark,
        line_width: WIDTH_RANGE = DEFAULT_LINE_WIDTH,
        point_radius: WIDTH_RANGE | None = None,
        arrow_radius: WIDTH_RANGE | None = None,
        max_overlaps: MAX_OVERLAPS_RANGE = DEFAULT_MAX_OVERLAPS,
        scale: SCALE_RANGE = DEFAULT_SCALE,
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

        options = get_grid_options(
            palette,
            theme,
            per_world=info.is_great,
            line_width=line_width,
            point_radius=point_radius,
            arrow_radius=arrow_radius,
            max_overlaps=max_overlaps,
        )
        image = draw_patterns(
            (direction, pattern),
            options,
            scale=scale,
        )

        await send_pattern(
            info=info,
            interaction=interaction,
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
    )
    @app_commands.rename(should_align_horizontal="align_horizontal")
    async def numerical_reflection(
        self,
        interaction: Interaction,
        number: app_commands.Range[int, -MAX_PREGEN_NUMBER, MAX_PREGEN_NUMBER],
        show_to_everyone: bool = False,
        should_align_horizontal: bool = False,
        palette: Palette = Palette.Classic,
        theme: Theme = Theme.Dark,
        line_width: WIDTH_RANGE = DEFAULT_LINE_WIDTH,
        point_radius: WIDTH_RANGE | None = None,
        arrow_radius: WIDTH_RANGE | None = None,
        max_overlaps: MAX_OVERLAPS_RANGE = DEFAULT_MAX_OVERLAPS,
        scale: SCALE_RANGE = DEFAULT_SCALE,
    ) -> None:
        """Generate and display a Numerical Reflection pattern"""
        if not (gen := self.registry.pregen_numbers.get(number)):
            return await interaction.response.send_message(
                "❌ Failed to generate number literal.",
                ephemeral=True,
            )

        direction, pattern = (
            align_horizontal(*gen, True) if should_align_horizontal else gen
        )
        info = self.registry.from_name["number"]

        options = get_grid_options(
            palette,
            theme,
            per_world=info.is_great,
            line_width=line_width,
            point_radius=point_radius,
            arrow_radius=arrow_radius,
            max_overlaps=max_overlaps,
        )
        image = draw_patterns(
            (direction, pattern),
            options,
            scale=scale,
        )

        # nothing to see here, move along
        translation = f"{info.display_name}: "
        if number == 69:
            translation += "69 (nice)"
        elif number == 1984:
            translation += "Literally 1984"
        else:
            translation += str(number)

        await send_pattern(
            info=info,
            interaction=interaction,
            translation=translation,
            direction=direction,
            pattern=pattern,
            image=image,
            show_to_everyone=show_to_everyone,
        )

    @app_commands.command()
    @app_commands.describe(
        pattern='The angle signature of the pattern (eg. aqaawde) — type "-" to leave blank',
        is_great="Whether the pattern should be considered a great spell or not",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
    )
    async def check(
        self,
        interaction: Interaction,
        pattern: str,
        is_great: bool,
        show_to_everyone: bool = False,
    ) -> None:
        """Check if a pattern exists in any of HexBug's supported mods (ignores numbers/bookkeepers)"""

        if pattern in ["-", '"-"']:
            pattern = ""
        elif not all(c in "aqweds" for c in pattern):
            return await interaction.response.send_message(
                "❌ Invalid angle signature, must only contain the characters `aqweds`.",
                ephemeral=True,
            )

        embed = discord.Embed()

        duplicates = self.registry.get_duplicates(
            pattern=pattern,
            is_great=is_great,
            name=None,
            translation=None,
        )

        if duplicates:
            es = "" if len(duplicates) == 1 else "es"
            embed.title = f"Match{es} found!"

            duplicates_by_attribute = defaultdict[str, list[DuplicatePattern]](list)
            for dupe in duplicates:
                duplicates_by_attribute[dupe.attribute].append(dupe)

            for attribute in sorted(duplicates_by_attribute.keys()):
                embed.add_field(
                    name=f"Same {attribute}",
                    value="\n".join(
                        f"* {duplicate.info.display_name} (`{duplicate.info.id}`)"
                        for duplicate in duplicates_by_attribute[attribute]
                    ),
                    inline=False,
                )
        else:
            embed.description = "No matches found."

        # TODO: this is copied in a lot of places, it should probably be a function
        await interaction.response.send_message(
            embed=embed,
            view=build_show_or_delete_button(
                show_to_everyone,
                interaction,
                embed=embed,
            ),
            ephemeral=not show_to_everyone,
        )

    @app_commands.command()
    @app_commands.describe(
        hide_stroke_order="Whether or not to hide the stroke order (like with great spells)",
        palette="The color palette to use for the lines (has no effect if hide_stroke_order is True)",
        theme="Whether the pattern should be rendered for light or dark theme",
    )
    async def build(
        self,
        interaction: Interaction,
        hide_stroke_order: bool = False,
        palette: Palette = Palette.Classic,
        theme: Theme = Theme.Dark,
        line_width: WIDTH_RANGE = DEFAULT_LINE_WIDTH,
        point_radius: WIDTH_RANGE | None = None,
        arrow_radius: WIDTH_RANGE | None = None,
        max_overlaps: MAX_OVERLAPS_RANGE = DEFAULT_MAX_OVERLAPS,
        scale: SCALE_RANGE = DEFAULT_SCALE,
    ):
        """Draw a pattern incrementally using directional buttons"""

        await interaction.response.send_message(
            view=PatternBuilderView(
                registry=self.registry,
                interaction=interaction,
                hide_stroke_order=hide_stroke_order,
                palette=palette,
                theme=theme,
                line_width=line_width,
                point_radius=point_radius,
                arrow_radius=arrow_radius,
                max_overlaps=max_overlaps,
                scale=scale,
            ),
            ephemeral=True,
        )


@dataclass(kw_only=True)
class PatternBuilderView(ui.View):
    registry: Registry
    interaction: Interaction
    hide_stroke_order: bool
    palette: Palette
    theme: Theme
    line_width: float
    point_radius: float | None
    arrow_radius: float | None
    max_overlaps: int
    scale: float

    start_direction: Direction | None = field(default=None, init=False)
    current_direction: Direction = field(default=Direction.EAST, init=False)
    pattern: str = field(default="", init=False)

    def __post_init__(self):
        super().__init__(timeout=60 * 5)

    # buttons

    @ui.button(emoji="↖️", row=0)
    async def button_north_west(self, interaction: Interaction, button: ui.Button):
        await self.append_direction(Direction.NORTH_WEST)
        await interaction.response.defer()

    @ui.button(emoji="↗️", row=0)
    async def button_north_east(self, interaction: Interaction, button: ui.Button):
        await self.append_direction(Direction.NORTH_EAST)
        await interaction.response.defer()

    @ui.button(emoji="✅", row=0, disabled=True)
    async def button_done(self, interaction: Interaction, button: ui.Button):
        embed = self.get_embed()
        if embed is None:
            await interaction.response.defer()
            return

        await interaction.response.send_message(
            content=get_user_used_command_message(self.interaction),
            embed=embed,
            files=self.get_attachments(),
            view=DeleteButton(interaction),
            ephemeral=False,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        await self.interaction.delete_original_response()

    @ui.button(emoji="⬅️", row=1)
    async def button_west(self, interaction: Interaction, button: ui.Button):
        await self.append_direction(Direction.WEST)
        await interaction.response.defer()

    @ui.button(emoji="➡️", row=1)
    async def button_east(self, interaction: Interaction, button: ui.Button):
        await self.append_direction(Direction.EAST)
        await interaction.response.defer()

    @ui.button(emoji="↩️", row=1, disabled=True)
    async def button_undo(self, interaction: Interaction, button: ui.Button):
        if self.pattern:
            angle = Angle[self.pattern[-1]]
            self.current_direction = self.current_direction.rotated(-angle)
            self.pattern = self.pattern[:-1]
            await self.refresh()
        elif self.start_direction:
            self.start_direction = None
            await self.refresh()
        await interaction.response.defer()

    @ui.button(emoji="↙️", row=2)
    async def button_south_west(self, interaction: Interaction, button: ui.Button):
        await self.append_direction(Direction.SOUTH_WEST)
        await interaction.response.defer()

    @ui.button(emoji="↘️", row=2)
    async def button_south_east(self, interaction: Interaction, button: ui.Button):
        await self.append_direction(Direction.SOUTH_EAST)
        await interaction.response.defer()

    @ui.button(emoji="❌", row=2, disabled=True)
    async def button_clear(self, interaction: Interaction, button: ui.Button):
        if self.start_direction:
            self.start_direction = None
            self.pattern = ""
            await self.refresh()
        await interaction.response.defer()

    # helper methods

    async def append_direction(self, direction: Direction):
        if self.start_direction is None:
            self.start_direction = self.current_direction = direction
        else:
            angle = direction.angle_from(self.current_direction)
            self.current_direction = direction
            self.pattern += angle.letter
        await self.refresh()

    async def refresh(self):
        disabled = self.start_direction is None
        self.button_done.disabled = disabled
        self.button_undo.disabled = disabled
        self.button_clear.disabled = disabled

        await self.interaction.edit_original_response(
            embed=self.get_embed(),
            attachments=self.get_attachments(),
            view=self,
        )

    def get_embed(self) -> discord.Embed | None:
        if self.start_direction is None:
            return None

        info = self.registry.parse_unknown_pattern(self.start_direction, self.pattern)
        translation = translate_pattern(info)

        return get_pattern_embed(
            info=info,
            translation=translation,
            direction=self.start_direction,
            pattern=self.pattern,
        )

    def get_attachments(self) -> list[discord.File]:
        if self.start_direction is None:
            return []

        options = get_grid_options(
            self.palette,
            self.theme,
            per_world=self.hide_stroke_order,
            line_width=self.line_width,
            point_radius=self.point_radius,
            arrow_radius=self.arrow_radius,
            max_overlaps=self.max_overlaps,
        )
        image = draw_patterns(
            (self.start_direction, self.pattern),
            options,
            scale=self.scale,
        )

        return [discord.File(image_to_buffer(image), filename=PATTERN_FILENAME)]


def translate_pattern(info: PatternInfo | None) -> str:
    if info is None:
        return "Unknown"
    if info.pattern == "dewdeqwwedaqedwadweqewwd":
        return "Amogus"
    return info.print()


async def setup(bot: HexBugBot) -> None:
    await bot.add_cog(PatternCog(bot))
