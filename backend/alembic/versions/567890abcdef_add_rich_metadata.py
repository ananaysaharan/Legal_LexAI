"""add rich metadata for chunks

Revision ID: 567890abcdef
Revises: 4567890abcde
Create Date: 2026-07-15 15:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '567890abcdef'
down_revision: Union[str, None] = '4567890abcde'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add document_type and version to documents
    op.add_column('documents', sa.Column('document_type', sa.String(), nullable=True))
    op.add_column('documents', sa.Column('version', sa.String(), nullable=True))
    
    # Add section and clause to document_chunks
    op.add_column('document_chunks', sa.Column('section', sa.String(), nullable=True))
    op.add_column('document_chunks', sa.Column('clause', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('document_chunks', 'clause')
    op.drop_column('document_chunks', 'section')
    op.drop_column('documents', 'version')
    op.drop_column('documents', 'document_type')
