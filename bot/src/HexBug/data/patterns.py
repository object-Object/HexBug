from __future__ import annotations

from typing import Annotated

from hexdoc.core import ResourceLocation
from hexdoc.utils import PydanticURL
from pydantic import BaseModel, Field, field_validator

from .hex_math import HexDir


class StaticPatternInfo(BaseModel):
    """Similar interface to hexdoc_hexcasting.utils.pattern.PatternInfo, because we
    don't have hexdoc_hexcasting at runtime."""

    id: ResourceLocation
    startdir: HexDir
    signature: str
    is_per_world: bool = False


class PatternInfo(BaseModel):
    id: ResourceLocation
    name: Annotated[str, Field(max_length=256)]
    """Pattern name.

    Can be up to 256 characters, to fit in an embed title.
    """
    direction: HexDir
    signature: str
    is_per_world: bool
    operators: list[PatternOperator]


class PatternOperator(BaseModel):
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
