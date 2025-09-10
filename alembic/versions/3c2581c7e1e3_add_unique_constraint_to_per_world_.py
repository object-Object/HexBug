"""Add unique constraint to per_world_pattern.signature

Revision ID: 3c2581c7e1e3
Revises: 33506baa6a28
Create Date: 2025-09-09 22:36:52.737480

"""

from typing import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3c2581c7e1e3"
down_revision: str | Sequence[str] | None = "33506baa6a28"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        op.f("uq_per_world_pattern_signature"), "per_world_pattern", ["signature"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        op.f("uq_per_world_pattern_signature"), "per_world_pattern", type_="unique"
    )
