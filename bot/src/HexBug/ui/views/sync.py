from re import Match
from types import MethodType
from typing import Any, Awaitable, Callable, override

from discord import ButtonStyle, Color, Embed
from discord.interactions import Interaction
from discord.ui import (
    ActionRow,
    Button,
    Container,
    DynamicItem,
    LayoutView,
    TextDisplay,
)
from discord.ui.item import Item

from HexBug.core.bot import HexBugBot, HexBugContext


class SyncView(LayoutView):
    bot: HexBugBot

    def __init__(self, ctx: HexBugContext):
        super().__init__(timeout=60 * 15)
        self.bot = ctx.bot

        container = SyncContainer(ctx.bot)
        if ctx.guild is None:
            for item in container.guild_row.children:
                match item:
                    case Button():
                        item.disabled = True
                    case DynamicItem(item=Button() as button):  # pyright: ignore[reportUnknownVariableType]
                        button.disabled = True
                    case _:
                        pass

        self.add_item(container)

    @override
    async def interaction_check(self, interaction: Interaction) -> bool:
        return await self.bot.is_owner(interaction.user)

    @override
    async def on_error(
        self,
        interaction: Interaction,
        error: Exception,
        item: Item[Any],
    ):
        embed = Embed(
            title=error.__class__.__name__,
            description=f"```\n{error}\n```",
            color=Color.red(),
        )
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


type SyncButtonCallback = Callable[[SyncButton, Interaction], Awaitable[Any]]


class SyncButton(
    DynamicItem[Button[Any]],
    template=r"SyncButton:index:(?P<index>[0-9]+)",
):
    def __init__(self, index: int):
        callback, label, style = self.buttons[index]
        super().__init__(
            Button(
                label=label,
                style=style,
                custom_id=f"SyncButton:index:{index}",
            )
        )
        self.callback = MethodType(callback, self)

    @classmethod
    async def from_custom_id(
        cls,
        interaction: Interaction,
        item: Item[Any],
        match: Match[str],
    ):
        return cls(int(match["index"]))

    @classmethod
    def from_callback(cls, callback: SyncButtonCallback):
        return cls(cls.buttons_lookup[callback])

    async def global_sync_button(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=False, thinking=True)

        bot = HexBugBot.of(interaction)
        await bot.tree.sync(guild=None)

        await interaction.followup.send("Synced global slash commands to all guilds.")

    async def global_clear_button(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=False, thinking=True)

        bot = HexBugBot.of(interaction)
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync(guild=None)

        await interaction.followup.send(
            "Removed global slash commands from all guilds."
        )

    async def guild_sync_button(self, interaction: Interaction):
        assert interaction.guild
        await interaction.response.defer(ephemeral=False, thinking=True)

        bot = HexBugBot.of(interaction)
        bot.tree.copy_global_to(guild=interaction.guild)
        await bot.tree.sync(guild=interaction.guild)

        await interaction.followup.send("Synced guild slash commands to this guild.")

    async def guild_clear_button(self, interaction: Interaction):
        assert interaction.guild
        await interaction.response.defer(ephemeral=False, thinking=True)

        bot = HexBugBot.of(interaction)
        bot.tree.clear_commands(guild=interaction.guild)
        await bot.tree.sync(guild=interaction.guild)

        await interaction.followup.send("Removed guild slash commands from this guild.")

    async def emoji_sync_button(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=False, thinking=True)

        bot = HexBugBot.of(interaction)
        await bot.sync_custom_emojis()

        await interaction.followup.send("Synced custom bot emojis.")

    async def emoji_clear_button(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=False, thinking=True)

        bot = HexBugBot.of(interaction)
        await bot.sync_custom_emojis()

        await interaction.followup.send("Removed custom bot emojis.")

    buttons = [
        (global_sync_button, "Sync", ButtonStyle.blurple),
        (global_clear_button, "Clear", ButtonStyle.red),
        (guild_sync_button, "Sync", ButtonStyle.blurple),
        (guild_clear_button, "Clear", ButtonStyle.red),
        (emoji_sync_button, "Sync", ButtonStyle.blurple),
        (emoji_clear_button, "Clear", ButtonStyle.red),
    ]

    buttons_lookup: dict[SyncButtonCallback, int] = {
        button: i for i, (button, _, _) in enumerate(buttons)
    }


class SyncContainer(Container[Any]):
    bot: HexBugBot

    def __init__(self, bot: HexBugBot):
        super().__init__()
        self.bot = bot

    global_text = TextDisplay[Any]("**Global**")
    global_row = ActionRow[Any](
        SyncButton.from_callback(SyncButton.global_sync_button),
        SyncButton.from_callback(SyncButton.global_clear_button),
    )

    guild_text = TextDisplay[Any]("**Guild**")
    guild_row = ActionRow[Any](
        SyncButton.from_callback(SyncButton.guild_sync_button),
        SyncButton.from_callback(SyncButton.guild_clear_button),
    )

    emoji_text = TextDisplay[Any]("**Emoji**")
    emoji_row = ActionRow[Any](
        SyncButton.from_callback(SyncButton.emoji_sync_button),
        SyncButton.from_callback(SyncButton.emoji_clear_button),
    )
