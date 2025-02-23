# pyright: reportUntypedFunctionDecorator=none, reportFunctionMemberAccess=none

from discord.ext import commands

from HexBug.discord.bot import HexBugContext
from HexBug.discord.cog import HexBugCog


class SyncCog(HexBugCog):
    """Owner-only message commands for syncing slash commands."""

    async def cog_check(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        ctx: HexBugContext,
    ) -> bool:
        return await commands.is_owner().predicate(ctx)

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def sync(self, ctx: HexBugContext):
        """Sync guild slash commands to the current guild."""

        assert ctx.guild

        async with ctx.channel.typing():
            self.bot.tree.copy_global_to(guild=ctx.guild)
            await self.bot.tree.sync(guild=ctx.guild)

        await ctx.reply("Synced guild slash commands to this guild.")

    @sync.command(name="all", aliases=["global"])
    async def sync_all(self, ctx: HexBugContext):
        """Sync global slash commands to all guilds."""

        async with ctx.channel.typing():
            await self.bot.tree.sync()

        await ctx.reply("Synced global slash commands to all guilds.")

    @sync.command(name="emoji", aliases=["emojis", "emotes"])
    async def sync_emoji(self, ctx: HexBugContext):
        async with ctx.channel.typing():
            await self.bot.sync_custom_emojis()

        await ctx.reply("Synced custom bot emojis.")

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def clear(self, ctx: HexBugContext):
        """Remove guild slash commands from the current guild."""

        assert ctx.guild

        async with ctx.channel.typing():
            self.bot.tree.clear_commands(guild=ctx.guild)
            await self.bot.tree.sync(guild=ctx.guild)

        await ctx.reply("Removed guild slash commands from this guild.")

    @clear.command(name="all", aliases=["global"])
    async def clear_all(self, ctx: HexBugContext):
        """Sync global slash commands to all guilds."""

        async with ctx.channel.typing():
            self.bot.tree.clear_commands(guild=None)
            await self.bot.tree.sync()

        await ctx.reply("Removed global slash commands from all guilds.")
