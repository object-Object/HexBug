from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import InitVar, dataclass, field
from enum import Enum
from itertools import chain
from typing import AsyncIterator, Iterable

import discord
import jproperties
from aiohttp import ClientSession
from discord import app_commands
from Hexal.doc import collate_data as hexal_docgen
from hexdoc.core import ResourceLocation
from hexdoc.minecraft import I18n
from HexKinetics.doc import collate_data as hexkinetics_docgen
from HexMod.doc import collate_data as hex_docgen
from HexTweaks.doc import collate_data as hextweaks_docgen
from mediaworks.doc import collate_data as mediaworks_docgen
from MoreIotas.doc import collate_data as moreiotas_docgen

from HexBug.utils import modrinth
from HexBug.utils.hexdoc import load_hexdoc_mod, load_plugin_manager, patch_collate_data

from .api import API
from .book_types import Book as BookTypeDef
from .git import get_current_commit
from .urls import wrap_url

# monkeypatch the legacy docgens so we can use hexdoc's fancy text formatting
pm = load_plugin_manager()
for book_id, collate_data in [
    ("hexal:hexalbook", hexal_docgen),
    ("hexkinetics:hexkineticsbook", hexkinetics_docgen),
    ("hexcasting:thehexbook", hex_docgen),
    ("hextweaks:hextweaksbook", hextweaks_docgen),
    ("mediaworks:mediaworksbook", mediaworks_docgen),
    ("moreiotas:moreiotasbook", moreiotas_docgen),
]:
    patch_collate_data(
        collate_data,
        pm=pm,
        book_id=ResourceLocation.from_str(book_id),
    )

logger = logging.getLogger(__name__)

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
    modrinth_slug: str | None
    icon_url: str | None
    modloaders: list[str]
    version_regex: re.Pattern | None = None
    skipped_versions: set[str] = field(default_factory=set)

    def __post_init__(self):
        if self.modrinth_slug:
            self.modrinth_url = f"https://modrinth.com/mod/{self.modrinth_slug}/"
        else:
            self.modrinth_url = None

    def build_source_tree_url(self, path: str) -> str:
        return f"{self.source_url}tree/{self.commit}/{path}"

    def build_source_blob_url(self, path: str) -> str:
        return f"{self.source_url}blob/{self.commit}/{path}"

    def build_book_url(self, url: str, show_spoilers: bool, escape: bool) -> str | None:
        if self.book_url is None:
            return None
        book_url = f"{self.book_url}{'?nospoiler' if show_spoilers else ''}{url}"
        return wrap_url(book_url, show_spoilers, escape)

    @property
    def mod_url(self) -> str | None:
        return self.modrinth_url or self.curseforge_url

    async def get_latest_version(self, session: ClientSession) -> str | None:
        async for raw_version in self._get_raw_versions(session):
            version = self._parse_version(raw_version)
            if version not in self.skipped_versions:
                return version

    async def _get_raw_versions(self, session: ClientSession) -> AsyncIterator[str]:
        """Fetches and returns the list of available versions for this mod, from newest
        to oldest.

        Raises `ClientResponseError` if a network error occurs.
        """
        if self.modrinth_slug is None:
            return

        versions = await modrinth.get_versions(session, self.modrinth_slug)
        for version in versions:
            yield version["version_number"]

    def _parse_version(self, raw_version: str) -> str:
        if not self.version_regex:
            return raw_version

        match = self.version_regex.search(raw_version)
        if not match:
            logger.warning(
                f"Failed to match version regex for {self.name}: {raw_version}"
            )
            return raw_version

        return match[1]


class RegistryRegexType(Enum):
    """Regexes (regices?) for parsing pattern registry files."""

    HexCasting = re.compile(
        r'HexPattern\.fromAngles\("([qweasd]+)", HexDir\.(\w+)\),\s*modLoc\("([^"]+)"\)[^;]+?(makeConstantOp|Op\w+)([^;]*true\);)?',
        re.M,
    )

    Hexal = re.compile(
        r'HexPattern\.fromAngles\("([qweasd]+)", HexDir\.(\w+)\),\s*modLoc\("([^"]+)"\),[^,]+?(makeConstantOp|Op\w+).*?(\btrue)?\)(?:[^\)]+?\bval\b|(?:(?!\bval\b)(?:.))+$)',
        re.S,
    )
    r"""
    regex explanation because this is cursed
    flags: S because . needs to match newlines, and no M because we want $ to be the end of the file

    HexPattern\.fromAngles\("([qweasd]+)", HexDir\.(\w+)\),\s*  # direction and angle
    modLoc\("([^"]+)"\),.+?  # internal name
    (makeConstantOp|Op\w+)  # classname - make this a non-capturing group with ?: if you don't need it
    .*?(\btrue)?\)  # lazy wildcard, then optional true for great spells, then closing bracket
    (?:
        [^\)]+?\bval\b  # lazy match anything other than a closing bracket, because we only want to find "true" at the very end of this declaration; then find "val" to start the next pattern declaration
        |(?:(?!\bval\b)(?:.))+$  # didn't match the previous group, so keep going until the end of the document, but fail if we find "val" anywhere
    )
    """

    HexTweaks = re.compile(
        r'PatternRegistry.mapPattern\([\n ]+(?:HexPattern\.fromAngles|fromAnglesIllegal)\("([qweasd]+)", ?HexDir\.(.+)?\)[,\n ]+?new ResourceLocation\(".+"(.+)?"\),\n.+new (.+)\(.+, ?(true)?'
    )

    """
    Mediaworks declares its spells in Java code.
    Named groups are used because the is_great group is at the beginning of the match.
    """
    Mediaworks = re.compile(
        r'register(?P<is_great>PerWorld)?\(HexPattern\.fromAngles\("(?P<pattern>[qweasd]+)", HexDir\.(?P<direction>\w+)\),\s*\"(?P<name>[^"]*)\",\s*new (?P<classname>Op\w+)'
    )

    @property
    def value(self) -> re.Pattern:
        return super().value


@dataclass(kw_only=True)
class RegistryModInfo(_BaseModInfo, ABC):
    source_url: str
    book_url: str | None
    directory: str
    book: BookTypeDef
    registry_regex_type: InitVar[RegistryRegexType]
    version_property_key: InitVar[str] = field(default="modVersion")
    pattern_files: list[str]
    operator_directories: list[str]
    extra_classname_paths: dict[str, str] = field(default_factory=dict)
    # iterable instead of list because invariance etc
    # see https://github.com/microsoft/pylance-release/discussions/3383
    pattern_stubs: Iterable[tuple[str | None, str]]

    def __post_init__(
        self, registry_regex: RegistryRegexType, version_property_key: str
    ):
        super().__post_init__()
        self.commit = get_current_commit(self.directory)
        self.version = self._load_version(version_property_key)
        self.pattern_files = [f"{self.directory}/{s}" for s in self.pattern_files]
        self.operator_directories = [
            f"{self.directory}/{s}" for s in self.operator_directories
        ]
        self.registry_regex = registry_regex.value

    def _load_version(self, version_property_key: str) -> str:
        # get the version from the mod's gradle.properties (why weren't we doing this all along???)
        p = jproperties.Properties()
        with open(f"{self.directory}/gradle.properties", "rb") as f:
            p.load(f, "utf-8")
        return p[version_property_key][0]

    @property
    def modid(self) -> str:
        return self.book["modid"]


@dataclass(kw_only=True)
class _BaseAPIModInfo(_BaseModInfo, ABC):
    api_base_url: InitVar[str]
    modid: str
    version: str
    """No trailing slash"""

    def __post_init__(self, api_base_url: str):
        super().__post_init__()
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

    async def _get_raw_versions(self, session: ClientSession) -> AsyncIterator[str]:
        versions = await self.api.get_versions(session)
        for version in versions["versions"]:
            yield version["id"]


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


APIModInfo = APIWithBookModInfo | APIWithoutBookModInfo


@dataclass(kw_only=True)
class HexdocModInfo(_BaseModInfo):
    modid: str
    book_id: str
    lang: str = "en_us"

    def __post_init__(self):
        super().__post_init__()

        with load_hexdoc_mod(
            modid=self.modid,
            book_id=self.book_id,
            lang=self.lang,
        ) as (plugin, book, context, metadata, hex_metadata):
            self.version = plugin.mod_version

            self.book_url = str(metadata.book_url) if metadata.book_url else None

            # ('/', 'SamsTheNerd', 'HexGloop', '2176f6f40c1bee5c8eb8')
            _, author, repo, self.commit = metadata.asset_url.parts
            self.source_url = f"https://github.com/{author}/{repo}/"

            # new fields
            self.patterns = hex_metadata.patterns
            self.book = book
            self.i18n = I18n.of(context)


class RegistryMod(Enum):
    # HEX NEEDS TO BE FIRST
    HexCasting = RegistryModInfo(
        name="Hex Casting",
        description="A mod for Forge and Fabric adding stack-based programmable spellcasting, inspired by Psi.",
        directory="vendor/HexMod",
        book=hex_docgen.parse_book(
            "vendor/HexMod/Common/src/main/resources", "hexcasting", "thehexbook"
        ),
        registry_regex_type=RegistryRegexType.HexCasting,
        book_url="https://hexcasting.hexxy.media/v/0.10.3/1.0.dev20/en_us/",
        curseforge_url="https://www.curseforge.com/minecraft/mc-mods/hexcasting/",
        modrinth_slug="hex-casting",
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
        pattern_stubs=hex_docgen.pattern_stubs,
        modloaders=[FORGE, FABRIC, QUILT],
    )

    Hexal = RegistryModInfo(
        name="Hexal",
        description="Adds many utility patterns/spells (eg. entity health, item smelting), autonomous casting with wisps, and powerful item manipulation/storage.",
        directory="vendor/Hexal",
        book=hexal_docgen.parse_book(
            "vendor/Hexal/Common/src/main/resources",
            "vendor/Hexal/doc/HexCastingResources",
            "hexal",
            "hexalbook",
        ),
        registry_regex_type=RegistryRegexType.Hexal,
        book_url="https://talia-12.github.io/Hexal/",
        curseforge_url="https://www.curseforge.com/minecraft/mc-mods/hexal/",
        modrinth_slug="hexal",
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
        pattern_stubs=hexal_docgen.pattern_stubs,
        modloaders=[FORGE, FABRIC, QUILT],
    )

    MoreIotas = RegistryModInfo(
        name="MoreIotas",
        description="Adds matrix and string iotas, allowing things like complex calculations and chat commands.",
        directory="vendor/MoreIotas",
        book=moreiotas_docgen.parse_book(
            "vendor/MoreIotas/Common/src/main/resources",
            "vendor/MoreIotas/doc/HexCastingResources",
            "moreiotas",
            "moreiotasbook",
        ),
        registry_regex_type=RegistryRegexType.Hexal,
        book_url="https://talia-12.github.io/MoreIotas/",
        curseforge_url="https://www.curseforge.com/minecraft/mc-mods/moreiotas/",
        modrinth_slug="moreiotas",
        source_url="https://github.com/Talia-12/MoreIotas/",
        icon_url="https://cdn.modrinth.com/data/Jmt7p37B/e4640394d665e134c80900c94d6d49ddb9047edd.png",
        pattern_files=[
            "Common/src/main/java/ram/talia/moreiotas/common/casting/Patterns.kt"
        ],
        operator_directories=[
            "Common/src/main/java/ram/talia/moreiotas/common/casting/actions"
        ],
        pattern_stubs=moreiotas_docgen.pattern_stubs,
        modloaders=[FORGE, FABRIC, QUILT],
    )

    HexTweaks = RegistryModInfo(
        name="HexTweaks",
        description="Adds various (mildly opinionated) quality of life changes, as well as dictionary iotas.",
        directory="vendor/HexTweaks",
        book=hextweaks_docgen.parse_book(
            "vendor/HexTweaks/common/src/main/resources",
            "vendor/HexTweaks/common/src/main/java",
            "vendor/HexMod/Common/src/main/resources",
            "hextweaks",
            "thetweakedbook",
        ),
        registry_regex_type=RegistryRegexType.HexTweaks,
        version_property_key="mod_version",
        book_url="https://walksanatora.github.io/HexTweaks/",
        modrinth_slug="hextweaks",
        curseforge_url=None,
        source_url="https://github.com/walksanatora/HexTweaks/",
        icon_url="https://cdn.modrinth.com/data/pim6pG9O/0f36451e826a46c00d337d7ef65e62c87bc40eba.png",
        pattern_files=[
            "common/src/main/java/net/walksanator/hextweaks/patterns/PatternRegister.java"
        ],
        operator_directories=[
            "common/src/main/java/net/walksanator/hextweaks/patterns"
        ],
        pattern_stubs=hextweaks_docgen.pattern_stubs,
        modloaders=[FORGE, FABRIC, QUILT],
        skipped_versions={"3.2.3"},
    )

    HexKinetics = RegistryModInfo(
        name="HexKinetics",
        description="Adds patterns and spells related to vectors and dynamics.",
        directory="vendor/HexKinetics",
        book=hexkinetics_docgen.parse_book(
            "vendor/HexKinetics/Common/src/main/resources",
            "vendor/HexKinetics/doc/HexCastingResources",
            "hexkinetics",
            "hexkineticsbook",
        ),
        registry_regex_type=RegistryRegexType.Hexal,
        book_url="https://sonunte.github.io/HexKinetics/",
        curseforge_url=None,
        modrinth_slug="hexkinetics",
        source_url="https://github.com/Sonunte/HexKinetics/",
        icon_url="https://cdn.modrinth.com/data/8FVr3ohp/66f16e550e1757a511674b26cb9d9cda8dbbbb24.png",
        pattern_files=[
            "Common/src/main/java/net/sonunte/hexkinetics/common/casting/Patterns.kt"
        ],
        operator_directories=[
            "Common/src/main/java/net/sonunte/hexkinetics/common/casting/actions"
        ],
        pattern_stubs=hexkinetics_docgen.pattern_stubs,
        modloaders=[FABRIC, QUILT],
    )

    Mediaworks = RegistryModInfo(
        name="Mediaworks",
        description="Adds QOL features and new spells. Create HUD's and become a ghost!",  # stolen from addons.hexxy.media
        directory="vendor/mediaworks",
        book=mediaworks_docgen.parse_book(
            "vendor/mediaworks/common/src/main/resources",
            "vendor/mediaworks/doc/resources",
            "mediaworks",
            "mediaworksbook",
        ),
        registry_regex_type=RegistryRegexType.Mediaworks,
        book_url="https://artynova.github.io/mediaworks/",
        curseforge_url=None,
        modrinth_slug="mediaworks",
        source_url="https://github.com/artynova/mediaworks/",
        icon_url="https://cdn-raw.modrinth.com/data/2kZJcMa9/58257ac58547acd70079e3c436bafccbb2d52620.png",
        pattern_files=[
            "common/src/main/java/io/github/artynova/mediaworks/casting/pattern/MediaworksPatterns.java",
        ],
        operator_directories=[
            "common/src/main/java/io/github/artynova/mediaworks/casting/pattern",
        ],
        pattern_stubs=mediaworks_docgen.pattern_stubs,
        modloaders=[FORGE, FABRIC, QUILT],
    )

    @property
    def value(self) -> RegistryModInfo:
        return super().value


class APIMod(Enum):
    # https://hexbound.cypher.coffee/versions.json
    Hexbound = APIWithBookModInfo(
        name="Hexbound",
        modid="hexbound",
        description="Adds several utility patterns/spells (eg. item types, Hex Shields), quasi-playerless casting with Figments, pattern editing, and constructs (powerful automatable golems).",
        curseforge_url=None,
        modrinth_slug="hexbound",
        icon_url="https://cdn.modrinth.com/data/PHgo4bVw/daa508e0b61340a46e04f669af1cf5e557193bc4.png",
        api_base_url="https://hexbound.cypher.coffee/",
        version="0.1.3+1.19.2",
        modloaders=[QUILT],
    )

    @property
    def value(self) -> APIModInfo:
        return super().value


class HexdocMod(Enum):
    HexGloop = HexdocModInfo(
        name="Hex Gloop",
        modid="hexgloop",
        book_id="hexgloop:hexgloopbook",
        description="Hex Casting's gloopiest addon! Adds exciting new items, blocks, QoL tweaks, and the occasional new spell or two.",
        curseforge_url="https://www.curseforge.com/minecraft/mc-mods/hexgloop/",
        modrinth_slug="hexgloop",
        icon_url="https://cdn.modrinth.com/data/ryfyOhoP/fd47e532776ba9580c2e7b847b5308b7b8b9d7ae.png",
        modloaders=[FORGE, FABRIC, QUILT],
        version_regex=re.compile(
            r"""
                ^
                1\.\d+\.\d+  # Minecraft version
                -
                (\d+\.\d+\.\d+)  # mod version (we want this part)
                -
                [a-zA-Z]+  # platform (eg. fabric, forge)
                $
            """,
            re.MULTILINE | re.VERBOSE,
        ),
    )

    Oneironaut = HexdocModInfo(
        name="Oneironaut",
        modid="oneironaut",
        book_id="oneironaut:oneironautbook",
        description="An addon for Hex Casting centered around exploration and use of the noosphere.",
        curseforge_url="https://www.curseforge.com/minecraft/mc-mods/oneironaut/",
        modrinth_slug="oneironaut",
        icon_url="https://raw.githubusercontent.com/beholderface/oneironaut/14a5797b9d40/fabric/src/main/resources/icon.png",
        modloaders=[FORGE, FABRIC],
        skipped_versions={"0.2.3"},
    )

    HexKeys = HexdocModInfo(
        name="Hex Keys",
        modid="hexkeys",
        book_id="hexkeys:hexkeysbook",
        description="Unlock the secrets of your mind's library.",
        curseforge_url="https://www.curseforge.com/minecraft/mc-mods/hex-keys/",
        modrinth_slug="hexkeys",
        icon_url="https://github.com/MoonlitJolteon/hex-keys-addon/blob/main/common/src/main/resources/hexkeys.png?raw=true",
        modloaders=[FORGE, FABRIC],
    )


ModInfo = RegistryModInfo | APIModInfo | HexdocModInfo
Mod = RegistryMod | APIMod | HexdocMod

MOD_TYPES = (RegistryMod, APIMod, HexdocMod)
MODS = tuple(chain(*MOD_TYPES))


def get_mod(name: str) -> Mod:
    for mod in MOD_TYPES:
        try:
            return mod[name]
        except KeyError:
            pass
    raise KeyError(name)


class ModTransformer(app_commands.Transformer):
    _choices = [
        app_commands.Choice(name=mod.value.name, value=mod.name) for mod in MODS
    ]

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
            for mod in MODS
            if mod.value.book_url is not None
        ]

    async def transform(self, interaction: discord.Interaction, value: str) -> Mod:
        return get_mod(value)


ModTransformerHint = app_commands.Transform[Mod, ModTransformer]
WithBookModTransformerHint = app_commands.Transform[Mod, WithBookModTransformer]
