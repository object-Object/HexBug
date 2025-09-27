import textwrap
from datetime import datetime

from discord import Color, Embed, Interaction, app_commands

from HexBug.common.__version__ import VERSION
from HexBug.core.cog import HexBugCog
from HexBug.utils.discord.translation import translate_command_text
from HexBug.utils.discord.visibility import (
    Visibility,
    VisibilityOption,
    respond_with_visibility,
)


class StatusCog(HexBugCog):
    @app_commands.command()
    async def status(
        self,
        interaction: Interaction,
        visibility: VisibilityOption = Visibility.PRIVATE,
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
            commit_info = await translate_command_text(interaction, "commit-unknown")
            deployment_time_info = await translate_command_text(
                interaction, "deployment-time-unknown"
            )

        app_info = await self.bot.application_info()
        registry = self.bot.registry

        embed = (
            Embed(
                title=await translate_command_text(interaction, "title"),
                color=color,
            )
            .set_footer(text=f"v{VERSION}")
            .add_field(
                name=await translate_command_text(interaction, "commit"),
                value=commit_info,
                inline=False,
            )
            .add_field(
                name=await translate_command_text(interaction, "deployment-time"),
                value=deployment_time_info,
                inline=False,
            )
            .add_field(
                name=await translate_command_text(interaction, "uptime"),
                value=_discord_date(self.bot.start_time),
                inline=False,
            )
            .add_field(
                name=await translate_command_text(interaction, "installs"),
                value=await translate_command_text(
                    interaction,
                    "installs-value",
                    servers=app_info.approximate_guild_count,
                    users=app_info.approximate_user_install_count or 0,
                ),
            )
            .add_field(
                name=await translate_command_text(interaction, "mods"),
                value=len(registry.mods),
            )
            .add_field(
                name=await translate_command_text(interaction, "patterns"),
                value=len(registry.patterns)  # includes hidden
                + len(registry.special_handlers),
            )
            .add_field(
                name=await translate_command_text(interaction, "categories"),
                value=len(registry.categories),
            )
            .add_field(
                name=await translate_command_text(interaction, "entries"),
                value=len(registry.entries),
            )
            .add_field(
                name=await translate_command_text(interaction, "pages"),
                value=len(registry.pages),
            )
            .add_field(
                name=await translate_command_text(interaction, "recipes"),
                value=sum(len(recipes) for recipes in registry.recipes.values()),
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
