import discord
from discord import app_commands
from discord.ext import commands

from hexdecode.hexast import ModName
from utils.commands import HexBugBot, build_autocomplete
from utils.links import build_book_url


class BookCog(commands.GroupCog, name="book"):
    def __init__(self, bot: HexBugBot) -> None:
        self.bot = bot
        self.registry = bot.registry
        self.autocomplete = build_autocomplete(
            [
                (app_commands.Choice(name=title, value=title), names)
                for title, (_, _, names) in self.registry.page_title_to_url.items()
            ]
        )

    @app_commands.command()
    @app_commands.describe(
        mod="The mod to link the home page for",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
        show_spoilers="Whether the link should have spoilers unblurred or not",
    )
    async def home(
        self,
        interaction: discord.Interaction,
        mod: ModName,
        show_to_everyone: bool = False,
        show_spoilers: bool = False,
    ) -> None:
        await interaction.response.send_message(
            build_book_url(mod, "", show_spoilers, True), ephemeral=not show_to_everyone
        )

    @app_commands.command()
    @app_commands.describe(
        page_title="The title of the page to link",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
        show_spoilers="Whether the link should have spoilers unblurred or not",
    )
    async def page(
        self,
        interaction: discord.Interaction,
        page_title: str,
        show_to_everyone: bool = False,
        show_spoilers: bool = False,
    ) -> None:
        """Get a link to the web book"""
        if not (value := self.registry.page_title_to_url.get(page_title)):
            return await interaction.response.send_message("❌ Unknown page.", ephemeral=True)

        mod, url, _ = value
        await interaction.response.send_message(
            build_book_url(mod, url, show_spoilers, True), ephemeral=not show_to_everyone
        )

    @page.autocomplete("page_title")
    async def page_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
        return self.autocomplete.get(current.lower(), [])[:25]


async def setup(bot: HexBugBot) -> None:
    await bot.add_cog(BookCog(bot))
