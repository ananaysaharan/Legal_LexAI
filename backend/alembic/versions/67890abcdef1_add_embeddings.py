"""add embedding column

Revision ID: 67890abcdef1
Revises: 567890abcdef
Create Date: 2026-07-15 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector


# revision identifiers, used by Alembic.
revision: str = '67890abcdef1'
down_revision: Union[str, None] = '567890abcdef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')
    
    # 2. Add embedding column to document_chunks
    op.add_column('document_chunks', sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=384), nullable=True))


def downgrade() -> None:
    op.drop_column('document_chunks', 'embedding')
    op.execute('DROP EXTENSION IF EXISTS vector;')
