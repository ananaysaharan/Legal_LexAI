"""add conversation provenance to case memory

Revision ID: 923abcdef456
Revises: 912abcdef345
Create Date: 2026-07-26 13:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "923abcdef456"
down_revision: Union[str, None] = "912abcdef345"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "case_memories",
        sa.Column("source_conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_case_memories_source_conversation_id",
        "case_memories",
        "conversations",
        ["source_conversation_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_case_memories_source_conversation_id",
        "case_memories",
        ["source_conversation_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_case_memories_source_conversation_id", table_name="case_memories")
    op.drop_constraint(
        "fk_case_memories_source_conversation_id", "case_memories", type_="foreignkey"
    )
    op.drop_column("case_memories", "source_conversation_id")
