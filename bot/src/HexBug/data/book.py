from __future__ import annotations

from hexdoc.core import ResourceLocation
from hexdoc.model import Color
from hexdoc.utils import PydanticURL
from pydantic import BaseModel as _BaseModel


class BaseModel(_BaseModel):
    mod_id: str
    url: PydanticURL
    icon_urls: list[PydanticURL]  # teehee


class CategoryInfo(BaseModel):
    id: ResourceLocation
    name: str
    description: str


class EntryInfo(BaseModel):
    category_id: ResourceLocation
    id: ResourceLocation
    name: str
    color: Color | None


class PageInfo(BaseModel):
    entry_id: ResourceLocation
    anchor: str
    title: str
    text: str | None

    @property
    def key(self) -> str:
        return f"{self.entry_id}#{self.anchor}"
