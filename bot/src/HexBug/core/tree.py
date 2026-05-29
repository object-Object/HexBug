from datetime import UTC, datetime
from typing import override

from discord import Color, Embed, Interaction
from discord.app_commands import (
    AppCommandError,
    CommandInvokeError,
    CommandTree,
    Transformer,
    TransformerError,
)
from discord.app_commands.installs import AppCommandContext, AppInstallationType
from discord.client import Client
from discord.utils import MISSING
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from HexBug.core.exceptions import InvalidInputError, SilentError
from HexBug.utils.discord.embeds import add_fields
from HexBug.utils.metrics import COMMAND_RUNTIME_HISTOGRAM


class HexBugCommandTree(CommandTree):
    _command_start_times: dict[int, datetime]
    _next_command_key: int

    def __init__(
        self,
        client: Client,
        *,
        fallback_to_global: bool = True,
        allowed_contexts: AppCommandContext = MISSING,
        allowed_installs: AppInstallationType = MISSING,
    ):
        super().__init__(
            client,
            fallback_to_global=fallback_to_global,
            allowed_contexts=allowed_contexts,
            allowed_installs=allowed_installs,
        )
        self._command_start_times = {}
        self._next_command_key = 0

    @property
    def num_active_commands(self):
        return len(self._command_start_times)

    def get_longest_active_command_runtime(self):
        now = datetime.now()
        return max(
            (
                (now - start).total_seconds()
                for start in self._command_start_times.values()
            ),
            default=None,
        )

    @override
    async def _call(self, interaction: Interaction) -> None:
        # map PRIMARY_ENTRY_POINT to CHAT_INPUT to make discord.py handle it
        if interaction.data and interaction.data.get("type") == 4:
            # lie
            interaction.data["type"] = 1  # pyright: ignore[reportGeneralTypeIssues]

        start = datetime.now()
        key = self._next_command_key
        self._next_command_key += 1
        try:
            self._command_start_times[key] = start
            await super()._call(interaction)
        finally:
            del self._command_start_times[key]
            COMMAND_RUNTIME_HISTOGRAM.observe((datetime.now() - start).total_seconds())

    @override
    async def on_error(self, interaction: Interaction, error: AppCommandError):
        if isinstance(error, SilentError):
            return

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
            case InvalidInputError(message=message, fields=fields):
                embed.title = "Invalid input!"
                embed.description = message
                add_fields(embed, *fields)
            case CommandInvokeError(command=command, original=original):
                # don't print the error message twice
                await super().on_error(interaction, error)
                embed.title = "Command failed!"
                embed.description = f"Command {command.name!r} raised an exception: {original.__class__.__name__}"
            case _:
                await super().on_error(interaction, error)
                embed.title = "Command failed!"
                embed.description = str(error)

        if cause := error.__cause__:
            match cause:
                case SQLAlchemyError():
                    # don't show the full SQL statement
                    reason = f"```\n{cause.args[0]}\n```"
                case ValidationError():
                    reason = f"```\n{cause}\n```"
                case _:
                    reason = str(cause)

            embed.add_field(
                name="Reason",
                value=reason,
                inline=False,
            )

        footer = error.__class__.__name__
        if (
            (context := error.__cause__)
            or (context := error.__context__)
            and not error.__suppress_context__
        ):
            footer += f" ({context.__class__.__name__})"
        embed.set_footer(text=footer)

        await interaction.response.send_message(embed=embed, ephemeral=True)
