from dataclasses import dataclass
from typing import Any, override

from discord import Embed, File, Interaction, SelectOption, app_commands, ui
from discord.app_commands import ContextMenu, Transform
from discord.app_commands.transformers import EnumNameTransformer
from discord.ext.commands import GroupCog

from HexBug.core.bot import HexBugBot
from HexBug.core.cog import HexBugCog
from HexBug.core.exceptions import InvalidInputError
from HexBug.data.hex_math import VALID_SIGNATURE_PATTERN, HexDir
from HexBug.data.patterns import PatternInfo, PatternOperator
from HexBug.data.registry import HexBugRegistry, PatternMatchResult
from HexBug.data.special_handlers import SpecialHandlerMatch
from HexBug.data.static_data import SPECIAL_HANDLERS
from HexBug.rendering.draw import draw_patterns, get_grid_options, image_to_buffer
from HexBug.rendering.types import Palette, Theme
from HexBug.utils.discord.commands import AnyCommand
from HexBug.utils.discord.transformers import (
    PatternInfoOption,
    SpecialHandlerInfoOption,
)
from HexBug.utils.discord.visibility import MessageVisibility, add_visibility_buttons

PATTERN_FILENAME = "pattern.png"


class PatternCog(HexBugCog, GroupCog, group_name="pattern"):
    @app_commands.command()
    @app_commands.rename(pattern="name")
    async def name(
        self,
        interaction: Interaction,
        pattern: PatternInfoOption,
        visibility: MessageVisibility = "private",
    ):
        await PatternView(
            interaction=interaction,
            pattern=pattern,
            direction=pattern.direction,
            signature=pattern.signature,
            hide_stroke_order=pattern.is_per_world,
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
        result = handler.try_parse_value(self.bot.registry, value)
        if result is None:
            raise InvalidInputError(value, f"Invalid value for {info.base_name}")
        parsed_value, pattern = result

        await PatternView(
            interaction=interaction,
            pattern=SpecialHandlerMatch(
                handler=handler,
                info=info,
                value=parsed_value,
            ),
            direction=pattern.direction,
            signature=pattern.signature,
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
        signature = signature.lower()
        if signature in ["-", '"-"']:
            signature = ""
        elif not VALID_SIGNATURE_PATTERN.fullmatch(signature):
            raise InvalidInputError(
                value=signature,
                message="Invalid signature, must only contain the characters `aqweds`.",
            )

        pattern = self.bot.registry.try_match_pattern(direction, signature)

        await PatternView(
            interaction=interaction,
            pattern=pattern,
            direction=direction,
            signature=signature,
            hide_stroke_order=hide_stroke_order,
        ).send(visibility)


@dataclass(kw_only=True)
class PatternView(ui.View):
    interaction: Interaction
    pattern: PatternMatchResult | None
    direction: HexDir
    signature: str
    hide_stroke_order: bool

    def __post_init__(self):
        super().__init__(timeout=60 * 5)

        self.command: AnyCommand | ContextMenu | None = self.interaction.command
        self.registry: HexBugRegistry = HexBugBot.registry_of(self.interaction)
        self.op_index: int = 0

        self.select_operator.options = [
            SelectOption(
                label=op.plain_args or "→",
                value=str(i),
                default=i == 0,
            )
            for i, op in enumerate(self.operators)
        ]

    @property
    def operators(self) -> list[PatternOperator]:
        match self.pattern:
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
    def pattern_info(self):
        match self.pattern:
            case (PatternInfo() as info) | SpecialHandlerMatch(info=info):
                return info
            case None:
                return None

    @property
    def title(self):
        if self.pattern:
            return self.pattern.name
        if self.signature == "dewdeqwwedaqedwadweqewwd":
            return "Amogus"
        return "Unknown"

    @override
    async def interaction_check(self, interaction: Interaction):
        return interaction.user == self.interaction.user

    @ui.select(cls=ui.Select[Any], min_values=1, max_values=1)
    async def select_operator(self, interaction: Interaction, select: ui.Select[Any]):
        # TODO: why do we need to do this???
        self.select_operator.options[self.op_index].default = False
        self.op_index = int(select.values[0])
        self.select_operator.options[self.op_index].default = True
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

        add_visibility_buttons(
            view=self,
            interaction=self.interaction,
            command=self.command,
            visibility=visibility,
            show_usage=show_usage,
            send_as_public=lambda i: self.send("public", i, show_usage=True),
        )

        if self.should_show_select_menu:
            self.add_item(self.select_operator)

        await self.interaction.response.send_message(
            embed=self.get_embed(),
            file=self.get_image(),
            view=self,
            ephemeral=visibility == "private",
        )

    async def refresh(self, interaction: Interaction):
        await interaction.response.edit_message(
            embed=self.get_embed(),
            attachments=[self.get_image()],
            view=self,
        )

    def get_embed(self) -> Embed:
        if self.operator:
            description_lines = [
                self.operator.args,
                self.operator.description,
            ]
            description = "\n\n".join(line for line in description_lines if line)
        else:
            description = None

        footer = f"{self.direction.name} {self.signature}"
        if self.pattern_info:
            footer = f"{self.pattern_info.id}  •  {footer}"

        embed = (
            Embed(
                title=self.title,
                url=self.operator and self.operator.book_url,
                description=description,
            )
            .set_image(
                url=f"attachment://{PATTERN_FILENAME}",
            )
            .set_footer(
                text=footer,
            )
        )

        if self.mod:
            embed.set_author(
                name=self.mod.name,
                icon_url=self.mod.icon_url,
                url=self.mod.book_url,
            )

        return embed

    def get_image(self) -> File:
        options = get_grid_options(
            palette=Palette.Classic,
            theme=Theme.Dark,
            per_world=self.hide_stroke_order,
        )
        image = draw_patterns(
            (self.direction, self.signature),
            options,
        )
        return File(image_to_buffer(image), PATTERN_FILENAME)
