"""Fix per_world_pattern.signature unique constraint to be per-guild instead of global

Revision ID: b83e6ea86a3e
Revises: 3c2581c7e1e3
Create Date: 2025-09-09 23:09:26.393963

"""

from typing import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b83e6ea86a3e"
down_revision: str | Sequence[str] | None = "3c2581c7e1e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(
        op.f("uq_per_world_pattern_signature"), "per_world_pattern", type_="unique"
    )
    op.create_unique_constraint(
        op.f("uq_per_world_pattern_signature"),
        "per_world_pattern",
        ["signature", "guild_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        op.f("uq_per_world_pattern_signature"), "per_world_pattern", type_="unique"
    )
    op.create_unique_constraint(
        op.f("uq_per_world_pattern_signature"),
        "per_world_pattern",
        ["signature"],
    )
