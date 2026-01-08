from discord.ext.prometheus import PrometheusCog

from HexBug.core.bot import HexBugBot


async def setup(bot: HexBugBot):
    await bot.add_cog(PrometheusCog(bot, port=bot.env.metrics_port))
