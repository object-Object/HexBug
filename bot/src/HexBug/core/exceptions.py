from typing import Any, Self, overload

from discord.app_commands import AppCommandError
from discord.utils import MISSING

from HexBug.utils.discord.embeds import EmbedField


class SilentError(AppCommandError):
    """Base class for exceptions that should be silently caught and ignored."""


class InvalidInputError(AppCommandError):
    """An exception raised within command handlers when an input value is invalid.

    Displays a similar error message as `TransformerError`.
    """

    @overload
    def __init__(self, message: str, *, value: Any) -> None: ...

    @overload
    def __init__(
        self,
        message: str,
        *,
        fields: list[EmbedField],
    ) -> None: ...

    def __init__(
        self,
        message: str,
        *,
        value: Any = MISSING,
        fields: list[EmbedField] = MISSING,
    ):
        self.message: str = message
        self.fields: list[EmbedField] = [] if fields is MISSING else fields

        if value is MISSING:
            super().__init__(message)
        else:
            super().__init__(f"{message} (value: {value})")
            self.add_field(name="Value", value=value, inline=False)

    def add_field(
        self,
        *,
        name: Any,
        value: Any,
        inline: bool = True,
    ) -> Self:
        self.fields.append(EmbedField(name=name, value=value, inline=inline))
        return self
