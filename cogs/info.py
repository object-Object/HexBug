from enum import Enum
from typing import TypedDict

import discord
from discord import app_commands
from discord.ext import commands

from utils.buttons import build_show_or_delete_button
from utils.commands import HexBugBot


class InfoMessage(TypedDict, total=False):
    content: str
    embed: discord.Embed


class InfoMessages(Enum):
    addons = InfoMessage(
        embed=discord.Embed(
            title="Hex-related addons, mods, and tools",
            description="https://hexxy.media/addons",
        )
    )

    bug_report = InfoMessage(
        embed=discord.Embed(
            description="""Please do not post your bug reports to Discord. Instead, post them to the issue tracker on the mod's GitHub.

Hex Casting: https://github.com/gamma-delta/HexMod/issues
PAUCAL: https://github.com/gamma-delta/PAUCAL/issues""",
        ),
    )

    crashlog = InfoMessage(
        embed=discord.Embed(
            description="""You can use a service like [Pastebin](https://pastebin.com) to post the crashlog.
Do ***NOT*** upload it directly to Discord in a message or file."""
        ).set_image(url="https://cdn.discordapp.com/attachments/326397739074060288/976135876046356560/image0-4-2.gif"),
    )

    forum = InfoMessage(
        embed=discord.Embed(
            title="petrak@'s mods forum",
            url="https://forum.petra-k.at/index.php",
            description="""[Join the forum](https://forum.petra-k.at/ucp.php?mode=register) to post/browse cool hexes, ask for help, or chat about petrak@'s mods.

**Quick links**
[General Chat](https://forum.petra-k.at/viewforum.php?f=7)
[Akashic Records](https://forum.petra-k.at/viewforum.php?f=2)
[Hexcasting Help](https://forum.petra-k.at/viewforum.php?f=5)
[Miner's Lung](https://forum.petra-k.at/viewforum.php?f=9)
[Bliss Mods](https://forum.petra-k.at/viewforum.php?f=10)""",
        )
    )

    gemini_skill_issue = InfoMessage(content="https://twitter.com/_Kinomoru/status/1550127535404359684")

    git_log = InfoMessage(content="https://xkcd.com/1296/")

    pk = InfoMessage(
        embed=discord.Embed(
            description="""**What are all the `[BOT]` messages doing?**
This is the result of PluralKit, a discord bot for plural people. Plurality is the experience of having more than one mind in one body.

PluralKit info: https://pluralkit.me/
More info on plurality: https://morethanone.info/""",
        ),
    )

    tools = InfoMessage(
        embed=discord.Embed(
            title="Hex-related addons, mods, and tools",
            description="https://hexxy.media/addons#tools",
        )
    )

    @property
    def value(self) -> InfoMessage:
        # for the type hints
        return super().value


class InfoCog(commands.Cog):
    def __init__(self, bot: HexBugBot) -> None:
        self.bot = bot

    @app_commands.command()
    @app_commands.describe(
        info="The name of the info message to show",
        show_to_everyone="Whether the result should be visible to everyone, or just you (to avoid spamming)",
    )
    @app_commands.rename(info="name")
    async def info(self, interaction: discord.Interaction, info: InfoMessages, show_to_everyone: bool = False):
        """Show a premade info message"""
        await interaction.response.send_message(
            **info.value,
            ephemeral=not show_to_everyone,
            view=build_show_or_delete_button(show_to_everyone, interaction, **info.value),
        )


# TODO: remove this in a while when people are used to the new command
class TagCog(commands.Cog):
    @app_commands.command()
    async def tag(self, interaction: discord.Interaction):
        """This command has been renamed to /info."""
        await interaction.response.send_message("This command has been renamed to `/info`.", ephemeral=True)


async def setup(bot: HexBugBot) -> None:
    await bot.add_cog(InfoCog(bot))
    await bot.add_cog(TagCog())
