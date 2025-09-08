from hexdoc.core import ResourceLocation
from sqlalchemy import BigInteger
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column

from HexBug.data.hex_math import HexDir, HexPattern

from .types import ResourceLocationType


class Base(AsyncAttrs, MappedAsDataclass, DeclarativeBase):
    type_annotation_map = {
        ResourceLocation: ResourceLocationType,
    }


class PerWorldPattern(Base):
    __tablename__ = "per_world_pattern"

    id: Mapped[ResourceLocation] = mapped_column(primary_key=True)
    """The ResourceLocation of the pattern.

    Example: `hexcasting:create_lava`
    """
    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    """The guild where this pattern was added."""
    user_id: Mapped[int] = mapped_column(BigInteger)
    """The user that added this pattern."""

    direction: Mapped[HexDir]
    """Starting direction."""
    signature: Mapped[str]
    """Angle signature."""

    @property
    def pattern(self):
        return HexPattern(self.direction, self.signature)
