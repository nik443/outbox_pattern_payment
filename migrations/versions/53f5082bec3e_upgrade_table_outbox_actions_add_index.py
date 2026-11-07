"""upgrade table outbox_actions: add index

Revision ID: 53f5082bec3e
Revises: 9f19bf6f5c5c
Create Date: 2026-11-01 13:59:01.406185

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '53f5082bec3e'
down_revision: Union[str, Sequence[str], None] = '9f19bf6f5c5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
