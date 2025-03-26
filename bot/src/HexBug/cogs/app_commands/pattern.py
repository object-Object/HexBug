from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Self, override

from discord import (
    ButtonStyle,
    Color,
    DiscordException,
    Embed,
    File,
    Interaction,
    Member,
    SelectOption,
    User,
    app_commands,
    ui,
)
from discord.app_commands import ContextMenu, Transform
from discord.app_commands.transformers import EnumNameTransformer
from discord.ext.commands import GroupCog
from hexdoc.core import ResourceLocation

from HexBug.core.bot import HexBugBot
from HexBug.core.cog import HexBugCog
from HexBug.core.exceptions import InvalidInputError
from HexBug.core.translator import translate_text
from HexBug.data.hex_math import VALID_SIGNATURE_PATTERN, HexDir, HexPattern
from HexBug.data.patterns import PatternInfo, PatternOperator
from HexBug.data.registry import HexBugRegistry, PatternMatchResult
from HexBug.data.special_handlers import SpecialHandlerMatch
from HexBug.data.static_data import SPECIAL_HANDLERS
from HexBug.rendering.draw import PatternRenderingOptions
from HexBug.rendering.types import Palette, Theme
from HexBug.utils.discord.commands import AnyCommand
from HexBug.utils.discord.components import update_indexed_select_menu
from HexBug.utils.discord.editable_button import (
    EditableButton,
    EditableButtonView,
    editable_button,
)
from HexBug.utils.discord.transformers import (
    PatternInfoOption,
    SpecialHandlerInfoOption,
)
from HexBug.utils.discord.visibility import (
    MessageVisibility,
    add_visibility_buttons,
    respond_with_visibility,
)
from HexBug.utils.strings import join_truthy

PATTERN_FILENAME = "pattern.png"


class PatternCog(HexBugCog, GroupCog, group_name="pattern"):
    @app_commands.command()
    @app_commands.rename(info="name")
    async def name(
        self,
        interaction: Interaction,
        info: PatternInfoOption,
        visibility: MessageVisibility = "private",
    ):
        await PatternView(
            interaction=interaction,
            pattern=info.pattern,
            info=info,
            hide_stroke_order=info.is_per_world,
        ).send(visibility)

    @app_commands.command()
    @app_commands.rename(info="name")
    async def special(
        self,
        interaction: Interaction,
        info: SpecialHandlerInfoOption,
        value: str,
        visibility: MessageVisibility = "private",
    ):
        handler = SPECIAL_HANDLERS[info.id]
        try:
            parsed_value, pattern = handler.parse_value(self.bot.registry, value)
        except ValueError as e:
            raise InvalidInputError(
                value, f"Failed to parse value for {info.base_name}."
            ) from e

        await PatternView(
            interaction=interaction,
            pattern=pattern,
            info=SpecialHandlerMatch(
                handler=handler,
                info=info,
                value=parsed_value,
            ),
            hide_stroke_order=False,
        ).send(visibility)

    @app_commands.command()
    async def raw(
        self,
        interaction: Interaction,
        direction: Transform[HexDir, EnumNameTransformer(HexDir)],
        signature: str,
        visibility: MessageVisibility = "private",
        hide_stroke_order: bool = False,
    ):
        signature = validate_signature(signature)
        pattern = HexPattern(direction, signature)

        info = self.bot.registry.try_match_pattern(pattern)

        await PatternView(
            interaction=interaction,
            pattern=pattern,
            info=info,
            hide_stroke_order=hide_stroke_order,
        ).send(visibility)

    @app_commands.command()
    async def check(
        self,
        interaction: Interaction,
        signature: str,
        is_per_world: bool,
        visibility: MessageVisibility = "private",
    ):
        signature = validate_signature(signature)
        pattern = HexPattern(HexDir.EAST, signature)

        conflicts = dict[ResourceLocation, PatternMatchResult]()

        if conflict := self.bot.registry.try_match_pattern(pattern):
            conflicts[conflict.id] = conflict

        if is_per_world:
            segments = pattern.get_aligned_segments()
            for conflict in self.bot.registry.lookups.segments.get(segments, []):
                conflicts[conflict.id] = conflict

        title = await translate_text(interaction, "title", conflicts=len(conflicts))

        if conflicts:
            embed = Embed(
                title=title,
                description="\n".join(
                    f"- {conflict.name} (`{conflict.id}`)"
                    for conflict in conflicts.values()
                ),
                color=Color.red(),
            )
        else:
            embed = Embed(
                description=title,
                color=Color.green(),
            )

        await respond_with_visibility(interaction, visibility, embed=embed)


def validate_signature(signature: str) -> str:
    signature = signature.lower()
    if signature in ["-", '"-"']:
        signature = ""
    elif not VALID_SIGNATURE_PATTERN.fullmatch(signature):
        raise InvalidInputError(
            value=signature,
            message="Invalid signature, must only contain the characters `aqweds`.",
        )
    return signature


@dataclass(kw_only=True)
class PatternView(ui.View):
    interaction: Interaction
    pattern: HexPattern
    info: PatternMatchResult | None
    hide_stroke_order: bool

    def __post_init__(self):
        super().__init__(timeout=60 * 15)

        self.command: AnyCommand | ContextMenu | None = self.interaction.command
        self.registry: HexBugRegistry = HexBugBot.registry_of(self.interaction)
        self.op_index: int = 0
        self.options: PatternRenderingOptions = PatternRenderingOptions()
        self.options_interaction: Interaction | None = None

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
        match self.info:
            case PatternInfo(operators=operators):
                return operators
            case SpecialHandlerMatch(info=info):
                return [info.operator]
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

    @property
    def title(self):
        if self.pattern.signature == "dewdeqwwedaqedwadweqewwd":
            return "Amogus"
        if self.info:
            return self.info.name
        return "Unknown"

    @override
    async def interaction_check(self, interaction: Interaction):
        return interaction.user == self.interaction.user

    @ui.button(emoji="⚙️")
    async def options_button(self, interaction: Interaction, button: ui.Button[Self]):
        if self.options_interaction:
            try:
                await self.options_interaction.delete_original_response()
            except DiscordException:
                pass

        self.options_interaction = interaction
        await interaction.response.send_message(
            view=PatternRenderingOptionsView(
                on_change=self.refresh,
                user=self.interaction.user,
                options=self.options,
            ),
            ephemeral=True,
        )

    @ui.select(cls=ui.Select[Any], min_values=1, max_values=1)
    async def operator_select(self, interaction: Interaction, select: ui.Select[Self]):
        self.op_index = update_indexed_select_menu(select)[0]
        await self.refresh(interaction)

    async def send(
        self,
        visibility: MessageVisibility,
        interaction: Interaction | None = None,
        show_usage: bool = False,
    ):
        if interaction:
            self.interaction = interaction

        self.clear_items()

        self.add_item(self.options_button)

        add_visibility_buttons(
            view=self,
            interaction=self.interaction,
            command=self.command,
            visibility=visibility,
            show_usage=show_usage,
            send_as_public=lambda i: self.send("public", i, show_usage=True),
        )

        if self.should_show_select_menu:
            self.add_item(self.operator_select)

        await self.interaction.response.send_message(
            embed=self.get_embed(),
            file=self.get_image(),
            view=self,
            ephemeral=visibility == "private",
        )

    async def refresh(self, interaction: Interaction | None = None):
        if interaction:
            await interaction.response.edit_message(
                embed=self.get_embed(),
                attachments=[self.get_image()],
                view=self,
            )
        else:
            await self.interaction.edit_original_response(
                embed=self.get_embed(),
                attachments=[self.get_image()],
                view=self,
            )

    def get_embed(self) -> Embed:
        embed = (
            Embed(
                title=self.title,
            )
            .set_image(
                url=f"attachment://{PATTERN_FILENAME}",
            )
            .set_footer(
                text=join_truthy(
                    "  •  ",
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

    def get_image(self) -> File:
        return self.options.render_discord_file(
            self.pattern,
            hide_stroke_order=self.hide_stroke_order,
            filename=PATTERN_FILENAME,
        )


class PatternRenderingOptionsView(EditableButtonView):
    def __init__(
        self,
        *,
        on_change: Callable[[], Awaitable[Any]],
        user: User | Member,
        options: PatternRenderingOptions,
        defaults: PatternRenderingOptions | None = None,
    ):
        self.user = user
        self.options = options
        self.defaults = defaults or PatternRenderingOptions()

        super().__init__(on_change=on_change, timeout=60 * 15)

        self.refresh_selects()

    def refresh_selects(self):
        for option in self.palette_select.options:
            option.default = self.options.palette.name == option.label

        for option in self.theme_select.options:
            option.default = self.options.theme.name == option.label

    @override
    async def interaction_check(self, interaction: Interaction):
        return interaction.user == self.user

    @ui.select(
        cls=ui.Select[Any],
        options=[
            SelectOption(label=palette.name, value=str(i))
            for i, palette in enumerate(Palette)
        ],
        row=0,
    )
    async def palette_select(self, interaction: Interaction, select: ui.Select[Any]):
        i = update_indexed_select_menu(select)[0]
        old_value = self.options.palette
        self.options.palette = Palette(select.options[i].label)
        await self.on_editable_button_success(
            interaction,
            changed=old_value != self.options.palette,
        )

    @ui.select(
        cls=ui.Select[Any],
        options=[
            SelectOption(label=theme.name, value=str(i))
            for i, theme in enumerate(Theme)
        ],
        row=1,
    )
    async def theme_select(self, interaction: Interaction, select: ui.Select[Any]):
        i = update_indexed_select_menu(select)[0]
        old_value = self.options.theme
        self.options.theme = Theme(select.options[i].label)
        await self.on_editable_button_success(
            interaction,
            changed=old_value != self.options.theme,
        )

    @editable_button(
        name="Line width",
        required=True,
        row=2,
    )
    def line_width_button(self):
        return self.options.line_width

    @line_width_button.setter
    def _set_line_width(self, value: Any):
        self.options.line_width = value

    @editable_button(
        name="Point radius",
        required=False,
        row=2,
    )
    def point_radius_button(self):
        return self.options.point_radius

    @point_radius_button.setter
    def _set_point_radius(self, value: Any):
        self.options.point_radius = value or None

    @editable_button(
        name="Arrow radius",
        required=False,
        row=2,
    )
    def arrow_radius_button(self):
        return self.options.arrow_radius

    @arrow_radius_button.setter
    def _set_arrow_radius(self, value: Any):
        self.options.arrow_radius = value or None

    @editable_button(
        name="Maximum overlaps",
        required=True,
        row=3,
    )
    def max_overlaps_button(self):
        return self.options.max_overlaps

    @max_overlaps_button.setter
    def _set_max_overlaps(self, value: Any):
        self.options.max_overlaps = value

    @editable_button(
        name="Scale",
        required=True,
        row=3,
    )
    def scale_button(self):
        return self.options.scale

    @scale_button.setter
    def _set_scale(self, value: Any):
        self.options.scale = value

    @editable_button(
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
        label="Reset to defaults",
        style=ButtonStyle.danger,
        row=4,
    )
    async def reset_button(self, interaction: Interaction, button: ui.Button[Self]):
        changed = False
        for name, value in self.defaults:
            if value != getattr(self.options, name):
                changed = True
                setattr(self.options, name, value)

        self.refresh_selects()
        for item in self.children:
            if isinstance(item, EditableButton):
                item.refresh_label()

        await self.on_editable_button_success(interaction, changed)
