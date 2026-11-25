from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Enum as SAEnum, String, DateTime, func, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column, relationship

from application.core.db.base import Base


class CurrencyType(StrEnum):
    rub = "rub"
    usd = "usd"
    eur = "eur"


class PaymentStatus(StrEnum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"


class ActionType(StrEnum):
    create = "create"
    delete = "delete"


class Payment(Base):
    __tablename__ = "payments"

    currency: Mapped[CurrencyType] = mapped_column(
        SAEnum(CurrencyType, name="currency_types_enum"),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    metadata_: Mapped[dict | None] = mapped_column(
        MutableDict.as_mutable(JSONB),
        name="metadata",
        nullable=True,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, name="payment_status_enum"),
        nullable=False,
        default=PaymentStatus.pending,
        server_default=PaymentStatus.pending.value,
    )
    idempotency_key: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        unique=True,
        nullable=False,
    )
    webhook_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )


class OutboxAction(Base):
    __tablename__ = "outbox_actions"
    __table_args__ = (
        Index(
            "ix_outbox_unpublished_created",
            "is_published",
            "created_at",
        ),
    )

    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payment: Mapped[Payment] = relationship()
    action_type: Mapped[ActionType] = mapped_column(
        SAEnum(ActionType, name="action_type_enum"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    is_published: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
