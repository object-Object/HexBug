from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import InitVar, dataclass, field
from enum import Enum
from itertools import chain

import discord
from discord import app_commands

from Hexal.doc.collate_data import parse_book as hexal_parse_book
from HexMod.doc.collate_data import parse_book as hex_parse_book
from MoreIotas.doc.collate_data import parse_book as moreiotas_parse_book
from utils.api import API
from utils.book_types import Book
from utils.git import get_current_commit
from utils.urls import wrap_url


class NotInitializedError(Exception):
    """Attribute that hasn't been initialized yet."""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


@dataclass(kw_only=True)
class _BaseModInfo(ABC):
    name: str
    source_url: str = field(init=False)
    book_url: str | None = field(init=False)
    commit: str = field(init=False)
    mod_url: str | None
    icon_url: str | None

    def build_source_url(self, path: str) -> str:
        return f"{self.source_url}blob/{self.commit}/{path}"

    @abstractmethod
    def build_book_url(self, url: str, show_spoilers: bool, escape: bool) -> str:
        raise NotImplementedError


@dataclass(kw_only=True)
class RegistryModInfo(_BaseModInfo):
    source_url: str = field()
    book_url: str | None = field()
    directory: InitVar[str]
    book: Book
    registry_regex: re.Pattern[str]
    pattern_files: list[str]
    operator_directories: list[str]
    extra_classname_paths: dict[str, str] = field(default_factory=dict)

    def __post_init__(self, directory: str):
        self.commit = get_current_commit(directory)
        self.pattern_files = [f"{directory}/{s}" for s in self.pattern_files]
        self.operator_directories = [f"{directory}/{s}" for s in self.operator_directories]

    def build_book_url(self, url: str, show_spoilers: bool, escape: bool) -> str:
        book_url = f"{self.book_url}{'?nospoiler' if show_spoilers else ''}{url}"
        return wrap_url(book_url, show_spoilers, escape)


@dataclass(kw_only=True)
class HexalRegistryModInfo(RegistryModInfo):
    # thanks Talia for changing the registry format
    registry_regex: re.Pattern[str] = re.compile(
        r'HexPattern\.fromAngles\("([qweasd]+)", HexDir\.(\w+)\),\s*modLoc\("([^"]+)"\)[^val]+?(makeConstantOp|Op\w+)(?:[^val]*[^\(](true)\))?',
        re.M,
    )


@dataclass(kw_only=True)
class _BaseAPIModInfo(_BaseModInfo, ABC):
    api_base_url: InitVar[str]
    version: str
    """No trailing slash"""

    def __post_init__(self, api_base_url: str):
        self.api = API(f"{api_base_url}{self.version}/")
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

    def build_book_url(self, url: str, show_spoilers: bool, escape: bool) -> str:
        return wrap_url(self.book_url + url, show_spoilers, escape)


class APIWithoutBookModInfo(_BaseAPIModInfo):
    def __late_init__(self, source_url: str, commit: str):
        return super().__late_init__(source_url, None, commit)

    @property
    def book_url(self) -> None:
        return None

    def build_book_url(self, url: str, show_spoilers: bool, escape: bool) -> str:
        raise NotImplementedError


APIModInfo = APIWithBookModInfo | APIWithoutBookModInfo


class RegistryMod(Enum):
    HexCasting = RegistryModInfo(
        name="Hex Casting",
        directory="HexMod",
        book=hex_parse_book("HexMod/Common/src/main/resources", "hexcasting", "thehexbook"),
        book_url="https://gamma-delta.github.io/HexMod/",
        mod_url="https://www.curseforge.com/minecraft/mc-mods/hexcasting/",
        source_url="https://github.com/gamma-delta/HexMod/",
        icon_url="https://media.forgecdn.net/avatars/thumbnails/535/944/64/64/637857298951404372.png",
        # thanks Alwinfy for (unknowingly) making my registry regex about 5x simpler
        registry_regex=re.compile(
            r'HexPattern\.fromAngles\("([qweasd]+)", HexDir\.(\w+)\),\s*modLoc\("([^"]+)"\)[^;]+?(makeConstantOp|Op\w+)([^;]*true\);)?',
            re.M,
        ),
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
    )

    Hexal = HexalRegistryModInfo(
        name="Hexal",
        directory="Hexal",
        book=hexal_parse_book("Hexal/Common/src/main/resources", "Hexal/doc/HexCastingResources", "hexal", "hexalbook"),
        book_url="https://talia-12.github.io/Hexal/",
        mod_url="https://modrinth.com/mod/hexal/",
        source_url="https://github.com/Talia-12/Hexal/",
        icon_url="https://cdn.modrinth.com/data/aBVJ6Q36/e2bfd87a5e333a972c39d12a1c4e55add7616785.jpeg",
        pattern_files=["Common/src/main/java/ram/talia/hexal/common/casting/Patterns.kt"],
        operator_directories=["Common/src/main/java/ram/talia/hexal/common/casting/actions"],
    )

    MoreIotas = HexalRegistryModInfo(
        name="MoreIotas",
        directory="MoreIotas",
        book=moreiotas_parse_book(
            "MoreIotas/Common/src/main/resources", "MoreIotas/doc/HexCastingResources", "moreiotas", "moreiotasbook"
        ),
        book_url="https://talia-12.github.io/MoreIotas/",
        mod_url="https://modrinth.com/mod/moreiotas/",
        source_url="https://github.com/Talia-12/MoreIotas/",
        icon_url="https://cdn.modrinth.com/data/Jmt7p37B/e4640394d665e134c80900c94d6d49ddb9047edd.png",
        pattern_files=["Common/src/main/java/ram/talia/moreiotas/common/casting/Patterns.kt"],
        operator_directories=["Common/src/main/java/ram/talia/moreiotas/common/casting/actions"],
    )

    @property
    def value(self) -> RegistryModInfo:
        return super().value


class APIMod(Enum):
    # https://hexbound.cypher.coffee/versions.json
    Hexbound = APIWithoutBookModInfo(
        name="Hexbound",
        mod_url="https://modrinth.com/mod/hexbound/",
        icon_url="https://cdn.modrinth.com/data/PHgo4bVw/daa508e0b61340a46e04f669af1cf5e557193bc4.png",
        api_base_url="https://hexbound.cypher.coffee/",
        version="0.1.0-beta.2+1.19.2",
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
    _choices = [
        app_commands.Choice(name=mod.value.name, value=mod.name)
        for mod in chain(RegistryMod, APIMod)
        if mod.value.book_url is not None
    ]

    @property
    def choices(self) -> list[app_commands.Choice[str]]:
        return self._choices

    async def transform(self, interaction: discord.Interaction, value: str) -> Mod:
        return get_mod(value)


ModTransformerHint = app_commands.Transform[Mod, ModTransformer]
WithBookModTransformerHint = app_commands.Transform[Mod, WithBookModTransformer]
