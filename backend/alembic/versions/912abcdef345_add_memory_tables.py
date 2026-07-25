"""add case and user preference memory tables

Revision ID: 912abcdef345
Revises: 901abcdef234
Create Date: 2026-07-26 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "912abcdef345"
down_revision: Union[str, None] = "901abcdef234"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "case_memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("memory_type", sa.String(length=80), nullable=False),
        sa.Column("memory_key", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_execution_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_execution_id"], ["ai_executions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_document_id"], ["documents.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_case_memories_case_id", "case_memories", ["case_id"])
    op.create_index("ix_case_memories_memory_type", "case_memories", ["memory_type"])
    op.create_index("ix_case_memories_memory_key", "case_memories", ["memory_key"])
    op.create_index("ix_case_memories_source_execution_id", "case_memories", ["source_execution_id"])
    op.create_index("ix_case_memories_source_document_id", "case_memories", ["source_document_id"])
    op.create_table(
        "user_preference_memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("preference_key", sa.String(length=120), nullable=False),
        sa.Column("preference_value", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("scope", sa.String(length=80), nullable=False),
        sa.Column("metadata_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_id", "preference_key", "scope", name="uq_user_preference_scope"),
    )
    op.create_index("ix_user_preference_memories_user_id", "user_preference_memories", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_preference_memories_user_id", table_name="user_preference_memories")
    op.drop_table("user_preference_memories")
    op.drop_index("ix_case_memories_source_document_id", table_name="case_memories")
    op.drop_index("ix_case_memories_source_execution_id", table_name="case_memories")
    op.drop_index("ix_case_memories_memory_key", table_name="case_memories")
    op.drop_index("ix_case_memories_memory_type", table_name="case_memories")
    op.drop_index("ix_case_memories_case_id", table_name="case_memories")
    op.drop_table("case_memories")
