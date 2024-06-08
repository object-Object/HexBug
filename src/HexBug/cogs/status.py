import os
import textwrap

import discord
from discord import app_commands
from discord.ext import commands

from HexBug.utils.buttons import build_show_or_delete_button
from HexBug.utils.commands import HexBugBot
from HexBug.utils.git import get_commit_datetime, get_commit_message, get_current_commit
from HexBug.utils.mods import MODS


class StatusCog(commands.Cog):
    def __init__(self, bot: HexBugBot) -> None:
        self.bot = bot

    @app_commands.command()
    @app_commands.describe(
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
    )
    async def status(
        self,
        interaction: discord.Interaction,
        show_to_everyone: bool = False,
    ) -> None:
        """Show information about HexBug"""

        commit_sha = get_current_commit(".", short=None)
        commit_url = f"https://github.com/object-Object/HexBug/commit/{commit_sha}"
        commit_message = get_commit_message(".", commit_sha)
        commit_datetime = get_commit_datetime(".", commit_sha)
        commit_timestamp = int(commit_datetime.timestamp())

        deploy_timestamp = int(os.getenv("DEPLOYMENT_TIMESTAMP", "0"))

        restart_timestamp = int(self.bot.start_time.timestamp())

        commands = list(self.bot.tree.walk_commands())

        embed = (
            discord.Embed(title="HexBug Status")
            .add_field(
                name="Commit",
                value=textwrap.dedent(
                    f"""\
                    [{commit_sha[:7]}]({commit_url}): {commit_message}
                    {_discord_date(commit_timestamp)}"""
                ),
                inline=False,
            )
            .add_field(
                name="Latest deployment",
                value=_discord_date(deploy_timestamp) if deploy_timestamp else "N/A",
                inline=False,
            )
            .add_field(
                name="Latest restart",
                value=_discord_date(restart_timestamp),
                inline=False,
            )
            .add_field(name="Servers", value=f"{len(self.bot.guilds)}")
            .add_field(name="Cogs", value=f"{len(self.bot.cogs)}")
            .add_field(name="Commands", value=f"{len(commands)}")
            .add_field(name="Mods", value=f"{len(MODS)}")
            .add_field(name="Patterns", value=f"{len(self.bot.registry.patterns)}")
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=not show_to_everyone,
            view=build_show_or_delete_button(
                show_to_everyone, interaction, embed=embed
            ),
        )


def _discord_date(timestamp: int | float):
    timestamp = int(timestamp)
    return f"<t:{timestamp}:f> (<t:{timestamp}:R>)"


async def setup(bot: HexBugBot) -> None:
    await bot.add_cog(StatusCog(bot))
