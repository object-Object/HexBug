import logging
import uuid
from pathlib import Path

from discord.ext import commands

from ..utils.commands import HexBugBot

HEALTH_CHECK_FILE = Path("health_check.txt")

logger = logging.getLogger("bot")


class MessageCommandsCog(commands.Cog):
    def __init__(self, bot: HexBugBot) -> None:
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context):
        """Sync slash commands to this guild"""
        assert ctx.guild
        async with ctx.channel.typing():
            self.bot.tree.copy_global_to(guild=ctx.guild)
            await self.bot.tree.sync(guild=ctx.guild)
        await ctx.reply("✅ Synced slash commands to this guild.")

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def global_sync(self, ctx: commands.Context):
        """Sync slash commands to all guilds"""
        assert ctx.guild
        async with ctx.channel.typing():
            await self.bot.tree.sync()
        await ctx.reply(
            "✅ Synced slash commands to all guilds (may take up to an hour to update everywhere)."
        )

    @commands.command()
    @commands.guild_only()
    async def health_check(self, ctx: commands.Context, raw_uuid: str):
        if ctx.channel.id != self.bot.health_check_channel_id:
            return

        try:
            uuid.UUID(raw_uuid)
        except Exception as e:
            logger.error(
                f"Ignoring health check, malformed UUID: {raw_uuid}"
                + f"\n  {e.__class__.__name__}: {e}"
            )
            await ctx.message.add_reaction("❌")
            return

        logger.info(f"Responding to health check with UUID: {raw_uuid}")
        HEALTH_CHECK_FILE.write_text(raw_uuid)
        await ctx.message.add_reaction("✅")


async def setup(bot: HexBugBot):
    await bot.add_cog(MessageCommandsCog(bot))
