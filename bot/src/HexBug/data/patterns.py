from __future__ import annotations

from hexdoc.core import ResourceLocation
from hexdoc.utils import PydanticURL
from pydantic import BaseModel, field_validator

from .hex_math import HexDir


class PatternInfo(BaseModel):
    id: ResourceLocation
    name: str
    """Canonical name.

    Note that individual operators may have different names (eg. MoreIotas renames
    Retrograde Purification to Transpose Purification when used on a matrix).
    """
    direction: HexDir
    signature: str
    operators: dict[str | None, PatternOperator]
    """Mapping from operator.inputs to operator.

    TODO: does this really need to be a dict?
    """


class PatternOperator(BaseModel):
    name: str
    description: str | None
    inputs: str | None
    outputs: str | None
    book_url: PydanticURL | None

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
