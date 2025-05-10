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
    icon_url: PydanticURL | None
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

    pattern_count: int = 0
    special_handler_count: int = 0
    first_party_operator_count: int = 0
    """Number of operators added to this mod's patterns by this mod."""
    third_party_operator_count: int = 0
    """Number of operators added to other mods' patterns by this mod."""

    @property
    def github_url(self) -> URL:
        return URL("https://github.com") / self.github_author / self.github_repo

    @property
    def github_permalink(self) -> URL:
        return self.github_url / "tree" / self.github_commit

    @property
    def is_versioned(self) -> bool:
        """Returns True if the hexdoc plugin was built from a static book version.

        For example:
        - `https://hexcasting.hexxy.media/v/0.11.2/1.0/en_us`: True
        - `https://hexcasting.hexxy.media/v/latest/main/en_us`: False
        """
        return "/v/latest/" not in self.book_url.path

    @property
    def pretty_version(self) -> str:
        """Returns `version` if `is_versioned` is True, otherwise appends the GitHub
        commit hash."""
        if self.is_versioned:
            return self.version
        return f"{self.version} @ {self.github_commit[:8]}"


class ModInfo(StaticModInfo, DynamicModInfo):
    @classmethod
    def from_parts(cls, static: StaticModInfo, dynamic: DynamicModInfo) -> Self:
        return cls(**dict(static), **dict(dynamic))
