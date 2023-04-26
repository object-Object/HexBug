from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import InitVar, dataclass, field
from enum import Enum
from itertools import chain
from typing import Iterable

import discord
from discord import app_commands

from Hexal.doc.collate_data import parse_book as hexal_parse_book
from Hexal.doc.collate_data import pattern_stubs as hexal_stubs
from HexMod.doc.collate_data import parse_book as hex_parse_book
from HexMod.doc.collate_data import pattern_stubs as hex_stubs
from HexTweaks.doc.collate_data import parse_book as hextweaks_parse_book
from HexTweaks.doc.collate_data import pattern_stubs as hextweaks_stubs
from MoreIotas.doc.collate_data import parse_book as moreiotas_parse_book
from MoreIotas.doc.collate_data import pattern_stubs as moreiotas_stubs
from utils.api import API
from utils.book_types import Book
from utils.git import get_commit_message, get_commit_tags, get_current_commit, get_latest_tags
from utils.urls import wrap_url

# modloader emotes
# this isn't an enum because it looks ugly as an enum, and for no other reason
FABRIC = "<:_:1089636969618882700>"
FORGE = "<:_:1089636157505142976>"
QUILT = "<:_:1089636999142576241>"


class NotInitializedError(Exception):
    """Attribute that hasn't been initialized yet."""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


@dataclass(kw_only=True)
class _BaseModInfo(ABC):
    name: str
    description: str
    source_url: str = field(init=False)
    book_url: str | None = field(init=False)
    commit: str = field(init=False)
    version: str = field(init=False)
    curseforge_url: str | None
    modrinth_url: str | None
    icon_url: str | None
    modloaders: list[str]

    def build_source_tree_url(self, path: str) -> str:
        return f"{self.source_url}tree/{self.commit}/{path}"

    def build_source_blob_url(self, path: str) -> str:
        return f"{self.source_url}blob/{self.commit}/{path}"

    def build_book_url(self, url: str, show_spoilers: bool, escape: bool) -> str:
        book_url = f"{self.book_url}{'?nospoiler' if show_spoilers else ''}{url}"
        return wrap_url(book_url, show_spoilers, escape)

    @property
    def mod_url(self) -> str | None:
        return self.curseforge_url or self.modrinth_url


@dataclass(kw_only=True)
class _BaseRegistryModInfo(_BaseModInfo, ABC):
    source_url: str
    book_url: str | None
    directory: str
    book: Book
    registry_regex: re.Pattern[str]
    version_regex: re.Pattern[str]
    pattern_files: list[str]
    operator_directories: list[str]
    extra_classname_paths: dict[str, str] = field(default_factory=dict)
    # iterable instead of list because invariance etc
    # see https://github.com/microsoft/pylance-release/discussions/3383
    pattern_stubs: Iterable[tuple[str | None, str]]

    def __post_init__(self):
        self.commit = get_current_commit(self.directory)
        self.version = self._get_version()
        self.pattern_files = [f"{self.directory}/{s}" for s in self.pattern_files]
        self.operator_directories = [f"{self.directory}/{s}" for s in self.operator_directories]

    @abstractmethod
    def _get_version(self) -> str:
        raise NotImplementedError


@dataclass(kw_only=True)
class HexCastingRegistryModInfo(_BaseRegistryModInfo):
    # thanks Alwinfy for (unknowingly) making my registry regex about 5x simpler
    registry_regex: re.Pattern[str] = re.compile(
        r'HexPattern\.fromAngles\("([qweasd]+)", HexDir\.(\w+)\),\s*modLoc\("([^"]+)"\)[^;]+?(makeConstantOp|Op\w+)([^;]*true\);)?',
        re.M,
    )
    version_regex: re.Pattern[str] = re.compile(r"\[Release\].*?([\d\.]+)")

    def _get_version(self) -> str:
        # get version from the current commit message
        version = self.version_regex.match(get_commit_message(self.directory, self.commit))
        assert version is not None
        return version.group(1)


@dataclass(kw_only=True)
class _BaseTagVersionRegistryModInfo(_BaseRegistryModInfo):
    def _get_version(self) -> str:
        # get version from git tags - return first versiony-looking tag we find that isn't a beta/prerelease
        # prefer tags for the current commit if available, otherwise check most recent tags first
        tags = get_commit_tags(self.directory, self.commit) + get_latest_tags(self.directory)
        return next(filter(lambda t: self.version_regex.fullmatch(t), tags))


@dataclass(kw_only=True)
class HexalRegistryModInfo(_BaseTagVersionRegistryModInfo):
    registry_regex: re.Pattern[str] = re.compile(
        r'HexPattern\.fromAngles\("([qweasd]+)", HexDir\.(\w+)\),\s*modLoc\("([^"]+)"\)[^val]+?(makeConstantOp|Op\w+)(?:[^val]*[^\(](true)\))?',
        re.M,
    )
    version_regex: re.Pattern[str] = re.compile(r"^\d+\.\d+\.\d+$")


@dataclass(kw_only=True)
class HexTweaksRegistryModInfo(_BaseTagVersionRegistryModInfo):
    registry_regex: re.Pattern[str] = re.compile(
        r'PatternRegistry.mapPattern\([\n ]+HexPattern\.fromAngles\("([qweasd]+)", ?HexDir\.(.+)?\)[,\n ]+?new ResourceLocation\(".+"(.+)?"\),\n.+new (.+)\(.+, ?(true)?'
    )
    version_regex: re.Pattern[str] = re.compile(r"^v\d+.\d+.\d+$")


@dataclass(kw_only=True)
class _BaseAPIModInfo(_BaseModInfo, ABC):
    api_base_url: InitVar[str]
    version: str
    """No trailing slash"""

    def __post_init__(self, api_base_url: str):
        self.api = API(api_base_url, self.version)
        self._source_url: str | None = None
        self._book_url: str | None = None
        self._commit: str | None = None

    @abstractmethod
    def __late_init__(self, source_url: str, book_url: str | None, commit: str):
        """Initializes attributes that need to be fetched from the API."""
        self._source_url = source_url
        self._book_url = book_url
        self._commit = commit

    @property
    @abstractmethod
    def book_url(self) -> str | None:
        raise NotImplementedError

    @property
    def source_url(self) -> str:
        if self._source_url is None:
            raise NotInitializedError(self)
        return self._source_url

    @property
    def commit(self) -> str:
        if self._commit is None:
            raise NotInitializedError(self)
        return self._commit


class APIWithBookModInfo(_BaseAPIModInfo):
    def __late_init__(self, source_url: str, book_url: str, commit: str):
        return super().__late_init__(source_url, book_url, commit)

    @property
    def book_url(self) -> str:
        if self._book_url is None:
            raise NotInitializedError(self)
        return self._book_url


class APIWithoutBookModInfo(_BaseAPIModInfo):
    def __late_init__(self, source_url: str, commit: str):
        return super().__late_init__(source_url, None, commit)

    @property
    def book_url(self) -> None:
        return None

    def build_book_url(self, url: str, show_spoilers: bool, escape: bool) -> str:
        raise NotImplementedError


RegistryModInfo = HexCastingRegistryModInfo | HexalRegistryModInfo | HexTweaksRegistryModInfo
APIModInfo = APIWithBookModInfo | APIWithoutBookModInfo


class RegistryMod(Enum):
    # HEX NEEDS TO BE FIRST
    HexCasting = HexCastingRegistryModInfo(
        name="Hex Casting",
        description="A mod for Forge and Fabric adding stack-based programmable spellcasting, inspired by Psi. (Why are you using this bot if you don't know what Hex is?)",
        directory="HexMod",
        book=hex_parse_book("HexMod/Common/src/main/resources", "hexcasting", "thehexbook"),
        book_url="https://gamma-delta.github.io/HexMod/",
        curseforge_url="https://www.curseforge.com/minecraft/mc-mods/hexcasting/",
        modrinth_url="https://modrinth.com/mod/hex-casting/",
        source_url="https://github.com/gamma-delta/HexMod/",
        icon_url="https://media.forgecdn.net/avatars/thumbnails/535/944/64/64/637857298951404372.png",
        pattern_files=[
            "Common/src/main/java/at/petrak/hexcasting/common/casting/RegisterPatterns.java",
            "Common/src/main/java/at/petrak/hexcasting/interop/pehkui/PehkuiInterop.java",
            "Fabric/src/main/java/at/petrak/hexcasting/fabric/interop/gravity/GravityApiInterop.java",
        ],
        operator_directories=[
            "Common/src/main/java/at/petrak/hexcasting/common/casting/operators",
            "Common/src/main/java/at/petrak/hexcasting/interop/pehkui",
            "Fabric/src/main/java/at/petrak/hexcasting/fabric/interop/gravity",
        ],
        extra_classname_paths={
            "makeConstantOp": "Common/src/main/java/at/petrak/hexcasting/api/spell/ConstMediaAction.kt",
            "ConstMediaAction": "Common/src/main/java/at/petrak/hexcasting/api/spell/ConstMediaAction.kt",
        },
        pattern_stubs=hex_stubs,
        modloaders=[FORGE, FABRIC, QUILT],
    )

    Hexal = HexalRegistryModInfo(
        name="Hexal",
        description="Adds many utility patterns/spells (eg. entity health, item smelting), autonomous casting with wisps, and powerful item manipulation/storage.",
        directory="Hexal",
        book=hexal_parse_book("Hexal/Common/src/main/resources", "Hexal/doc/HexCastingResources", "hexal", "hexalbook"),
        book_url="https://talia-12.github.io/Hexal/",
        curseforge_url="https://www.curseforge.com/minecraft/mc-mods/hexal/",
        modrinth_url="https://modrinth.com/mod/hexal/",
        source_url="https://github.com/Talia-12/Hexal/",
        icon_url="https://cdn.modrinth.com/data/aBVJ6Q36/e2bfd87a5e333a972c39d12a1c4e55add7616785.jpeg",
        pattern_files=[
            "Common/src/main/java/ram/talia/hexal/common/casting/Patterns.kt",
            "Fabric/src/main/java/ram/talia/hexal/fabric/FabricHexalInitializer.kt",
        ],
        operator_directories=[
            "Common/src/main/java/ram/talia/hexal/common/casting/actions",
            "Fabric/src/main/java/ram/talia/hexal/fabric/interop/phantom",
        ],
        pattern_stubs=hexal_stubs,
        modloaders=[FORGE, FABRIC, QUILT],
    )

    MoreIotas = HexalRegistryModInfo(
        name="MoreIotas",
        description="Adds matrix and string iotas, allowing things like complex calculations and chat commands.",
        directory="MoreIotas",
        book=moreiotas_parse_book(
            "MoreIotas/Common/src/main/resources", "MoreIotas/doc/HexCastingResources", "moreiotas", "moreiotasbook"
        ),
        book_url="https://talia-12.github.io/MoreIotas/",
        curseforge_url="https://www.curseforge.com/minecraft/mc-mods/moreiotas/",
        modrinth_url="https://modrinth.com/mod/moreiotas/",
        source_url="https://github.com/Talia-12/MoreIotas/",
        icon_url="https://cdn.modrinth.com/data/Jmt7p37B/e4640394d665e134c80900c94d6d49ddb9047edd.png",
        pattern_files=["Common/src/main/java/ram/talia/moreiotas/common/casting/Patterns.kt"],
        operator_directories=["Common/src/main/java/ram/talia/moreiotas/common/casting/actions"],
        pattern_stubs=moreiotas_stubs,
        modloaders=[FORGE, FABRIC, QUILT],
    )

    HexTweaks = HexTweaksRegistryModInfo(
        name="HexTweaks",
        description="Adds various (mildly opinionated) quality of life changes, as well as dictionary iotas.",
        directory="HexTweaks",
        book=hextweaks_parse_book(
            "HexTweaks/common/src/main/resources",
            "HexTweaks/common/src/main/java",
            "HexMod/Common/src/main/resources",
            "hextweaks",
            "thetweakedbook",
        ),
        book_url="https://walksanatora.github.io/HexTweaks/",
        modrinth_url="https://modrinth.com/mod/hextweaks/",
        curseforge_url=None,
        source_url="https://github.com/walksanatora/HexTweaks/",
        icon_url="https://cdn.modrinth.com/data/pim6pG9O/0f36451e826a46c00d337d7ef65e62c87bc40eba.png",
        pattern_files=["common/src/main/java/net/walksanator/hextweaks/patterns/PatternRegister.java"],
        operator_directories=["common/src/main/java/net/walksanator/hextweaks/patterns"],
        pattern_stubs=hextweaks_stubs,
        modloaders=[FORGE, FABRIC, QUILT],
    )

    @property
    def value(self) -> RegistryModInfo:
        return super().value


class APIMod(Enum):
    # https://hexbound.cypher.coffee/versions.json
    Hexbound = APIWithBookModInfo(
        name="Hexbound",
        description="Adds several utility patterns/spells (eg. item types, Hex Shields), quasi-playerless casting with Figments, pattern editing, and constructs (powerful automatable golems).",
        curseforge_url=None,
        modrinth_url="https://modrinth.com/mod/hexbound/",
        icon_url="https://cdn.modrinth.com/data/PHgo4bVw/daa508e0b61340a46e04f669af1cf5e557193bc4.png",
        api_base_url="https://hexbound.cypher.coffee/",
        version="0.1.3+1.19.2",
        modloaders=[QUILT],
    )

    @property
    def value(self) -> APIModInfo:
        return super().value


ModInfo = RegistryModInfo | APIModInfo
Mod = RegistryMod | APIMod


def get_mod(name: str) -> Mod:
    try:
        return RegistryMod[name]
    except KeyError:
        return APIMod[name]


class ModTransformer(app_commands.Transformer):
    _choices = [app_commands.Choice(name=mod.value.name, value=mod.name) for mod in chain(RegistryMod, APIMod)]

    @property
    def choices(self) -> list[app_commands.Choice[str]]:
        return self._choices

    async def transform(self, interaction: discord.Interaction, value: str) -> Mod:
        return get_mod(value)


class WithBookModTransformer(app_commands.Transformer):
    @property
    def choices(self) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=mod.value.name, value=mod.name)
            for mod in chain(RegistryMod, APIMod)
            if mod.value.book_url is not None
        ]

    async def transform(self, interaction: discord.Interaction, value: str) -> Mod:
        return get_mod(value)


ModTransformerHint = app_commands.Transform[Mod, ModTransformer]
WithBookModTransformerHint = app_commands.Transform[Mod, WithBookModTransformer]
