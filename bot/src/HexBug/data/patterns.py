from __future__ import annotations

from typing import Annotated

from hexdoc.core import ResourceLocation
from hexdoc.utils import PydanticURL
from pydantic import BaseModel, Field, field_validator

from .hex_math import HexDir


class PatternInfo(BaseModel):
    id: ResourceLocation
    name: Annotated[str, Field(max_length=256)]
    """Canonical name.

    Note that individual operators may have different names (eg. MoreIotas renames
    Retrograde Purification to Transpose Purification when used on a matrix).

    Can be up to 256 characters, to fit in an embed title.
    """
    direction: HexDir
    signature: str
    is_per_world: bool
    operators: list[PatternOperator]


class PatternOperator(BaseModel):
    name: Annotated[str, Field(max_length=256)]
    """Pattern name from the page header.

    This may or may not be the name you want to use. For example, page headers use the
    shortened version of pattern names (eg. Zone Dstl. instead of Zone Distillation),
    and a few patterns (eg. Vector Reflection +X) don't use the pattern name for the
    title at all.

    Can be up to 256 characters, to fit in an embed title.
    """
    description: Annotated[str | None, Field(max_length=4096)]
    """Description from the pattern page, or from the next page in some cases.

    Can be up to 4096 characters, to fit in an embed description.
    """
    inputs: str | None
    outputs: str | None
    book_url: PydanticURL | None
    mod_id: str

    @property
    def args(self) -> str | None:
        if self.inputs is None and self.outputs is None:
            return None
        inputs = f"__{self.inputs}__ " if self.inputs else ""
        outputs = f" __{self.outputs}__" if self.outputs else ""
        return f"**{inputs}→{outputs}**"

    @field_validator("inputs", "outputs", mode="after")
    @classmethod
    def _strip_args(cls, value: str | None) -> str | None:
        value = value.strip() if value else ""
        if not value:
            return None
        return value


class StaticPatternInfo(BaseModel):
    """Similar interface to hexdoc_hexcasting.utils.pattern.PatternInfo, because we
    don't have hexdoc_hexcasting at runtime."""

    id: ResourceLocation
    startdir: HexDir
    signature: str
    is_per_world: bool = False


EXTRA_PATTERNS: list[StaticPatternInfo] = [
    StaticPatternInfo(
        id=ResourceLocation("hexcasting", "escape"),
        startdir=HexDir.WEST,
        signature="qqqaw",
    ),
    StaticPatternInfo(
        id=ResourceLocation("hexcasting", "open_paren"),
        startdir=HexDir.WEST,
        signature="qqq",
    ),
    StaticPatternInfo(
        id=ResourceLocation("hexcasting", "close_paren"),
        startdir=HexDir.WEST,
        signature="eee",
    ),
    StaticPatternInfo(
        id=ResourceLocation("hexcasting", "undo"),
        startdir=HexDir.WEST,
        signature="eeedw",
    ),
]
