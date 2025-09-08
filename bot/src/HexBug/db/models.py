from hexdoc.core import ResourceLocation
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from HexBug.data.hex_math import HexDir

from .types import ResourceLocationType


class Base(DeclarativeBase):
    type_annotation_map = {
        ResourceLocation: ResourceLocationType,
    }


class PerWorldPattern(Base):
    __tablename__ = "per_world_pattern"

    id: Mapped[ResourceLocation] = mapped_column(primary_key=True)
    """The ResourceLocation of the pattern.

    Example: `hexcasting:create_lava`
    """
    guild_id: Mapped[int] = mapped_column(primary_key=True)
    """The guild where this pattern was added."""
    user_id: Mapped[int]
    """The user that added this pattern."""

    direction: Mapped[HexDir]
    """Starting direction."""
    signature: Mapped[str]
    """Angle signature."""
