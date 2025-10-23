from typing import Iterable, Self, override

from discord import Embed, Interaction, Member, SelectOption, User, ui
from discord.ui import Select, View

from HexBug.utils.discord.commands import AnyInteractionCommand
from HexBug.utils.discord.components import update_indexed_select_menu
from HexBug.utils.discord.visibility import Visibility, add_visibility_buttons


class EmbedSwitcherView(View):
    user: User | Member
    command: AnyInteractionCommand
    embeds: list[Embed]
    embed_index: int = 0

    def __init__(
        self,
        *,
        user: User | Member,
        command: AnyInteractionCommand,
        embeds: Iterable[Embed],
        options: Iterable[SelectOption] | None = None,
        timeout: float | None = 60 * 10,
    ):
        super().__init__(timeout=timeout)
        self.user = user
        self.command = command
        self.embeds = list(embeds)

        if options:
            for i, option in enumerate(options):
                option = option.copy()
                option.value = str(i)
                option.default = i == 0
                self.embed_select.options.append(option)

            if (a := len(self.embeds)) != (b := len(self.embed_select.options)):
                raise ValueError(
                    f"Mismatched embeds and options: got {a} embeds but {b} options"
                )
        else:
            self.embed_select.options = [
                SelectOption(
                    label=embed.title or f"Option {i + 1}",
                    value=str(i),
                    default=i == 0,
                )
                for i, embed in enumerate(embeds)
            ]

    @property
    def embed(self):
        return self.embeds[self.embed_index]

    async def send(
        self,
        interaction: Interaction,
        visibility: Visibility,
        *,
        _show_usage: bool = False,
    ):
        self.clear_items()
        self._add_items(interaction, visibility, _show_usage)
        await interaction.response.send_message(
            embed=self.embed,
            view=self,
            ephemeral=visibility.ephemeral,
        )

    def _add_items(
        self,
        interaction: Interaction,
        visibility: Visibility,
        _show_usage: bool = False,
    ):
        add_visibility_buttons(
            self,
            interaction,
            visibility,
            command=self.command,
            show_usage=_show_usage,
            send_as_public=lambda i: self.send(i, Visibility.PUBLIC, _show_usage=True),
        )
        if len(self.embeds) > 1:
            self.add_item(self.embed_select)

    @override
    async def interaction_check(self, interaction: Interaction):
        return interaction.user == self.user

    @ui.select()
    async def embed_select(self, interaction: Interaction, select: Select[Self]):
        self.embed_index = update_indexed_select_menu(select)[0]
        await interaction.response.edit_message(embed=self.embed, view=self)
