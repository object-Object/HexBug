import logging

from discord.ext import tasks
from discord.ext.prometheus import PrometheusCog as BasePrometheusCog

from HexBug.core.bot import HexBugBot
from HexBug.utils.metrics import (
    ACTIVE_COMMANDS_GAUGE,
    APPROX_GUILD_GAUGE,
    APPROX_USER_INSTALL_GAUGE,
    LONGEST_ACTIVE_COMMAND_RUNTIME_GAUGE,
)

logger = logging.getLogger(__name__)


class PrometheusCog(BasePrometheusCog):
    bot: HexBugBot

    def init_gauges(self):
        super().init_gauges()
        if not self.started:
            logger.debug("Initializing custom metrics")
            self.slow_loop.start()

    @tasks.loop(minutes=1)
    async def fast_loop(self):
        ACTIVE_COMMANDS_GAUGE.set(self.bot.num_active_commands)
        LONGEST_ACTIVE_COMMAND_RUNTIME_GAUGE.set(
            self.bot.get_longest_active_command_runtime() or 0
        )

    @tasks.loop(minutes=15)
    async def slow_loop(self):
        app_info = await self.bot.application_info()
        APPROX_GUILD_GAUGE.set(app_info.approximate_guild_count)
        if app_info.approximate_user_install_count is not None:
            APPROX_USER_INSTALL_GAUGE.set(app_info.approximate_user_install_count)


async def setup(bot: HexBugBot):
    await bot.add_cog(PrometheusCog(bot, port=bot.env.metrics_port))
