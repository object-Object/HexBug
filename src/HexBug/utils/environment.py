import os
from enum import Enum

from discord.ext import commands

from .commands import HexBugBot


class Environment(Enum):
    PROD = 0
    DEV = 1

    def check(self):
        """Asserts that the current execution environment is the same as this one."""

        def predicate(ctx: commands.Context[HexBugBot]):
            return get_environment() is self

        return commands.check(predicate)


def get_environment():
    match os.getenv("ENVIRONMENT", "").lower():
        case "prod":
            return Environment.PROD
        case "dev":
            return Environment.DEV
        case _:
            return None
