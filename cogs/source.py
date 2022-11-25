import discord
from discord import app_commands
from discord.ext import commands

from utils.commands import HexBugBot, build_autocomplete
from utils.mods import ModName
from utils.urls import build_source_url


class SourceCog(commands.GroupCog, name="source"):
    def __init__(self, bot: HexBugBot) -> None:
        self.bot = bot
        self.registry = bot.registry

        initial_choices = [
            (app_commands.Choice(name=translation, value=translation), [name, path.split("/")[-1]])
            for translation, (mod, path, name) in self.registry.translation_to_path.items()
        ]
        self.autocomplete = build_autocomplete(initial_choices)

    @app_commands.command()
    @app_commands.describe(
        mod="The mod to link the repository for",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
    )
    async def repo(self, interaction: discord.Interaction, mod: ModName, show_to_everyone: bool = False) -> None:
        await interaction.response.send_message(build_source_url(mod, ""), ephemeral=not show_to_everyone)

    @app_commands.command()
    @app_commands.describe(
        translation="The name of the pattern to link",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
    )
    @app_commands.rename(translation="name")
    async def pattern(self, interaction: discord.Interaction, translation: str, show_to_everyone: bool = False) -> None:
        """Get a link to the web book"""
        if not (value := self.registry.translation_to_path.get(translation)):
            return await interaction.response.send_message("❌ Unknown pattern.", ephemeral=True)

        mod, path, name = value
        filename: str = path.split("/")[-1]
        source_url = build_source_url(mod, path)

        await interaction.response.send_message(
            embed=discord.Embed(title=filename, url=source_url).set_author(name=f"{translation} ({name})"),
            ephemeral=not show_to_everyone,
        )

    @pattern.autocomplete("translation")
    async def pattern_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
        return self.autocomplete.get(current.lower(), [])[:25]


async def setup(bot: HexBugBot) -> None:
    await bot.add_cog(SourceCog(bot))
