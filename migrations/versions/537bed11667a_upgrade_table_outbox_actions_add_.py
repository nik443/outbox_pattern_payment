"""upgrade table outbox_actions: add columns created_at is_published

Revision ID: 537bed11667a
Revises: 098a96a3eff8
Create Date: 2026-11-01 13:29:50.962260

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '537bed11667a'
down_revision: Union[str, Sequence[str], None] = '098a96a3eff8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
