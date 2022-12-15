import discord
from discord import app_commands
from discord.ext import commands

from utils.buttons import buildShowOrDeleteButton
from utils.commands import HexBugBot, build_autocomplete
from utils.mods import Mod, ModTransformerHint


class SourceCog(commands.GroupCog, name="source"):
    def __init__(self, bot: HexBugBot) -> None:
        self.bot = bot
        self.registry = bot.registry

        initial_choices = [
            (app_commands.Choice(name=translation, value=translation), [name, path.split("/")[-1]])
            for translation, (_, path, name, _) in self.registry.translation_to_path.items()
        ]
        self.autocomplete = build_autocomplete(initial_choices)

    @app_commands.command()
    @app_commands.describe(
        mod="The mod to link the repository for",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
    )
    async def repo(
        self, interaction: discord.Interaction, mod: ModTransformerHint, show_to_everyone: bool = False
    ) -> None:
        content = mod.value.source_url
        await interaction.response.send_message(
            content,
            ephemeral=not show_to_everyone,
            view=buildShowOrDeleteButton(show_to_everyone, interaction, content=content),
        )

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

        mod, path, name, classname = value
        filename: str = path.split("/")[-1]
        source_url = mod.value.build_source_url(path)
        title = filename if filename.split(".")[0] == classname else f"{filename} ({classname})"
        embed = (
            discord.Embed(title=title, url=source_url)
            .set_author(name=mod.value.name, icon_url=mod.value.icon_url, url=mod.value.mod_url)
            .set_footer(text=f"{translation} ({name})")
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=not show_to_everyone,
            view=buildShowOrDeleteButton(show_to_everyone, interaction, embed=embed),
        )

    @pattern.autocomplete("translation")
    async def pattern_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice]:
        return self.autocomplete.get(current.lower(), [])[:25]


async def setup(bot: HexBugBot) -> None:
    await bot.add_cog(SourceCog(bot))
