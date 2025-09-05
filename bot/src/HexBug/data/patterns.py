from __future__ import annotations

from typing import Annotated

from hexdoc.core import ResourceLocation
from hexdoc.utils import PydanticURL
from pydantic import BaseModel, Field, field_validator

from .hex_math import HexDir, HexPattern, PatternSignature


class StaticPatternInfo(BaseModel):
    """Similar interface to hexdoc_hexcasting.utils.pattern.PatternInfo, because we
    don't have hexdoc_hexcasting at runtime."""

    id: ResourceLocation
    startdir: HexDir
    signature: PatternSignature
    is_per_world: bool = False


class PatternInfo(BaseModel):
    id: ResourceLocation
    name: Annotated[str, Field(max_length=256)]
    """Pattern name.

    Can be up to 256 characters, to fit in an embed title.
    """
    direction: HexDir
    signature: PatternSignature
    is_per_world: bool
    display_only: bool
    """If True, this is a fake pattern that doesn't actually exist ingame in this form.

    This is currently used for Lapisworks' per-world shapes.
    """
    display_as: ResourceLocation | None
    """If provided, when this pattern would be visible to users, display the referenced
    pattern instead.

    This is currently used for Lapisworks' per-world shapes.
    """
    operators: list[PatternOperator]

    @property
    def mod_id(self) -> PatternSignature:
        return self.id.namespace

    @property
    def pattern(self) -> HexPattern:
        return HexPattern(self.direction, self.signature)

    @property
    def is_hidden(self) -> bool:
        return self.display_as is not None

    @property
    def is_documented(self) -> bool:
        return bool(self.operators)


class PatternOperator(BaseModel):
    """Information about a specific instance of a pattern, generated from a Patchouli
    book page."""

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

    @property
    def plain_args(self) -> str | None:
        if self.inputs is None and self.outputs is None:
            return None
        inputs = f"{self.inputs} " if self.inputs else ""
        outputs = f" {self.outputs}" if self.outputs else ""
        return f"{inputs}→{outputs}"

    @field_validator("inputs", "outputs", mode="after")
    @classmethod
    def _strip_args(cls, value: str | None) -> str | None:
        value = value.strip() if value else ""
        if not value:
            return None
        return value
