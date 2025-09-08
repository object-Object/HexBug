from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import InitVar, dataclass, field
from typing import Any, Self, override

from discord import (
    ButtonStyle,
    Embed,
    File,
    Interaction,
    Member,
    SelectOption,
    User,
    ui,
)
from discord.app_commands import Command
from hexdoc.core import ResourceLocation

from HexBug.core.bot import HexBugBot
from HexBug.data.hex_math import HexPattern
from HexBug.data.patterns import PatternInfo, PatternOperator
from HexBug.data.registry import HexBugRegistry, PatternMatchResult
from HexBug.data.special_handlers import SpecialHandlerMatch
from HexBug.rendering.draw import PatternRenderingOptions
from HexBug.rendering.types import Palette, Theme
from HexBug.utils.discord.commands import AnyCommand
from HexBug.utils.discord.components import update_indexed_select_menu
from HexBug.utils.discord.embeds import FOOTER_SEPARATOR
from HexBug.utils.discord.translation import translate
from HexBug.utils.discord.visibility import Visibility, add_visibility_buttons
from HexBug.utils.strings import join_truthy

from .options import OptionsView, option_button, option_select

PATTERN_FILENAME = "pattern.png"


@dataclass(kw_only=True)
class BasePatternView(ui.View, ABC):
    interaction: InitVar[Interaction]

    pattern: HexPattern
    hide_stroke_order: bool

    options: PatternRenderingOptions = field(default_factory=PatternRenderingOptions)
    default_options: PatternRenderingOptions = field(
        default_factory=PatternRenderingOptions
    )
    add_visibility_buttons: bool = True

    user: User | Member = field(init=False)

    command: AnyCommand | None = field(default=None, init=False)

    def __post_init__(self, interaction: Interaction):
        super().__init__(timeout=None)

        self.user = interaction.user

        if isinstance(interaction.command, Command):
            self.command = interaction.command

    @abstractmethod
    async def get_embed(self, interaction: Interaction) -> Embed: ...

    async def send(
        self,
        interaction: Interaction,
        visibility: Visibility,
        *,
        content: str | None = None,
        show_usage: bool = False,
    ):
        self.clear_items()
        self.add_items(interaction, visibility, show_usage)
        await interaction.response.send_message(
            content=content,
            embed=await self.get_embed(interaction),
            file=self.get_image(),
            view=self,
            ephemeral=visibility.ephemeral,
        )

    async def refresh(self, interaction: Interaction, *, view: ui.View | None = None):
        await interaction.response.edit_message(
            embed=await self.get_embed(interaction),
            attachments=[self.get_image()],
            view=view or self,
        )

    def get_image(self) -> File:
        return self.options.render_discord_file(
            self.pattern,
            hide_stroke_order=self.hide_stroke_order,
            filename=PATTERN_FILENAME,
        )

    def add_items(
        self,
        interaction: Interaction,
        visibility: Visibility,
        show_usage: bool = False,
    ):
        self.add_item(self.options_button)

        if self.add_visibility_buttons:
            add_visibility_buttons(
                self,
                interaction,
                visibility,
                command=self.command,
                show_usage=show_usage,
                send_as_public=lambda i: self.send(
                    i, Visibility.PUBLIC, show_usage=True
                ),
            )

    @override
    async def interaction_check(self, interaction: Interaction):
        return interaction.user == self.user

    # UI components

    @ui.button(emoji="⚙️")
    async def options_button(self, interaction: Interaction, button: ui.Button[Self]):
        await interaction.response.edit_message(
            view=PatternRenderingOptionsView(parent=self),
        )


@dataclass(kw_only=True)
class EmbedPatternView(BasePatternView):
    embed: Embed

    @override
    async def get_embed(self, interaction: Interaction) -> Embed:
        return self.embed.set_image(
            url=f"attachment://{PATTERN_FILENAME}",
        ).set_footer(
            text=self.pattern.display() if not self.hide_stroke_order else None,
        )


@dataclass(kw_only=True)
class NamedPatternView(BasePatternView):
    interaction: InitVar[Interaction]

    info: PatternMatchResult | None
    display_info: PatternMatchResult | None = None

    registry: HexBugRegistry = field(init=False)

    op_index: int = field(default=0, init=False)

    def __post_init__(self, interaction: Interaction):
        super().__post_init__(interaction)

        self.registry = HexBugBot.registry_of(interaction)

        if self.info and not self.display_info:
            self.display_info = self.registry.display_pattern(self.info)

        self.operator_select.options = [
            SelectOption(
                label=op.plain_args or "→",
                value=str(i),
                default=i == 0,
            )
            for i, op in enumerate(self.operators)
        ]

    @property
    def operators(self) -> list[PatternOperator]:
        match self.display_info:
            case PatternInfo(operators=operators):
                return operators
            case SpecialHandlerMatch(operator=operator):
                return [operator]
            case None:
                return []

    @property
    def should_show_select_menu(self):
        return len(self.operators) > 1

    @property
    def operator(self):
        if self.operators:
            return self.operators[self.op_index]

    @property
    def mod(self):
        if self.operator:
            return self.registry.mods[self.operator.mod_id]
        if self.display_info:
            return self.registry.mods[self.display_info.mod_id]

    @property
    def title(self):
        if self.pattern.signature == "dewdeqwwedaqedwadweqewwd":
            return "Amogus"
        if self.display_info:
            return self.display_info.name
        return "Unknown"

    @override
    async def get_embed(self, interaction: Interaction) -> Embed:
        embed = (
            Embed(
                title=self.title,
            )
            .set_image(
                url=f"attachment://{PATTERN_FILENAME}",
            )
            .set_footer(
                text=join_truthy(
                    FOOTER_SEPARATOR,
                    self.info and self.info.id,
                    not self.hide_stroke_order and self.pattern.display(),
                ),
            )
        )

        if self.operator:
            embed.description = join_truthy(
                "\n\n",
                self.operator.args,
                self.operator.description,
            )
            if self.operator.book_url:
                embed.url = str(self.operator.book_url)

        if self.mod:
            embed.set_author(
                name=self.mod.name,
                icon_url=self.mod.icon_url,
                url=self.mod.book_url,
            )

        return embed

    @override
    def add_items(
        self,
        interaction: Interaction,
        visibility: Visibility,
        show_usage: bool = False,
    ):
        super().add_items(interaction, visibility, show_usage)

        if self.should_show_select_menu:
            self.add_item(self.operator_select)

    # UI components

    @ui.select(cls=ui.Select[Any], min_values=1, max_values=1)
    async def operator_select(self, interaction: Interaction, select: ui.Select[Self]):
        self.op_index = update_indexed_select_menu(select)[0]
        await self.refresh(interaction)


@dataclass(kw_only=True)
class PerWorldPatternView(NamedPatternView):
    pattern_id: ResourceLocation
    contributor: User | Member
    hide_stroke_order: bool = False

    @override
    async def get_embed(self, interaction: Interaction) -> Embed:
        embed = await super().get_embed(interaction)
        embed.set_footer(
            text=join_truthy(
                FOOTER_SEPARATOR,
                await translate(
                    interaction,
                    "per-world-pattern-contributor",
                    name=self.contributor.name,
                ),
                self.pattern_id,
                self.pattern.display(),
            ),
            icon_url=self.contributor.display_avatar.url,
        )
        return embed


class PatternRenderingOptionsView(OptionsView):
    def __init__(self, *, parent: BasePatternView):
        self.parent: BasePatternView = parent

        super().__init__(timeout=None)

    @property
    def options(self):
        return self.parent.options

    @options.setter
    def options(self, options: PatternRenderingOptions):
        self.parent.options = options

    @override
    async def interaction_check(self, interaction: Interaction):
        return interaction.user == self.parent.user

    @override
    async def on_change(self, interaction: Interaction):
        await self.parent.refresh(interaction, view=self)

    @option_select(
        labels=[palette.name for palette in Palette],
        row=0,
    )
    def palette_select(self):
        return self.options.palette.name

    @palette_select.setter
    def _set_palette(self, label: str):
        self.options.palette = Palette(label)

    @option_select(
        labels=[theme.name for theme in Theme],
        row=1,
    )
    def theme_select(self):
        return self.options.theme.name

    @theme_select.setter
    def _set_theme(self, label: str):
        self.options.theme = Theme(label)

    @option_button(
        name="Line width",
        required=True,
        row=2,
    )
    def line_width_button(self):
        return self.options.line_width

    @line_width_button.setter
    def _set_line_width(self, value: Any):
        self.options.line_width = value

    @option_button(
        name="Point radius",
        required=False,
        row=2,
    )
    def point_radius_button(self):
        return self.options.point_radius

    @point_radius_button.setter
    def _set_point_radius(self, value: Any):
        self.options.point_radius = value or None

    @option_button(
        name="Arrow radius",
        required=False,
        row=2,
    )
    def arrow_radius_button(self):
        return self.options.arrow_radius

    @arrow_radius_button.setter
    def _set_arrow_radius(self, value: Any):
        self.options.arrow_radius = value or None

    @option_button(
        name="Maximum overlaps",
        required=True,
        row=3,
    )
    def max_overlaps_button(self):
        return self.options.max_overlaps

    @max_overlaps_button.setter
    def _set_max_overlaps(self, value: Any):
        self.options.max_overlaps = value

    @option_button(
        name="Scale",
        required=True,
        row=3,
    )
    def scale_button(self):
        return self.options.scale

    @scale_button.setter
    def _set_scale(self, value: Any):
        self.options.scale = value

    @option_button(
        name="Maximum grid width",
        required=True,
        row=3,
    )
    def max_grid_width_button(self):
        return self.options.max_grid_width

    @max_grid_width_button.setter
    def _set_max_grid_width(self, value: Any):
        self.options.max_grid_width = value

    @ui.button(
        label="Done",
        style=ButtonStyle.primary,
        row=4,
    )
    async def done_button(self, interaction: Interaction, button: ui.Button[Self]):
        await interaction.response.edit_message(view=self.parent)
        self.stop()

    @ui.button(
        label="Reset to defaults",
        style=ButtonStyle.danger,
        row=4,
    )
    async def reset_button(self, interaction: Interaction, button: ui.Button[Self]):
        changed = self.options != self.parent.default_options
        self.options = self.parent.default_options.model_copy(deep=True)
        self.refresh_option_items()
        await self.on_option_item_success(interaction, changed)
