from datetime import UTC, datetime

from discord import Color, Embed, Interaction
from discord.app_commands import (
    AppCommandError,
    CommandInvokeError,
    CommandTree,
    Transformer,
    TransformerError,
)
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from HexBug.core.exceptions import InvalidInputError, SilentError
from HexBug.utils.discord.embeds import add_fields


class HexBugCommandTree(CommandTree):
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
