from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from application.core import ActionType
from application.core.db.models import Payment, OutboxAction
from application.core.db.schemas import PaymentCreatedRead, PaymentBaseRead, PaymentCreate
from application.core.db.session import get_session


api_router = APIRouter()

@api_router.post(
    "/api/v1/payments/",
    response_model=PaymentCreatedRead,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_payment(
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: Annotated[
        UUID,
        Header(alias="Idempotency-Key", examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"]),
    ],
    payment: PaymentCreate,
):
    payment = Payment(idempotency_key=idempotency_key, **payment.model_dump())
    outbox_action = OutboxAction(payment=payment, action_type=ActionType.create)
    session.add_all([payment, outbox_action])
    await session.commit()
    return payment


@api_router.get("/api/v1/payments/{payment_id}", response_model=PaymentBaseRead)
async def read_payment(
    session: Annotated[AsyncSession, Depends(get_session)],
    payment_id: int,
):
    payment = await session.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment