# pyright: reportPrivateUsage=none

from collections import defaultdict
from datetime import UTC, datetime

from aiohttp import ClientSession
from discord import Color, Embed, Interaction, Webhook, app_commands
from discord.app_commands import (
    AppCommandContext,
    AppCommandError,
    AppInstallationType,
    CommandTree,
    Transformer,
    TransformerError,
)
from discord.ext import commands

from ..hexdecode.registry import Registry


def build_autocomplete(
    initial_choices: list[tuple[app_commands.Choice, list[str]]],
) -> dict[str, list[app_commands.Choice]]:
    autocomplete: defaultdict[str, set[app_commands.Choice]] = defaultdict(set)
    for choice, other_names in initial_choices:
        for name in other_names + [choice.name]:
            name = name.lower()
            for i in range(len(name)):
                for j in range(i, len(name)):
                    autocomplete[name[i : j + 1]].add(choice)
        autocomplete[""].add(choice)

    return {
        key: sorted(list(value), key=lambda c: c.name)
        for key, value in autocomplete.items()
    }


class HexBugCommandTree(CommandTree):
    async def on_error(self, interaction: Interaction, error: AppCommandError):
        if interaction.response.is_done():
            await super().on_error(interaction, error)
            return

        embed = Embed(
            color=Color.red(),
            timestamp=datetime.now(UTC),
        )

        match error:
            case TransformerError(
                value=value,
                type=opt_type,
                transformer=Transformer(_error_display_name=transformer_name),
            ):
                embed.title = "Invalid input!"
                embed.description = f"Failed to convert value from `{opt_type.name}` to `{transformer_name}`."
                embed.add_field(
                    name="Value",
                    value=str(value),
                    inline=False,
                )
            case _:
                await super().on_error(interaction, error)
                embed.title = "Command failed!"
                embed.description = str(error)

        if cause := error.__cause__:
            embed.add_field(
                name="Reason",
                value=str(cause),
                inline=False,
            ).set_footer(
                text=f"{error.__class__.__name__} ({cause.__class__.__name__})",
            )
        else:
            embed.set_footer(
                text=error.__class__.__name__,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)


class HexBugBot(commands.Bot):
    def __init__(
        self,
        registry: Registry,
        session: ClientSession,
        log_webhook_url: str,
        health_check_channel_id: int,
        **kwargs,
    ) -> None:
        super().__init__(
            tree_cls=HexBugCommandTree,
            allowed_installs=AppInstallationType(guild=True, user=True),
            allowed_contexts=AppCommandContext(
                guild=True, dm_channel=True, private_channel=True
            ),
            **kwargs,
        )
        self.registry = registry
        self.session = session
        self.log_webhook = Webhook.from_url(log_webhook_url, session=session)
        self.health_check_channel_id = health_check_channel_id
        self.start_time = datetime.fromtimestamp(0)  # updated in start event
