"""Add table for /info usage tracking

Revision ID: edf289098923
Revises: b83e6ea86a3e
Create Date: 2025-09-27 20:22:02.383880

"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "edf289098923"
down_revision: str | Sequence[str] | None = "b83e6ea86a3e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "info_message",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("usage_count", sa.Integer(), nullable=False),
        sa.Column("last_used", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("name", name=op.f("pk_info_message")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("info_message")
