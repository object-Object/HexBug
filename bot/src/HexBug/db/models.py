from datetime import datetime

from hexdoc.core import ResourceLocation
from sqlalchemy import BigInteger, MetaData, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column

from HexBug.data.hex_math import HexDir, HexPattern

from .types import ResourceLocationType


class Base(AsyncAttrs, MappedAsDataclass, DeclarativeBase):
    # https://docs.sqlalchemy.org/en/20/core/constraints.html#configuring-constraint-naming-conventions
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
    )
    type_annotation_map = {
        ResourceLocation: ResourceLocationType,
    }


class PerWorldPattern(Base):
    __tablename__ = "per_world_pattern"
    __table_args__ = (
        # signatures should be unique per-guild (NOT globally)
        UniqueConstraint("signature", "guild_id"),
    )

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


class InfoMessage(Base):
    __tablename__ = "info_message"

    name: Mapped[str] = mapped_column(primary_key=True)
    usage_count: Mapped[int]
    last_used: Mapped[datetime]
