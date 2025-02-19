from typing import Callable, Sequence, TypedDict, overload

import discord
from discord import app_commands
from discord.utils import MISSING
from typing_extensions import Unpack

TIMEOUT = 120


class MessageProps(TypedDict, total=False):
    content: str
    embed: discord.Embed
    file: discord.File
    files: Sequence[discord.File]


def build_show_or_delete_button(
    show_to_everyone: bool,
    interaction: discord.Interaction,
    builder: Callable[[bool], MessageProps] | None = None,
    **kwargs: Unpack[MessageProps],
) -> discord.ui.View:
    """If both builder and kwargs are specified, builder will take precedence in case of conflict."""
    if show_to_everyone:
        return DeleteButton(interaction)
    if builder:
        return ShowToEveryoneButton(interaction, builder, **kwargs)
    return ShowToEveryoneButton(interaction=interaction, **kwargs)


def get_full_command(
    interaction: discord.Interaction,
    command: app_commands.Command,
    truncate: bool = True,
) -> str:
    args = " ".join(
        f"{name}: {str(value)[:100] + ' ... (truncated)' if truncate and len(str(value)) > 100 else value}"
        for name, value in interaction.namespace
    )
    return f"/{command.qualified_name} {args}".rstrip()


@overload
def get_user_used_command_message(
    interaction: discord.Interaction,
    content: None = None,
) -> str | None:
    ...


@overload
def get_user_used_command_message(
    interaction: discord.Interaction,
    content: str,
) -> str:
    ...


def get_user_used_command_message(
    interaction: discord.Interaction,
    content: str | None = None,
) -> str | None:
    command = interaction.command
    if not isinstance(command, app_commands.Command):
        return content

    result = (
        f"{interaction.user.mention} used `{get_full_command(interaction, command)}`"
    )
    if content is not None:
        result += f"\n{content}"
    return result


class _BaseButton(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=TIMEOUT)
        self.interaction = interaction

    async def on_timeout(self) -> None:
        await self.delete_buttons()

    async def delete_message(self) -> None:
        await self.interaction.delete_original_response()
        self.stop()

    async def disable_buttons(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        await self.interaction.edit_original_response(view=self)

    async def delete_buttons(self) -> None:
        await self.interaction.edit_original_response(view=None)


class ShowToEveryoneButton(_BaseButton):
    def __init__(
        self,
        interaction: discord.Interaction,
        builder: Callable[[bool], MessageProps] | None = None,
        **kwargs: Unpack[MessageProps],
    ):
        super().__init__(interaction)
        self.builder = builder
        self.kwargs = kwargs

    @discord.ui.button(label="Show to everyone", style=discord.ButtonStyle.gray)
    async def button(self, interaction: discord.Interaction, button: discord.ui.Button):
        props = self.kwargs.copy()
        if self.builder:
            props |= self.builder(True)

        if "file" in props and props["file"] is not MISSING:
            props["file"].reset()

        if "files" in props and props["files"] is not MISSING:
            for f in props["files"]:
                f.reset()

        orig_content = props.get("content", "")
        if orig_content is MISSING or orig_content == "...":
            orig_content = ""

        props["content"] = get_user_used_command_message(self.interaction, orig_content)

        await interaction.response.send_message(
            **props,
            allowed_mentions=discord.AllowedMentions.none(),
            view=DeleteButton(interaction=interaction),
        )
        await self.delete_message()


class DeleteButton(_BaseButton):
    @discord.ui.button(emoji="🗑️", style=discord.ButtonStyle.gray)
    async def button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            return await interaction.response.send_message(
                f"Only {self.interaction.user.mention} can do that.",
                ephemeral=True,
            )
        await self.delete_message()
