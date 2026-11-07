"""upgrade table payments: add column repeat_column

Revision ID: 098a96a3eff8
Revises: 2f530350059b
Create Date: 2026-11-01 13:23:01.573057

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '098a96a3eff8'
down_revision: Union[str, Sequence[str], None] = '2f530350059b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
