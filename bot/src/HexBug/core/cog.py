import logging
import sys
from dataclasses import dataclass
from typing import Any, Self, cast

from discord.app_commands import Group
from discord.ext.commands import Cog, CogMeta, GroupCog

from .bot import HexBugBot

logger = logging.getLogger(__name__)


class HexBugCogMeta(CogMeta):
    def __new__(cls, *args: Any, **kwargs: Any) -> CogMeta:
        if "name" not in kwargs:
            name = cast(str, args[0]).removesuffix("Cog")
            if name:
                kwargs["name"] = name
        return super().__new__(cls, *args, **kwargs)


@dataclass(eq=False)
class HexBugCog(Cog, metaclass=HexBugCogMeta):
    """Base class for HexBug cogs.

    When subclasses are defined, a `setup` function (`cls.setup`) is added to the module
    of the subclass. This can be disabled by adding `setup=False` to the class kwargs.
    """

    bot: HexBugBot

    def __init_subclass__(cls, setup: bool = True, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if setup:
            module = sys.modules[cls.__module__]
            if not hasattr(module, "setup"):
                setattr(module, "setup", cls.setup)
            else:
                logger.debug(
                    f"Not adding setup function for {cls} to {cls.__module__},"
                    + f" attribute already exists: {getattr(module, 'setup', None)}"
                )

    @classmethod
    async def setup(cls, bot: HexBugBot):
        await bot.add_cog(cls._create_cog(bot))

    @classmethod
    def _create_cog(cls, bot: HexBugBot) -> Self:
        """Factory method called by `setup` when adding this cog to the bot."""
        return cls(bot)

    @property
    def env(self):
        return self.bot.env

    async def cog_load(self):
        if isinstance(self, GroupCog):
            assert self.app_command
            for child in self.__class__.__dict__.values():
                if isinstance(child, type) and issubclass(child, SubGroup):
                    self.app_command.add_command(child(bot=self.bot))

    # required to make the help command not fail
    def __hash__(self) -> int:
        return hash(self.__class__)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, HexBugCog):
            return self.__class__ == other.__class__
        return super().__eq__(other)


@dataclass
class SubGroup(Group):
    """Base class for subcommand groups.

    Automatically added as a subcommand if created as an inner class of a class that
    inherits from both `HexBugCog` and `GroupCog`.
    """

    bot: HexBugBot

    def __post_init__(self):
        super().__init__()
