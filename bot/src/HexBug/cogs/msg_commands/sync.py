# pyright: reportUntypedFunctionDecorator=none, reportFunctionMemberAccess=none

from discord.ext import commands

from HexBug.core.bot import HexBugContext
from HexBug.core.cog import HexBugCog
from HexBug.ui.views.sync import SyncView


class SyncCog(HexBugCog):
    """Owner-only message commands for syncing slash commands."""

    async def cog_check(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        ctx: HexBugContext,
    ) -> bool:
        return await commands.is_owner().predicate(ctx)

    @commands.command()
    async def sync(self, ctx: HexBugContext):
        """Open a menu to perform syncing operations."""
        await ctx.reply(view=SyncView(ctx))
