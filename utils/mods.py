from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import InitVar, dataclass, field
from enum import Enum
from itertools import chain

import discord
from discord import app_commands

from Hexal.doc.collate_data import parse_book as hexal_parse_book
from hexdecode.hex_math import Direction
from HexMod.doc.collate_data import parse_book as hex_parse_book
from MoreIotas.doc.collate_data import parse_book as moreiotas_parse_book
from utils.book_types import Book
from utils.git import get_current_commit


@dataclass(kw_only=True)
class SpecialPatternInfo:
    name: str
    direction: Direction
    pattern: str
    is_great: bool
    classname: str
    path: str

    @property
    def add_to_registry_kwargs(self):
        return {
            "direction": self.direction,
            "pattern": self.pattern,
            "name": self.name,
            "classname": self.classname,
            "is_great": self.is_great,
        }


@dataclass(kw_only=True)
class BaseModInfo(ABC):
    name: str
    book_url: str | None
    mod_url: str | None
    source_url: str
    icon_url: str | None

    @abstractmethod
    def build_source_url(self, path: str) -> str:
        raise NotImplementedError


@dataclass(kw_only=True)
class RegistryModInfo(BaseModInfo):
    directory: InitVar[str]
    book: Book
    registry_regex: re.Pattern[str]
    pattern_files: list[str]
    operator_directories: list[str]
    special_patterns: list[SpecialPatternInfo] = field(default_factory=list)
    extra_classname_paths: dict[str, str] = field(default_factory=dict)
    extra_translation_paths: dict[str, tuple[str, str, str]] = field(default_factory=dict)
    """translation: (path, name, classname)"""

    def __post_init__(self, directory: str):
        self.commit = get_current_commit(directory)

        for special_pattern in self.special_patterns:
            if special_pattern.classname in self.extra_classname_paths:
                raise Exception(
                    f"Duplicate classname path: remove {special_pattern.classname} from {self.name}.classname_paths"
                )
            self.extra_classname_paths[special_pattern.classname] = special_pattern.path

        self.pattern_files = [f"{directory}/{s}" for s in self.pattern_files]
        self.operator_directories = [f"{directory}/{s}" for s in self.operator_directories]

    def build_source_url(self, path: str) -> str:
        return f"{self.source_url}blob/{self.commit}/{path}"


@dataclass(kw_only=True)
class HexalRegistryModInfo(RegistryModInfo):
    # thanks Talia for changing the registry format
    registry_regex: re.Pattern[str] = re.compile(
        r'HexPattern\.fromAngles\("([qweasd]+)", HexDir\.(\w+)\),\s*modLoc\("([^"]+)"\)[^val]+?(makeConstantOp|Op\w+)(?:[^val]*[^\(](true)\))?',
        re.M,
    )


@dataclass(kw_only=True)
class APIModInfo(BaseModInfo):
    base_api_url: str

    def build_source_url(self, path: str) -> str:
        return super().build_source_url(path)


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
        # https://github.com/gamma-delta/HexMod/blob/main/Common/src/main/java/at/petrak/hexcasting/api/spell/casting/SpecialPatterns.java
        # https://github.com/gamma-delta/HexMod/blob/main/Common/src/main/java/at/petrak/hexcasting/api/utils/PatternNameHelper.java
        special_patterns=[
            SpecialPatternInfo(
                name="open_paren",
                direction=Direction.WEST,
                pattern="qqq",
                is_great=False,
                classname="INTROSPECTION",
                path="Common/src/main/java/at/petrak/hexcasting/api/spell/casting/CastingHarness.kt",
            ),
            SpecialPatternInfo(
                name="close_paren",
                direction=Direction.EAST,
                pattern="eee",
                is_great=False,
                classname="RETROSPECTION",
                path="Common/src/main/java/at/petrak/hexcasting/api/spell/casting/CastingHarness.kt",
            ),
            SpecialPatternInfo(
                name="escape",
                direction=Direction.WEST,
                pattern="qqqaw",
                is_great=False,
                classname="CONSIDERATION",
                path="Common/src/main/java/at/petrak/hexcasting/api/spell/casting/CastingHarness.kt",
            ),
        ],
        extra_classname_paths={"makeConstantOp": f"Common/src/main/java/at/petrak/hexcasting/api/spell/Action.kt"},
        extra_translation_paths={
            "Numerical Reflection": (
                f"Common/src/main/java/at/petrak/hexcasting/common/casting/RegisterPatterns.java",
                "number",
                "SpecialHandler",
            ),
            "Bookkeeper's Gambit": (
                f"Common/src/main/java/at/petrak/hexcasting/common/casting/RegisterPatterns.java",
                "mask",
                "SpecialHandler",
            ),
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
    Hexbound = APIModInfo(
        name="Hexbound",
        book_url=None,
        mod_url=None,
        source_url="https://github.com/Cypher121/hexbound/",
        icon_url=None,
        base_api_url="https://hexbound.cypher.coffee/",
    )

    @property
    def value(self) -> APIModInfo:
        return super().value


ModInfo = RegistryModInfo | APIModInfo
Mod = RegistryMod | APIMod


class ModTransformer(app_commands.Transformer):
    _mods = {mod.name: mod for mod in chain(RegistryMod, APIMod)}
    _choices = [app_commands.Choice(name=mod.value.name, value=mod.name) for mod in _mods.values()]

    @property
    def choices(self) -> list[app_commands.Choice[str]]:
        return self._choices

    async def transform(self, interaction: discord.Interaction, value: str) -> Mod:
        return self._mods[value]


ModTransformerHint = app_commands.Transform[Mod, ModTransformer]
