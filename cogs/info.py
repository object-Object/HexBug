from dataclasses import dataclass
from enum import Enum
from itertools import chain
from typing import Self, TypedDict

import discord
from discord import app_commands
from discord.ext import commands
from pyparsing import Iterable

from utils.buttons import build_show_or_delete_button
from utils.commands import HexBugBot
from utils.mods import FABRIC, FORGE, QUILT, APIMod, Mod, RegistryMod


@dataclass(kw_only=True)
class AddonEntry:
    """Information about a Hex-related mod or addon"""

    name: str
    description: str
    curseforge_url: str | None
    modrinth_url: str | None
    book_url: str | None
    source_url: str | None
    modloaders: list[str]

    @classmethod
    def from_mod(cls, mod: Mod) -> Self:
        mod_info = mod.value
        return AddonEntry(
            name=mod_info.name,
            description=mod_info.description,
            curseforge_url=mod_info.curseforge_url,
            modrinth_url=mod_info.modrinth_url,
            book_url=mod_info.book_url,
            source_url=mod_info.source_url,
            modloaders=mod_info.modloaders,
        )

    def url_line(self) -> str:
        urls: list[tuple[str, str | None]] = [
            ("CurseForge", self.curseforge_url),
            ("Modrinth", self.modrinth_url),
            ("Web Book", self.book_url),
            ("Source", self.source_url),
        ]
        return " | ".join(f"[{name}]({url})" for name, url in urls if url)

    def display(self) -> str:
        return f"**{self.name}**  {' '.join(self.modloaders)}\n{self.url_line()}\n{self.description}"


# TODO: make the AddonEntry stuff less ugly. i don't like any of this, but it works, and it matches the style of everything else here

# this SHOULD work fine with API mods because cogs aren't loaded until after the registry is built
# unless something else imports from this file
# so let's not do that

ADDONS: list[AddonEntry] = [
    AddonEntry.from_mod(mod) for mod in chain(RegistryMod, APIMod) if mod != RegistryMod.HexCasting
]

HEX_INTEROP: list[AddonEntry] = [
    AddonEntry(
        name="Gravity Changer / Gravity API",
        description="Adds [patterns](https://gamma-delta.github.io/HexMod/#interop/gravity) that allow changing an entity's gravity direction (eg. walking on walls).",
        curseforge_url="https://www.curseforge.com/minecraft/mc-mods/gravityapi",
        modrinth_url="https://modrinth.com/mod/gravity-api",
        book_url=None,
        source_url="https://github.com/Fusion-Flux/Gravity-Api",
        modloaders=[FABRIC, QUILT],
    ),
    AddonEntry(
        name="Pehkui",
        description="Adds [patterns](https://gamma-delta.github.io/HexMod/#interop/pehkui) that allow changing the size of entities.",
        curseforge_url="https://www.curseforge.com/minecraft/mc-mods/pehkui",
        modrinth_url="https://modrinth.com/mod/pehkui",
        book_url=None,
        source_url="https://github.com/Virtuoel/Pehkui",
        modloaders=[FORGE, FABRIC, QUILT],
    ),
    AddonEntry(
        name="Create",
        description="Adds the ability to use crushing wheels to turn amethyst blocks into shards and dust.",
        curseforge_url="https://www.curseforge.com/minecraft/mc-mods/create",
        modrinth_url="https://modrinth.com/mod/create",
        book_url=None,
        source_url="https://github.com/Creators-of-Create/Create",
        modloaders=[FORGE, FABRIC, QUILT],
    ),
    AddonEntry(
        name="Farmer's Delight",
        description="Adds the ability to use the cutting board to break down edified wood items, as well as drastically improving the Pansexual Pigment recipe. Also useful for turning amethyst blocks into shards.",
        curseforge_url="https://www.curseforge.com/minecraft/mc-mods/farmers-delight",
        modrinth_url="https://modrinth.com/mod/farmers-delight",
        book_url=None,
        source_url="https://github.com/vectorwing/FarmersDelight",
        modloaders=[FORGE, FABRIC],
    ),
]

OTHER_INTEROP: list[AddonEntry] = [
    AddonEntry(
        name="Ars Scalaes",
        description="Provides compatibility with Ars Nouveau: adds an Archwood Staff (crafted with a source gem, not charged amethyst) and the ability to use source gems and blocks as media.",
        curseforge_url="https://www.curseforge.com/minecraft/mc-mods/ars-scalaes",
        modrinth_url=None,
        book_url=None,
        source_url="https://github.com/Alexthw46/Ars-Scalaes",
        modloaders=[FORGE],
    ),
    AddonEntry(
        name="Ducky Peripherals",
        description="Adds the [Focal Port](https://github.com/SamsTheNerd/ducky-periphs/wiki/Focal-Port), which allows direct data transfer between Hex Casting and ComputerCraft.",
        curseforge_url="https://www.curseforge.com/minecraft/mc-mods/ducky-periphs",
        modrinth_url="https://modrinth.com/mod/ducky-periphs",
        book_url=None,
        source_url="https://github.com/SamsTheNerd/ducky-periphs",
        modloaders=[FABRIC],
    ),
    AddonEntry(
        name="Switchy",
        description="Adds the ability to change your pigment when switching presets.",
        curseforge_url=None,
        modrinth_url="https://modrinth.com/mod/switchy",
        book_url=None,
        source_url="https://github.com/sisby-folk/switchy",
        modloaders=[QUILT],
    ),
]


def _join_entries(entries: Iterable[AddonEntry]) -> str:
    return "\n\n".join(entry.display() for entry in entries)


class InfoMessage(TypedDict, total=False):
    content: str
    embed: discord.Embed


class InfoMessages(Enum):
    addons = InfoMessage(
        embed=discord.Embed(
            title="Addons for Hex",
            description=_join_entries(ADDONS),
        ).set_footer(text="See also: addons_interop, addons_other")
    )

    addons_interop = InfoMessage(
        embed=discord.Embed(
            title="Mods with Hex-provided interop",
            description=_join_entries(HEX_INTEROP),
        ).set_footer(text="See also: addons, addons_other")
    )

    addons_other = InfoMessage(
        embed=discord.Embed(
            title="Other mods that interact with Hex",
            description=_join_entries(OTHER_INTEROP),
        ).set_footer(text="See also: addons, addons_interop")
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
            title="Hex-related tools and programs",
            description="""**[HexBug](https://github.com/object-Object/HexBug):** This bot! If you're doing something Hex-related in Python, this has a lot of useful classes and methods that you can (and probably should) use.
**[hexdecode](https://github.com/gchpaco/hexdecode):** CLI tool for decoding pattern lists. HexBug's core functionality is based on this. Mostly superseded by HexBug (use `/decode`).
**[hex-interpreter](https://github.com/Robotgiggle/hex-interpreter):** CLI tool for parsing and displaying patterns. A modified version of its rendering code is used in HexBug.
**[Hex-Casting-Generator](https://github.com/DaComputerNerd717/Hex-Casting-Generator):** Very useful GUI tool for generating and displaying number literals.
**[hexnumgen](https://github.com/object-Object/hexnumgen-rs):** Hex-Casting-Generator's number generation functionality, ported to Rust. Contains a CLI tool for generating number literals, and can also be used as a Rust library or a Python package. Used in HexBug.
**[hexpiler](https://github.com/pandaxtc/hexpiler):** Proof-of-concept DSL for Hex Casting.
**[vscode-hex-casting](https://github.com/object-Object/vscode-hex-casting):** VSCode language features to make writing hexes easier, including highlighting, autocomplete, hover text, macro support, and more.
**[Hex Studio](https://master-bw3.github.io/Hex-Studio/):** WIP visual editor and stack simulator for writing hexes in a similar manner to using the actual mod.""",
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
