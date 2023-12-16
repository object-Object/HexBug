import discord
from discord import app_commands
from discord.ext import commands

from ..utils.buttons import build_show_or_delete_button
from ..utils.commands import HexBugBot, build_autocomplete
from ..utils.mods import ModTransformerHint


class SourceCog(commands.GroupCog, name="source"):
    def __init__(self, bot: HexBugBot) -> None:
        self.bot = bot
        self.registry = bot.registry

        initial_choices = [
            (
                app_commands.Choice(name=info.display_name, value=info.display_name),
                [info.name, info.classname],
            )
            for info in self.registry.patterns
            if info.classname is not None
        ]
        self.autocomplete = build_autocomplete(initial_choices)

    @app_commands.command()
    @app_commands.describe(
        mod="The mod to link the repository for",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
    )
    async def repo(
        self,
        interaction: discord.Interaction,
        mod: ModTransformerHint,
        show_to_everyone: bool = False,
    ) -> None:
        content = mod.value.build_source_tree_url("")
        await interaction.response.send_message(
            content,
            ephemeral=not show_to_everyone,
            view=build_show_or_delete_button(
                show_to_everyone, interaction, content=content
            ),
        )

    @app_commands.command()
    @app_commands.describe(
        translation="The name of the pattern to link",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
    )
    @app_commands.rename(translation="name")
    async def pattern(
        self,
        interaction: discord.Interaction,
        translation: str,
        show_to_everyone: bool = False,
    ) -> None:
        """Get a link to the web book"""
        if not (info := self.registry.from_display_name.get(translation)):
            return await interaction.response.send_message(
                "❌ Unknown pattern.", ephemeral=True
            )
        mod_info = info.mod.value

        if not (info.classname and info.class_mod and info.path):
            return await interaction.response.send_message(
                f"❌ Source info not found for {translation}.",
                ephemeral=True,
            )

        filename: str = info.path.split("/")[-1]
        source_url = info.class_mod.value.build_source_blob_url(info.path)
        title = (
            filename
            if filename.split(".")[0] == info.classname
            else f"{filename} ({info.classname})"
        )
        embed = (
            discord.Embed(title=title, url=source_url)
            .set_author(
                name=mod_info.name, icon_url=mod_info.icon_url, url=mod_info.mod_url
            )
            .set_footer(text=f"{translation} ({info.name})")
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=not show_to_everyone,
            view=build_show_or_delete_button(
                show_to_everyone, interaction, embed=embed
            ),
        )

    @pattern.autocomplete("translation")
    async def pattern_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice]:
        return self.autocomplete.get(current.lower(), [])[:25]


async def setup(bot: HexBugBot) -> None:
    await bot.add_cog(SourceCog(bot))
