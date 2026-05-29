import logging

from discord.ext import tasks
from discord.ext.prometheus import PrometheusCog as BasePrometheusCog
from discord.ext.prometheus.prometheus_cog import METRIC_PREFIX
from prometheus_client import Gauge, Histogram

from HexBug.core.bot import HexBugBot

logger = logging.getLogger(__name__)

COMMAND_RUNTIME_HISTOGRAM = Histogram(
    METRIC_PREFIX + "command_runtime",
    "Runtime in seconds of all executed commands",
)

ACTIVE_COMMANDS_GAUGE = Gauge(
    METRIC_PREFIX + "active_commands",
    "The number of currently active commands",
)

LONGEST_ACTIVE_COMMAND_RUNTIME_GAUGE = Gauge(
    METRIC_PREFIX + "longest_active_command_runtime",
    "The longest runtime in seconds of any currently active command",
)

APPROX_GUILD_GAUGE = Gauge(
    METRIC_PREFIX + "stat_approx_guilds",
    "The approximate count of the guilds the bot was added to",
)

APPROX_USER_INSTALL_GAUGE = Gauge(
    METRIC_PREFIX + "stat_approx_user_installs",
    "The approximate count of the user-level installations the bot has",
)


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
