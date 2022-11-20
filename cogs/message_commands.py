from discord.ext import commands

from utils.commands import HexBugBot


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
        await ctx.reply("✅ Synced slash commands to all guilds (may take up to an hour to update everywhere).")


async def setup(bot: HexBugBot):
    await bot.add_cog(MessageCommandsCog(bot))
