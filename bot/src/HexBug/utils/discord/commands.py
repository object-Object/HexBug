from contextlib import asynccontextmanager
from typing import Any, Callable

from discord import (
    Interaction,
    InteractionType,
)
from discord.app_commands import Command, ContextMenu
from discord.ext.commands import Paginator

from HexBug.utils.strings import truncate_str

AnyCommand = Command[Any, ..., Any]

AnyInteractionCommand = AnyCommand | ContextMenu | None


def get_command(interaction: Interaction) -> AnyCommand | None:
    match interaction.command:
        case Command() as command:
            if interaction.type == InteractionType.application_command:
                return command
        case _:
            pass


def print_command(
    interaction: Interaction,
    command: AnyCommand,
    truncate: bool = True,
) -> str:
    limit = 100 if truncate else None
    args = " ".join(
        f"{name}: {truncate_str(str(value), limit, message=' ... (truncated)')}"
        for name, value in interaction.namespace
    )
    return f"/{command.qualified_name} {args}"


@asynccontextmanager
async def paginate(
    page_consumer: Callable[[str], Any],
    paginator: Paginator = Paginator(),
):
    yield paginator
    for page in paginator.pages:
        await page_consumer(page)
    paginator.clear()
