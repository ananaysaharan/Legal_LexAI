"""add generated documents

Revision ID: a45bcdef678
Revises: 934abcdef567
Create Date: 2026-07-26 00:00:00.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "a45bcdef678"
down_revision = "934abcdef567"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "generated_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_execution_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("document_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("document_key", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("metadata_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("citations_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_execution_id"], ["ai_executions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("case_id", "document_key", "version", name="uq_generated_document_version"),
    )
    op.create_index("ix_generated_documents_case_id", "generated_documents", ["case_id"])
    op.create_index("ix_generated_documents_document_type", "generated_documents", ["document_type"])
    op.create_index("ix_generated_documents_source_execution_id", "generated_documents", ["source_execution_id"])


def downgrade() -> None:
    op.drop_index("ix_generated_documents_source_execution_id", table_name="generated_documents")
    op.drop_index("ix_generated_documents_document_type", table_name="generated_documents")
    op.drop_index("ix_generated_documents_case_id", table_name="generated_documents")
    op.drop_table("generated_documents")
