import logging

from discord.ext import commands

from utils.commands import HexBugBot


class EventsCog(commands.Cog):
    def __init__(self, bot: HexBugBot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.log(logging.INFO, f"logged in as {self.bot.user}")


async def setup(bot: HexBugBot) -> None:
    await bot.add_cog(EventsCog(bot))
