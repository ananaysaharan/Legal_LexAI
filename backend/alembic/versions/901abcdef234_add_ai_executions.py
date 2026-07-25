"""add AI execution records

Revision ID: 901abcdef234
Revises: 890abcdef123
Create Date: 2026-07-25 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "901abcdef234"
down_revision: Union[str, None] = "890abcdef123"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("request_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("intent_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("plan_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("trace_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_ai_executions_case_id", "ai_executions", ["case_id"])
    op.create_index("ix_ai_executions_user_id", "ai_executions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_executions_user_id", table_name="ai_executions")
    op.drop_index("ix_ai_executions_case_id", table_name="ai_executions")
    op.drop_table("ai_executions")
