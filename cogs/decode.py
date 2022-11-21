from io import BytesIO

import discord
from discord import app_commands
from discord.ext import commands

from hexdecode import revealparser
from hexdecode.hexast import massage_raw_pattern_list
from utils.commands import HexBugBot


class DecodeCog(commands.Cog):
    def __init__(self, bot: HexBugBot) -> None:
        self.bot = bot
        self.registry = bot.registry

    @app_commands.command()
    @app_commands.describe(
        data="The result of calling Reveal on your pattern list",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
    )
    async def decode(self, interaction: discord.Interaction, data: str, show_to_everyone: bool = False):
        """Decode a pattern list using hexdecode"""
        await interaction.response.defer(ephemeral=not show_to_everyone, thinking=True)

        output = ""
        level = 0
        for pattern in revealparser.parse(data):
            for iota in massage_raw_pattern_list(pattern, self.registry):
                level = iota.preadjust(level)
                output += iota.print(level, False, self.registry) + "\n"
                level = iota.postadjust(level)

        if not output:
            return await interaction.followup.send("❌ Invalid input.", ephemeral=True)

        result = f"```\n{output}```"
        if len(result) > 2000:
            return await interaction.followup.send(
                "⚠️ Result is too long to display. See attached file.",
                ephemeral=True,
                file=discord.File(BytesIO(output.encode("utf-8")), filename="decoded.txt"),
            )

        await interaction.followup.send(f"```\n{output}```", ephemeral=not show_to_everyone)


async def setup(bot: HexBugBot) -> None:
    await bot.add_cog(DecodeCog(bot))
