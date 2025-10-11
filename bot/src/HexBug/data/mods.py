from enum import Enum
from typing import Self

from hexdoc.utils.types import PydanticURL
from pydantic import BaseModel, model_validator
from yarl import URL

from HexBug.data.sources import SourceInfo


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
    """Relative URLs are interpreted relative to the mod's repository root."""
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
    book_title: str
    book_description: str

    source: SourceInfo

    pattern_count: int = 0
    """Total number of patterns in this mod, excluding display-only patterns."""
    documented_pattern_count: int = 0
    """Number of patterns in this mod documented by at least one book page, excluding
    display-only patterns."""
    special_handler_count: int = 0
    """Number of special handlers supported by HexBug in this mod."""
    first_party_operator_count: int = 0
    """Number of operators added to this mod's patterns by this mod."""
    third_party_operator_count: int = 0
    """Number of operators added to other mods' patterns by this mod."""

    category_count: int = 0
    entry_count: int = 0
    linkable_page_count: int = 0
    recipe_count: int = 0

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
        """Returns `version` if `is_versioned` is True, otherwise appends the source
        commit hash."""
        if self.is_versioned:
            return self.version
        return f"{self.version} @ {self.source.commit[:8]}"


class ModInfo(StaticModInfo, DynamicModInfo):
    @classmethod
    def from_parts(cls, static: StaticModInfo, dynamic: DynamicModInfo) -> Self:
        return cls(**dict(static), **dict(dynamic))

    @model_validator(mode="after")
    def _resolve_relative_icon_url(self):
        if self.icon_url and not self.icon_url.absolute:
            # https://github.com/aio-libs/yarl/issues/896
            self.icon_url = self.source.asset_url / str(self.icon_url)
        return self
