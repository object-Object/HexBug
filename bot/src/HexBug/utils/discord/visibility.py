from dataclasses import dataclass
from re import Match
from typing import Any, Awaitable, Callable, Literal

from discord import Embed, Interaction
from discord.app_commands import Command, ContextMenu
from discord.ui import Button, DynamicItem, Item, View
from discord.utils import MISSING

from HexBug.core.bot import HexBugBot
from HexBug.core.emoji import CustomEmoji

from .commands import AnyCommand

type MessageVisibility = Literal["public", "private"]


async def respond_with_visibility(
    interaction: Interaction,
    visibility: MessageVisibility,
    *,
    content: Any | None = None,
    embed: Embed = MISSING,
):
    await MessageContents(
        command=interaction.command,
        content=content,
        embed=embed,
    ).send_response(interaction, visibility)


@dataclass(kw_only=True)
class MessageContents:
    command: AnyCommand | ContextMenu | None
    content: Any | None = None
    embed: Embed = MISSING

    async def send_response(
        self,
        interaction: Interaction,
        visibility: MessageVisibility,
        show_usage: bool = False,
    ):
        await interaction.response.send_message(
            content=self.content,
            embed=self.embed,
            ephemeral=visibility == "private",
            view=self._get_view(interaction, visibility, show_usage),
        )

    def _get_view(
        self,
        interaction: Interaction,
        visibility: MessageVisibility,
        show_usage: bool,
    ):
        view = View(timeout=None)
        add_visibility_buttons(
            view=view,
            interaction=interaction,
            command=self.command,
            visibility=visibility,
            show_usage=show_usage,
            send_as_public=lambda i: self.send_response(i, "public", show_usage=True),
        )
        return view


@dataclass
class SendAsPublicButton(Button[Any]):
    original_interaction: Interaction
    send_as_public: Callable[[Interaction], Awaitable[Any]]

    def __post_init__(self):
        super().__init__(emoji="👁️")

    async def callback(self, interaction: Interaction):
        await self.original_interaction.delete_original_response()
        await self.send_as_public(interaction)


@dataclass
class DeleteButton(
    DynamicItem[Button[Any]],
    template=r"DeleteButton:user:(?P<id>[0-9]+)",
):
    """A button that deletes its message when pressed by the user who created it."""

    user_id: int

    def __post_init__(self):
        super().__init__(
            Button(
                emoji="🗑️",
                custom_id=f"DeleteButton:user:{self.user_id}",
            )
        )

    @classmethod
    async def from_custom_id(
        cls,
        interaction: Interaction,
        item: Item[Any],
        match: Match[str],
    ):
        return cls(user_id=int(match["id"]))

    async def callback(self, interaction: Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.defer()
            return

        # if the bot is in DMs, delete_original_response fails with this error:
        # 404 Not Found (error code: 10015): Unknown Webhook
        # but it works if we first "edit" the message that the component is on
        await interaction.response.edit_message()
        await interaction.delete_original_response()


def get_command_usage_button(
    interaction: Interaction,
    command: AnyCommand | ContextMenu | None,
) -> Button[Any]:
    match command:
        case Command(qualified_name=command_name):
            label = f"{interaction.user.name} used /{command_name}"
        case _:
            label = f"Sent by {interaction.user.name}"
    bot = HexBugBot.of(interaction)
    return Button(
        emoji=bot.get_custom_emoji(CustomEmoji.apps_icon),
        label=label,
        disabled=True,
    )


def add_visibility_buttons(
    *,
    view: View,
    interaction: Interaction,
    command: AnyCommand | ContextMenu | None,
    visibility: MessageVisibility,
    show_usage: bool,
    send_as_public: Callable[[Interaction], Awaitable[Any]],
):
    match visibility:
        case "private":
            view.add_item(SendAsPublicButton(interaction, send_as_public))
        case "public":
            view.add_item(DeleteButton(user_id=interaction.user.id))
            if show_usage:
                view.add_item(get_command_usage_button(interaction, command))
