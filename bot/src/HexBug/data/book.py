from typing import Annotated, Any

from hexdoc.core import ResourceLocation
from hexdoc.model import Color
from hexdoc.utils import PydanticURL
from pydantic import BaseModel as _BaseModel, BeforeValidator, PlainSerializer


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
    title: str | None
    text: str | None


def _validate_PageKey(value: Any):
    if isinstance(value, str):
        return value.split("#", 1)
    return value


def _serialize_PageKey(value: tuple[ResourceLocation, str]):
    return f"{value[0]}#{value[1]}"


type PageKey = Annotated[
    tuple[ResourceLocation, str],
    BeforeValidator(_validate_PageKey),
    PlainSerializer(_serialize_PageKey),
]
