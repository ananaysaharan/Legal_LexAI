"""add hnsw index

Revision ID: 7890abcdef12
Revises: 67890abcdef1
Create Date: 2026-07-16 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7890abcdef12'
down_revision: Union[str, None] = '67890abcdef1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create an HNSW index for cosine similarity (vector_cosine_ops)
    op.execute(
        "CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS document_chunks_embedding_idx;")
