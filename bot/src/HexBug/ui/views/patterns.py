from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import InitVar, dataclass, field
from typing import Any, Iterable, Self, override

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
from HexBug.data.hex_math import HexAngle, HexDir, HexPattern
from HexBug.data.patterns import PatternInfo, PatternOperator
from HexBug.data.registry import HexBugRegistry, PatternMatchResult
from HexBug.data.special_handlers import SpecialHandlerMatch
from HexBug.db.models import PerWorldPattern
from HexBug.rendering.draw import PatternRenderingOptions
from HexBug.rendering.types import Palette, Theme
from HexBug.utils.discord.commands import AnyCommand
from HexBug.utils.discord.components import update_indexed_select_menu
from HexBug.utils.discord.embeds import FOOTER_SEPARATOR, set_embed_mod_author
from HexBug.utils.discord.translation import translate
from HexBug.utils.discord.visibility import Visibility, add_visibility_buttons
from HexBug.utils.strings import join_truthy

from .options import OptionsView, option_button, option_select

PATTERN_FILENAME = "pattern.png"


@dataclass(kw_only=True)
class BasePatternView(ui.View, ABC):
    interaction: InitVar[Interaction]

    hide_stroke_order: bool

    options: PatternRenderingOptions = field(default_factory=PatternRenderingOptions)
    add_visibility_buttons: bool = True

    user: User | Member = field(init=False)
    default_options: PatternRenderingOptions = field(init=False)

    command: AnyCommand | None = field(default=None, init=False)

    def __post_init__(self, interaction: Interaction):
        super().__init__(timeout=None)

        self.user = interaction.user
        self.default_options = self.options

        if isinstance(interaction.command, Command):
            self.command = interaction.command

    @abstractmethod
    def get_patterns(self) -> Iterable[HexPattern]: ...

    @abstractmethod
    async def get_embeds(self, interaction: Interaction) -> list[Embed]: ...

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
            embeds=await self.get_embeds(interaction),
            files=self.get_attachments(),
            view=self,
            ephemeral=visibility.ephemeral,
        )

    async def refresh(self, interaction: Interaction, *, view: ui.View | None = None):
        await interaction.response.edit_message(
            embeds=await self.get_embeds(interaction),
            attachments=self.get_attachments(),
            view=view or self,
        )

    def get_attachments(self) -> list[File]:
        if patterns := list(self.get_patterns()):
            return [
                self.options.render_discord_file(
                    patterns,
                    hide_stroke_order=self.hide_stroke_order,
                    filename=PATTERN_FILENAME,
                )
            ]
        return []

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
    patterns: Iterable[HexPattern]
    add_footer: bool = True

    @override
    def get_patterns(self) -> Iterable[HexPattern]:
        return self.patterns

    @override
    async def get_embeds(self, interaction: Interaction) -> list[Embed]:
        if not self.patterns:
            return [self.embed]

        return [
            self.embed.set_image(
                url=f"attachment://{PATTERN_FILENAME}",
            ).set_footer(
                text=", ".join(p.display() for p in self.patterns)
                if self.add_footer and not self.hide_stroke_order
                else None,
            )
        ]


@dataclass(kw_only=True)
class NamedPatternView(BasePatternView):
    interaction: InitVar[Interaction]

    pattern: HexPattern
    info: PatternMatchResult | None
    display_info: PatternMatchResult | None = None

    registry: HexBugRegistry = field(init=False, repr=False)

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
    def get_patterns(self) -> list[HexPattern]:
        return [self.pattern]

    @override
    async def get_embeds(self, interaction: Interaction) -> list[Embed]:
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
            set_embed_mod_author(embed, self.mod)

        return [embed]

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

    @classmethod
    async def new(
        cls,
        interaction: Interaction,
        entry: PerWorldPattern,
        contributor: User | Member | None = None,
    ) -> Self:
        bot = HexBugBot.of(interaction)
        return cls(
            interaction=interaction,
            pattern=entry.pattern,
            pattern_id=entry.id,
            info=bot.registry.patterns.get(entry.id),
            contributor=contributor or await bot.fetch_user(entry.user_id),
        )

    @override
    async def get_embeds(self, interaction: Interaction) -> list[Embed]:
        embed = (await super().get_embeds(interaction))[0]

        if not self.info:
            embed.title = str(self.pattern_id)

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

        return [embed]


@dataclass(kw_only=True)
class PatternBuilderView(NamedPatternView):
    pattern: HexPattern = HexPattern(HexDir.EAST, "")
    info: PatternMatchResult | None = None
    add_visibility_buttons: bool = False

    _start_direction: HexDir | None = field(default=None, init=False)
    current_direction: HexDir = field(default=HexDir.EAST, init=False)

    @property
    def start_direction(self):
        return self._start_direction

    @start_direction.setter
    def start_direction(self, direction: HexDir | None):
        self._start_direction = direction
        if direction:
            self.pattern = HexPattern(direction, self.pattern.signature)

    @property
    def signature(self):
        return self.pattern.signature

    @signature.setter
    def signature(self, signature: str):
        self.pattern = HexPattern(self.pattern.direction, signature)

    async def append_direction(self, interaction: Interaction, direction: HexDir):
        if self.start_direction is None:
            self.start_direction = self.current_direction = direction
        else:
            angle = direction.angle_from(self.current_direction)
            self.current_direction = direction
            self.signature += angle.letter
        await self.refresh(interaction)

    @override
    def add_items(
        self,
        interaction: Interaction,
        visibility: Visibility,
        show_usage: bool = False,
    ):
        super().add_items(interaction, visibility, show_usage)
        if visibility is Visibility.PRIVATE:
            for button in [
                self.north_west_button,
                self.north_east_button,
                self.done_button,
                self.west_button,
                self.east_button,
                self.undo_button,
                self.south_west_button,
                self.south_east_button,
                self.clear_button,
            ]:
                self.add_item(button)

    @override
    async def get_embeds(self, interaction: Interaction) -> list[Embed]:
        if self.start_direction is None:
            return []
        return await super().get_embeds(interaction)

    @override
    def get_attachments(self) -> list[File]:
        if self.start_direction is None:
            return []
        return super().get_attachments()

    @override
    async def refresh(self, interaction: Interaction, *, view: ui.View | None = None):
        if not view:
            disabled = self.start_direction is None
            self.done_button.disabled = disabled
            self.undo_button.disabled = disabled
            self.clear_button.disabled = disabled

            if disabled:
                self.info = self.display_info = None
            else:
                self.info = info = self.registry.try_match_pattern(self.pattern)
                self.display_info = (
                    self.registry.display_pattern(info) if info else None
                )

        await (
            interaction.edit_original_response
            if interaction.response.is_done()
            else interaction.response.edit_message
        )(
            embeds=await self.get_embeds(interaction),
            attachments=self.get_attachments(),
            view=view or self,
        )

    # UI

    @ui.button(emoji="↖️", row=2)
    async def north_west_button(self, interaction: Interaction, button: ui.Button[Any]):
        await interaction.response.defer()
        await self.append_direction(interaction, HexDir.NORTH_WEST)

    @ui.button(emoji="↗️", row=2)
    async def north_east_button(self, interaction: Interaction, button: ui.Button[Any]):
        await interaction.response.defer()
        await self.append_direction(interaction, HexDir.NORTH_EAST)

    @ui.button(emoji="✅", row=2, disabled=True)
    async def done_button(self, interaction: Interaction, button: ui.Button[Any]):
        self.add_visibility_buttons = True
        await self.send(interaction, Visibility.PUBLIC, show_usage=True)

    @ui.button(emoji="⬅️", row=3)
    async def west_button(self, interaction: Interaction, button: ui.Button[Any]):
        await interaction.response.defer()
        await self.append_direction(interaction, HexDir.WEST)

    @ui.button(emoji="➡️", row=3)
    async def east_button(self, interaction: Interaction, button: ui.Button[Any]):
        await interaction.response.defer()
        await self.append_direction(interaction, HexDir.EAST)

    @ui.button(emoji="↩️", row=3, disabled=True)
    async def undo_button(self, interaction: Interaction, button: ui.Button[Any]):
        await interaction.response.defer()
        if self.pattern:
            angle = HexAngle[self.signature[-1]]
            self.current_direction = self.current_direction.rotated_by(-angle)
            self.signature = self.signature[:-1]
            await self.refresh(interaction)
        elif self.start_direction:
            self.start_direction = None
            await self.refresh(interaction)

    @ui.button(emoji="↙️", row=4)
    async def south_west_button(self, interaction: Interaction, button: ui.Button[Any]):
        await interaction.response.defer()
        await self.append_direction(interaction, HexDir.SOUTH_WEST)

    @ui.button(emoji="↘️", row=4)
    async def south_east_button(self, interaction: Interaction, button: ui.Button[Any]):
        await interaction.response.defer()
        await self.append_direction(interaction, HexDir.SOUTH_EAST)

    @ui.button(emoji="❌", row=4, disabled=True)
    async def clear_button(self, interaction: Interaction, button: ui.Button[Any]):
        await interaction.response.defer()
        if self.start_direction:
            self.start_direction = None
            self.signature = ""
            await self.refresh(interaction)


class PatternRenderingOptionsView(OptionsView):
    def __init__(self, *, parent: BasePatternView):
        self.parent: BasePatternView = parent

        super().__init__(timeout=None)

        if self.options.freeze_palette:
            self.remove_item(self.palette_select)

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
