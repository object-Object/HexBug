from __future__ import annotations

import inspect
from typing import Any, Callable, Literal, override

from discord import Client, Interaction
from discord.app_commands import Command, CommandTree, locale_str
from discord.app_commands.commands import Binding, CommandCallback
from discord.app_commands.installs import AppCommandContext, AppInstallationType
from discord.utils import (
    MISSING,
    _shorten,  # pyright: ignore[reportPrivateUsage]
    is_inside_class,
)


async def _default_callback(interaction: Interaction):
    raise NotImplementedError


class EntryPointCommand[GroupT: Binding, **P, T](Command[GroupT, P, T]):
    _handler: Literal[1, 2]

    def __init__(
        self,
        *,
        name: str | locale_str,
        description: str | locale_str,
        callback: CommandCallback[GroupT, P, T] = _default_callback,
        nsfw: bool = False,
        allowed_contexts: AppCommandContext | None = None,
        allowed_installs: AppInstallationType | None = None,
        auto_locale_strings: bool = True,
        extras: dict[Any, Any] = MISSING,
    ):
        super().__init__(
            name=name,
            description=description,
            callback=callback,
            nsfw=nsfw,
            parent=None,
            guild_ids=None,
            allowed_contexts=allowed_contexts,
            allowed_installs=allowed_installs,
            auto_locale_strings=auto_locale_strings,
            extras=extras,
        )

        if callback is _default_callback:
            self._handler = 2  # DISCORD_LAUNCH_ACTIVITY
        else:
            self._handler = 1  # APP_HANDLER

        if self.parameters:
            required_params = is_inside_class(callback) + 1
            raise TypeError(
                f"entry point callback {callback.__qualname__!r} must have exactly {required_params} parameter(s)"
            )

    @override
    def to_dict[ClientT: Client](self, tree: CommandTree[ClientT]) -> dict[str, Any]:
        if self.parent is not None:
            raise TypeError("entry point command must not be a subcommand")

        # https://docs.discord.com/developers/activities/development-guides/user-actions#setting-up-an-entry-point-command
        return {
            **super().to_dict(tree),
            "type": 4,  # PRIMARY_ENTRY_POINT
            "handler": self._handler,
        }


def entry_point_command[GroupT: Binding, **P, T](
    *,
    name: str | locale_str = MISSING,
    description: str | locale_str = MISSING,
    nsfw: bool = False,
    auto_locale_strings: bool = True,
    extras: dict[Any, Any] = MISSING,
) -> Callable[[CommandCallback[GroupT, P, T]], EntryPointCommand[GroupT, P, T]]:
    def decorator(
        func: CommandCallback[GroupT, P, T],
    ) -> EntryPointCommand[GroupT, P, T]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError("command function must be a coroutine function")

        if description is MISSING:
            if func.__doc__ is None:
                desc = "…"
            else:
                desc = _shorten(func.__doc__)
        else:
            desc = description

        return EntryPointCommand(
            name=name if name is not MISSING else func.__name__,
            description=desc,
            callback=func,
            nsfw=nsfw,
            auto_locale_strings=auto_locale_strings,
            extras=extras,
        )

    return decorator
