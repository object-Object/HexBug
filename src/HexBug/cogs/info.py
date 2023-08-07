import json
from collections import defaultdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TypedDict

import discord
from attr import dataclass
from discord import app_commands
from discord.ext import commands
from discord.utils import MISSING

from ..utils.buttons import MessageProps, build_show_or_delete_button
from ..utils.commands import HexBugBot

_DATA_PATH = Path(__file__).parent / "info_counts.json"


@dataclass(kw_only=True)
class CountedMessageProps:
    content: str = MISSING
    embed: discord.Embed

    def message_without_footer(self) -> MessageProps:
        return {
            "content": self.content,
            "embed": self.embed.set_footer(),
        }

    def message_and_increment(self, name: str) -> MessageProps:
        return {
            "content": self.content,
            "embed": self.embed.set_footer(text=self._footer_and_increment(name)),
        }

    def _footer_and_increment(self, name: str) -> str:
        # load data
        if _DATA_PATH.exists():
            raw_data = json.loads(_DATA_PATH.read_text("utf-8"))
            assert isinstance(raw_data, dict), str(raw_data)
        else:
            raw_data = {}
        data: defaultdict[str, tuple[int, float | None]] = defaultdict(lambda: (0, None), raw_data)

        # increment
        prev_count, prev_time = data[name]
        count = prev_count + 1

        # write
        now = datetime.now()
        data[name] = (count, now.timestamp())
        _DATA_PATH.write_text(json.dumps(data), "utf-8")

        # footer
        footer = f"Times posted: {count}"
        if prev_time is not None:
            then = datetime.fromtimestamp(prev_time)
            print(now, then)
            footer += f"  ·  Days since last post: {(now - then).days}"
        return footer


class InfoMessages(Enum):
    addons = MessageProps(
        embed=discord.Embed(
            title="Hex-related addons, mods, and tools",
            description="https://hexxy.media/addons",
        )
    )

    bug_report = MessageProps(
        embed=discord.Embed(
            description="""Please do not post your bug reports to Discord. Instead, post them to the issue tracker on the mod's GitHub.

Hex Casting: https://github.com/gamma-delta/HexMod/issues
PAUCAL: https://github.com/gamma-delta/PAUCAL/issues""",
        ),
    )

    crashlog = MessageProps(
        embed=discord.Embed(
            description="""You can use a service like [mclo.gs](https://mclo.gs) or [Pastebin](https://pastebin.com) to post the crashlog.
Do ***NOT*** upload it directly to Discord in a message or file."""
        ).set_image(url="https://hexxy.media/hexxy_media/i_will_not_give_crashlog.jpg"),
    )

    forum = MessageProps(
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

    gemini_skill_issue = MessageProps(content="https://vxtwitter.com/_Kinomoru/status/1550127535404359684")

    git_log = MessageProps(content="https://xkcd.com/1296/")

    pk = CountedMessageProps(
        embed=discord.Embed(
            description="""**What are all the `[BOT]` messages doing?**
This is the result of PluralKit, a discord bot for plural people. Plurality is the experience of having more than one mind in one body.

PluralKit info: https://pluralkit.me/
More info on plurality: https://morethanone.info/""",
        ).set_thumbnail(url="https://hexxy.media/hexxy_media/why_is_the_bot_talking.png"),
    )

    tools = MessageProps(
        embed=discord.Embed(
            title="Hex-related addons, mods, and tools",
            description="https://hexxy.media/addons#tools",
        )
    )

    def message(self, show_to_everyone: bool) -> MessageProps:
        value = self.value
        match value:
            case dict():
                return value
            case CountedMessageProps():
                if show_to_everyone:
                    return value.message_and_increment(self.name)
                else:
                    return value.message_without_footer()
            case _:
                raise TypeError(value)


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
        message = info.message(show_to_everyone)
        await interaction.response.send_message(
            **message,
            ephemeral=not show_to_everyone,
            view=build_show_or_delete_button(show_to_everyone, interaction, builder=lambda show: info.message(show)),
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
