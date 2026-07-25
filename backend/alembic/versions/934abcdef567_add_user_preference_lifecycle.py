"""add user preference lifecycle

Revision ID: 934abcdef567
Revises: 923abcdef456
Create Date: 2026-07-26 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

revision = "934abcdef567"
down_revision = "923abcdef456"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_preference_memories",
        sa.Column(
            "preference_type",
            sa.String(length=80),
            nullable=False,
            server_default="custom",
        ),
    )
    op.add_column(
        "user_preference_memories",
        sa.Column("confidence", sa.Integer(), nullable=False, server_default="100"),
    )
    op.add_column(
        "user_preference_memories",
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "user_preference_memories",
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "user_preference_memories",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index(
        "ix_user_preference_memories_preference_type",
        "user_preference_memories",
        ["preference_type"],
    )
    op.alter_column("user_preference_memories", "preference_type", server_default=None)
    op.alter_column("user_preference_memories", "confidence", server_default=None)
    op.alter_column("user_preference_memories", "usage_count", server_default=None)
    op.alter_column("user_preference_memories", "is_active", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_user_preference_memories_preference_type", table_name="user_preference_memories")
    op.drop_column("user_preference_memories", "is_active")
    op.drop_column("user_preference_memories", "last_used_at")
    op.drop_column("user_preference_memories", "usage_count")
    op.drop_column("user_preference_memories", "confidence")
    op.drop_column("user_preference_memories", "preference_type")
