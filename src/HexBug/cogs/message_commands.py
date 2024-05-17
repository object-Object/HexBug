import io
import logging
import traceback
import uuid
from contextlib import redirect_stderr, redirect_stdout
from textwrap import dedent, indent
from typing import Any, TextIO

import discord
from discord.ext import commands

from ..utils.commands import HexBugBot
from ..utils.environment import Environment

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
    async def health_check(self, ctx: commands.Context, port: int, raw_uuid: str):
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

        logger.debug(f"Responding to health check on port {port} with UUID {raw_uuid}")

        async with self.bot.session.get(
            f"http://localhost:{port}/health-check-reply/{raw_uuid}",
        ) as resp:
            if not resp.ok:
                logger.error(f"Health check request failed: {resp}")
                await ctx.message.add_reaction("❌")
                return

        await ctx.message.add_reaction("✅")

    @commands.command()
    @commands.is_owner()
    @Environment.DEV.check()
    async def exec(self, ctx: commands.Context, *, code: str):
        code = code.strip().removeprefix("```py").strip("`").strip()

        # execute the code and grab all the interesting outputs
        stdout = io.StringIO()
        stderr = io.StringIO()

        locals_ = {
            "discord": discord,
            "ctx": ctx,
            "bot": self.bot,
        }

        try:
            ret, exc = _eval_or_exec(code, stdout, stderr, locals_)
        except Exception:
            ret = None
            exc = traceback.format_exc()

        # prettify
        sections = {
            "Stdout": stdout.getvalue(),
            "Stderr": stderr.getvalue(),
            "Return": repr(ret) if ret is not None else None,
            "Exception": exc,
        }

        if exc:
            color = discord.Color.red()
        else:
            color = discord.Color.green()

        embed = discord.Embed(color=color)

        for name, value in sections.items():
            if value and (value := value.strip()):
                embed.add_field(name=name, value=f"```\n{value}\n```")

        await ctx.send(embed=embed)


def _eval_or_exec(code: str, stdout: TextIO, stderr: TextIO, globals_: dict[str, Any]):
    with redirect_stdout(stdout), redirect_stderr(stderr):
        try:
            return _wrapped_eval(code, globals_)
        except SyntaxError:
            pass

        stdout.truncate()
        stderr.truncate()
        return _wrapped_exec(code, globals_)


def _wrapped_eval(code: str, globals_: dict[str, Any]):
    if "\n" in code:
        raise SyntaxError
    return _wrapped_exec(f"return {code}", globals_)


def _wrapped_exec(code: str, globals_: dict[str, Any]):
    wrapped_code = dedent(
        """\
        import traceback

        def func():
        {}
        
        try:
            globals()["return"] = func()
        except Exception:
            globals()["exception"] = traceback.format_exc()
        """
    ).format(indent(code, " " * 4))

    exec(wrapped_code, globals_)
    return globals_.get("return"), globals_.get("exception")


async def setup(bot: HexBugBot):
    await bot.add_cog(MessageCommandsCog(bot))
