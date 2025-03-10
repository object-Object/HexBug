from typing import Any

from discord.app_commands import AppCommandError
from hexdoc.core import ResourceLocation


class SilentError(AppCommandError):
    """Base class for exceptions that should be silently caught and ignored."""


class InvalidInputError(AppCommandError):
    """An exception raised within command handlers when an input value is invalid.

    Displays a similar error message as `TransformerError`.
    """

    def __init__(self, value: Any, message: str):
        self.value = value
        self.message = message
        super().__init__(f"{message} (value: {value})")


class DuplicatePatternError(ValueError):
    def __init__(self, field: str, value: Any, *pattern_ids: ResourceLocation):
        ids = ", ".join(str(pattern_id) for pattern_id in pattern_ids)
        super().__init__(f"Multiple patterns found with same {field} ({value}): {ids}")
