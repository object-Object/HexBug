import discord
from discord import app_commands
from discord.ext import commands

from utils.buttons import build_show_or_delete_button
from utils.commands import HexBugBot
from utils.mods import ModTransformerHint


class ModCog(commands.Cog):
    def __init__(self, bot: HexBugBot) -> None:
        self.bot = bot

    @app_commands.command()
    @app_commands.describe(
        mod="The mod to show information about",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
    )
    async def mod(
        self, interaction: discord.Interaction, mod: ModTransformerHint, show_to_everyone: bool = False
    ) -> None:
        """Show information and links for a specific mod"""
        mod_info = mod.value

        embed = discord.Embed(title=mod_info.name).set_footer(text=f"Version: {mod_info.version}")
        if mod_info.curseforge_url:
            embed.add_field(name="CurseForge", value=mod_info.curseforge_url, inline=False)
        if mod_info.modrinth_url:
            embed.add_field(name="Modrinth", value=mod_info.modrinth_url, inline=False)
        if mod_info.book_url:
            embed.add_field(name="Web Book", value=mod_info.book_url, inline=False)
        embed.add_field(name="Source", value=mod_info.source_url, inline=False)
        if mod_info.icon_url:
            embed.set_thumbnail(url=mod_info.icon_url)

        await interaction.response.send_message(
            embed=embed,
            ephemeral=not show_to_everyone,
            view=build_show_or_delete_button(show_to_everyone, interaction, embed=embed),
        )


async def setup(bot: HexBugBot) -> None:
    await bot.add_cog(ModCog(bot))
