"""initial_migration

Revision ID: 1234567890ab
Revises: 
Create Date: 2026-07-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1234567890ab'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This is an empty migration.
    # In the future, Alembic will automatically generate code here 
    # to create tables (e.g., op.create_table('users', ...))
    pass


def downgrade() -> None:
    # This is the reverse operation of upgrade().
    # e.g., op.drop_table('users')
    pass
