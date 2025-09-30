"""Add per_world_pattern table

Revision ID: 33506baa6a28
Revises:
Create Date: 2025-09-07 21:56:52.730654

"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

import HexBug.db.types

# revision identifiers, used by Alembic.
revision: str = "33506baa6a28"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "per_world_pattern",
        sa.Column("id", HexBug.db.types.ResourceLocationType(), nullable=False),
        sa.Column("guild_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "direction",
            sa.Enum(
                "NORTH_EAST",
                "EAST",
                "SOUTH_EAST",
                "SOUTH_WEST",
                "WEST",
                "NORTH_WEST",
                name="hexdir",
            ),
            nullable=False,
        ),
        sa.Column("signature", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", "guild_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("per_world_pattern")
    op.execute("DROP TYPE hexdir")
