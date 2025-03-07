from enum import Enum
from typing import Self

from hexdoc.utils.types import PydanticURL
from pydantic import BaseModel
from yarl import URL


class Modloader(Enum):
    FABRIC = "Fabric"
    FORGE = "Forge"
    NEOFORGE = "NeoForge"
    QUILT = "Quilt"


class StaticModInfo(BaseModel):
    id: str
    name: str
    description: str
    icon_url: PydanticURL
    curseforge_slug: str | None
    modrinth_slug: str | None
    modloaders: list[Modloader]

    @property
    def curseforge_url(self) -> URL | None:
        if self.curseforge_slug:
            return (
                URL("https://curseforge.com/minecraft/mc-mods") / self.curseforge_slug
            )

    @property
    def modrinth_url(self) -> URL | None:
        if self.modrinth_slug:
            return URL("https://modrinth.com/mod") / self.modrinth_slug


class DynamicModInfo(BaseModel):
    version: str
    book_url: PydanticURL
    github_author: str
    github_repo: str
    github_commit: str

    @property
    def github_url(self) -> URL:
        return URL("https://github.com") / self.github_author / self.github_repo


class ModInfo(StaticModInfo, DynamicModInfo):
    @classmethod
    def from_parts(cls, static: StaticModInfo, dynamic: DynamicModInfo) -> Self:
        return cls(**dict(static), **dict(dynamic))
