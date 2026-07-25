"""add document workspace version fields

Revision ID: b56cdef789
Revises: a45bcdef678
Create Date: 2026-07-26 00:00:00.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "b56cdef789"
down_revision = "a45bcdef678"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "generated_documents",
        sa.Column("parent_document_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "generated_documents",
        sa.Column("edit_operation", sa.String(length=30), nullable=False, server_default="generate"),
    )
    op.add_column("generated_documents", sa.Column("edit_instructions", sa.Text(), nullable=True))
    op.add_column("generated_documents", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.create_foreign_key(
        "fk_generated_documents_parent_document_id",
        "generated_documents", "generated_documents", ["parent_document_id"], ["id"], ondelete="SET NULL",
    )
    op.create_index("ix_generated_documents_parent_document_id", "generated_documents", ["parent_document_id"])
    op.alter_column("generated_documents", "edit_operation", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_generated_documents_parent_document_id", table_name="generated_documents")
    op.drop_constraint("fk_generated_documents_parent_document_id", "generated_documents", type_="foreignkey")
    op.drop_column("generated_documents", "deleted_at")
    op.drop_column("generated_documents", "edit_instructions")
    op.drop_column("generated_documents", "edit_operation")
    op.drop_column("generated_documents", "parent_document_id")
