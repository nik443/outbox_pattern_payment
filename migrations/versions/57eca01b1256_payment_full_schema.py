"""payment full schema

Revision ID: 57eca01b1256
Revises: 430bb7255c72
Create Date: 2026-10-25 16:50:59.524658

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '57eca01b1256'
down_revision: Union[str, Sequence[str], None] = '430bb7255c72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


currency_enum = postgresql.ENUM('rub', 'usd', 'eur', name='currency_types_enum')
status_enum = postgresql.ENUM('pending', 'succeeded', 'failed', name='payment_status_enum')


def upgrade() -> None:
    """Upgrade schema."""
    currency_enum.create(op.get_bind(), checkfirst=True)
    status_enum.create(op.get_bind(), checkfirst=True)

    op.add_column('payments', sa.Column('currency', currency_enum, nullable=False))
    op.add_column('payments', sa.Column('description', sa.String(length=255), nullable=True))
    op.add_column('payments', sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('payments', sa.Column('status', status_enum, server_default='pending', nullable=False))
    op.add_column('payments', sa.Column('idempotency_key', sa.UUID(), nullable=False))
    op.add_column('payments', sa.Column('webhook_url', sa.Text(), nullable=False))
    op.add_column('payments', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('payments', sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True))
    op.create_unique_constraint('uq_payments_idempotency_key', 'payments', ['idempotency_key'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_payments_idempotency_key', 'payments', type_='unique')
    op.drop_column('payments', 'processed_at')
    op.drop_column('payments', 'created_at')
    op.drop_column('payments', 'webhook_url')
    op.drop_column('payments', 'idempotency_key')
    op.drop_column('payments', 'status')
    op.drop_column('payments', 'metadata')
    op.drop_column('payments', 'description')
    op.drop_column('payments', 'currency')

    status_enum.drop(op.get_bind(), checkfirst=True)
    currency_enum.drop(op.get_bind(), checkfirst=True)
