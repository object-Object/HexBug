from typing import Any, override

from discord import ButtonStyle, Color, Embed
from discord.interactions import Interaction
from discord.ui import ActionRow, Button, Container, LayoutView, TextDisplay
from discord.ui.item import Item

from HexBug.core.bot import HexBugBot, HexBugContext


class SyncView(LayoutView):
    bot: HexBugBot

    def __init__(self, ctx: HexBugContext):
        super().__init__(timeout=60 * 15)
        self.bot = ctx.bot

        container = SyncContainer(ctx.bot)
        if ctx.guild is None:
            container.guild_sync_button.disabled = True
            container.guild_clear_button.disabled = True

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


class SyncContainer(Container[Any]):
    bot: HexBugBot

    def __init__(self, bot: HexBugBot):
        super().__init__()
        self.bot = bot

    global_text = TextDisplay[Any]("**Global**")
    global_row = ActionRow[Any]()

    @global_row.button(label="Sync", style=ButtonStyle.blurple)
    async def global_sync_button(self, interaction: Interaction, button: Button[Any]):
        await interaction.response.defer(ephemeral=False, thinking=True)

        await self.bot.tree.sync(guild=None)

        await interaction.followup.send("Synced global slash commands to all guilds.")

    @global_row.button(label="Clear", style=ButtonStyle.red)
    async def global_clear_button(self, interaction: Interaction, button: Button[Any]):
        await interaction.response.defer(ephemeral=False, thinking=True)

        self.bot.tree.clear_commands(guild=None)
        await self.bot.tree.sync(guild=None)

        await interaction.followup.send(
            "Removed global slash commands from all guilds."
        )

    guild_text = TextDisplay[Any]("**Guild**")
    guild_row = ActionRow[Any]()

    @guild_row.button(label="Sync", style=ButtonStyle.blurple)
    async def guild_sync_button(self, interaction: Interaction, button: Button[Any]):
        assert interaction.guild
        await interaction.response.defer(ephemeral=False, thinking=True)

        self.bot.tree.copy_global_to(guild=interaction.guild)
        await self.bot.tree.sync(guild=interaction.guild)

        await interaction.followup.send("Synced guild slash commands to this guild.")

    @guild_row.button(label="Clear", style=ButtonStyle.red)
    async def guild_clear_button(self, interaction: Interaction, button: Button[Any]):
        assert interaction.guild
        await interaction.response.defer(ephemeral=False, thinking=True)

        self.bot.tree.clear_commands(guild=interaction.guild)
        await self.bot.tree.sync(guild=interaction.guild)

        await interaction.followup.send("Removed guild slash commands from this guild.")

    emoji_text = TextDisplay[Any]("**Emoji**")
    emoji_row = ActionRow[Any]()

    @emoji_row.button(label="Sync", style=ButtonStyle.blurple)
    async def emoji_sync_button(self, interaction: Interaction, button: Button[Any]):
        await interaction.response.defer(ephemeral=False, thinking=True)

        await self.bot.sync_custom_emojis()

        await interaction.followup.send("Synced custom bot emojis.")

    @emoji_row.button(label="Clear", style=ButtonStyle.red)
    async def emoji_clear_button(self, interaction: Interaction, button: Button[Any]):
        await interaction.response.defer(ephemeral=False, thinking=True)

        await self.bot.sync_custom_emojis()

        await interaction.followup.send("Removed custom bot emojis.")
