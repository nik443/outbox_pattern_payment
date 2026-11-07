from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from application.core.db.models import CurrencyType, PaymentStatus


class PaymentBase(BaseModel):
    status: PaymentStatus


class PaymentCreate(PaymentBase):
    currency: CurrencyType
    description: str
    metadata_: dict | None
    status: PaymentStatus
    webhook_url: str


class PaymentCreatedRead(PaymentBase):
    model_config = ConfigDict(from_attributes=True)

    payment_id: int = Field(validation_alias="id")
    created_at: datetime


class PaymentBaseRead(PaymentBase):
    model_config = ConfigDict(from_attributes=True)

    payment_id: int = Field(validation_alias="id")
    currency: CurrencyType
    description: str | None
    metadata: dict | None = Field(validation_alias="metadata_")
    status: PaymentStatus
    idempotency_key: UUID
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None