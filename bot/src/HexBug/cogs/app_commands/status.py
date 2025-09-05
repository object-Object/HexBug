import textwrap
from datetime import datetime

from discord import Color, Embed, Interaction, app_commands

from HexBug.common.__version__ import VERSION
from HexBug.core.cog import HexBugCog
from HexBug.core.translator import translate_text
from HexBug.utils.discord.visibility import MessageVisibility, respond_with_visibility


class StatusCog(HexBugCog):
    @app_commands.command()
    async def status(
        self,
        interaction: Interaction,
        visibility: MessageVisibility = "private",
    ):
        if info := self.env.deployment:
            color = Color.green()
            commit_url = (
                f"https://github.com/object-Object/HexBug/commit/{info.commit_sha}"
            )
            commit_info = textwrap.dedent(
                f"""\
                    [{info.short_commit_sha}]({commit_url}): {info.commit_message}
                    {_discord_date(info.commit_timestamp)}"""
            )
            deployment_time_info = _discord_date(info.timestamp)
        else:
            color = Color.orange()
            commit_info = await translate_text(interaction, "commit-unknown")
            deployment_time_info = await translate_text(
                interaction, "deployment-time-unknown"
            )

        app_info = await self.bot.application_info()

        embed = (
            Embed(
                title=await translate_text(interaction, "title"),
                color=color,
            )
            .set_footer(text=f"v{VERSION}")
            .add_field(
                name=await translate_text(interaction, "commit"),
                value=commit_info,
                inline=False,
            )
            .add_field(
                name=await translate_text(interaction, "deployment-time"),
                value=deployment_time_info,
                inline=False,
            )
            .add_field(
                name=await translate_text(interaction, "uptime"),
                value=_discord_date(self.bot.start_time),
                inline=False,
            )
            .add_field(
                name=await translate_text(interaction, "installs"),
                value=await translate_text(
                    interaction,
                    "installs-value",
                    servers=app_info.approximate_guild_count,
                    users=app_info.approximate_user_install_count,
                ),
            )
            .add_field(
                name=await translate_text(interaction, "mods"),
                value=len(self.bot.registry.mods),
            )
            .add_field(
                name=await translate_text(interaction, "patterns"),
                value=len(self.bot.registry.patterns)  # includes hidden
                + len(self.bot.registry.special_handlers),
            )
        )

        await respond_with_visibility(interaction, visibility, embed=embed)


def _discord_date(timestamp: int | float | datetime):
    match timestamp:
        case int():
            pass
        case float():
            timestamp = int(timestamp)
        case datetime():
            timestamp = int(timestamp.timestamp())
    return f"<t:{timestamp}:f> (<t:{timestamp}:R>)"
