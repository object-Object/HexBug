from dataclasses import dataclass
from typing import Any, override

from discord import Embed, File, Interaction, SelectOption, app_commands, ui
from discord.app_commands import ContextMenu
from discord.ext.commands import GroupCog

from HexBug.core.bot import HexBugBot
from HexBug.core.cog import HexBugCog
from HexBug.data.patterns import PatternInfo
from HexBug.data.registry import HexBugRegistry
from HexBug.rendering.draw import draw_patterns, get_grid_options, image_to_buffer
from HexBug.rendering.types import Palette, Theme
from HexBug.utils.discord.commands import AnyCommand
from HexBug.utils.discord.transformers import PatternInfoOption
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
        await PatternView(interaction, pattern).send(visibility)


@dataclass
class PatternView(ui.View):
    interaction: Interaction
    pattern: PatternInfo

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
            for i, op in enumerate(self.pattern.operators)
        ]

    @property
    def should_show_select_menu(self):
        return len(self.pattern.operators) > 1

    @property
    def operator(self):
        return self.pattern.operators[self.op_index]

    @property
    def mod(self):
        return self.registry.mods[self.operator.mod_id]

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
        return (
            Embed(
                title=self.pattern.name,
                url=self.operator.book_url,
                description="\n\n".join(
                    line
                    for line in [
                        self.operator.args,
                        self.operator.description,
                    ]
                    if line
                ),
            )
            .set_image(
                url=f"attachment://{PATTERN_FILENAME}",
            )
            .set_author(
                name=self.mod.name,
                icon_url=self.mod.icon_url,
                url=self.mod.book_url,
            )
            .set_footer(
                text=f"{self.pattern.id}  •  {self.pattern.direction.name} {self.pattern.signature}",
            )
        )

    def get_image(self) -> File:
        options = get_grid_options(
            palette=Palette.Classic,
            theme=Theme.Dark,
            per_world=self.pattern.is_per_world,
        )
        image = draw_patterns(
            (self.pattern.direction, self.pattern.signature),
            options,
        )
        return File(image_to_buffer(image), PATTERN_FILENAME)
