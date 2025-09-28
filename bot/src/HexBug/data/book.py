from __future__ import annotations

from hexdoc.core import ResourceLocation
from hexdoc.model import Color
from hexdoc.utils import PydanticURL
from pydantic import BaseModel


class BaseBookModel(BaseModel):
    mod_id: str
    url: PydanticURL
    icon_urls: list[PydanticURL]  # teehee


class CategoryInfo(BaseBookModel):
    id: ResourceLocation
    name: str
    description: str


class EntryInfo(BaseBookModel):
    category_id: ResourceLocation
    id: ResourceLocation
    name: str
    color: Color | None


class PageInfo(BaseBookModel):
    entry_id: ResourceLocation
    anchor: str
    title: str
    text: str | None

    @property
    def key(self) -> str:
        return f"{self.entry_id}#{self.anchor}"


class RecipeInfo(BaseModel):
    mod_id: str
    icon_urls: list[PydanticURL]
    entry_id: ResourceLocation
    page_key: str | None
    type: ResourceLocation
    id: ResourceLocation
    name: str
    description: str | None
