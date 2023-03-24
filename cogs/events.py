import logging

import discord
from discord import app_commands
from discord.ext import commands

from utils.buttons import get_full_command
from utils.commands import HexBugBot


class EventsCog(commands.Cog):
    def __init__(self, bot: HexBugBot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.getLogger("bot").info(f"logged in as {self.bot.user}")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        # log commands in case something breaks and i need to see how
        if interaction.type == discord.InteractionType.application_command and isinstance(
            command := interaction.command, app_commands.Command
        ):
            user = interaction.user
            user_info = f"{user.name}#{user.discriminator} ({user.id})"
            logging.getLogger("bot").debug(f"{user_info} ran {get_full_command(interaction, command)}")


async def setup(bot: HexBugBot) -> None:
    await bot.add_cog(EventsCog(bot))
