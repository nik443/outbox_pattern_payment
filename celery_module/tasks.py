import asyncio
from datetime import datetime
from time import sleep

from aiohttp import ClientSession
from loguru import logger

import aiohttp
from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import load_only, selectinload

from application.rabbitmq.producer import send_payment_to_queue
from application.core.db.models import Payment, PaymentStatus, OutboxAction
from application.core.db.session import async_session_maker


@shared_task
def check_outbox_actions():
    asyncio.run(send_payment_to_queue())


@shared_task
def send_success_payment_webhook():
    asyncio.run(async_send_success_payment_webhook())


async def async_send_success_payment_webhook():
    async with async_session_maker() as session:
        result = await session.scalars(
            select(OutboxAction)
            .join(OutboxAction.payment)
            .options(
                load_only(OutboxAction.payment_id),
                selectinload(OutboxAction.payment)
                .load_only(Payment.id, Payment.webhook_url, Payment.processed_at, Payment.status),
            )
            .where(
                OutboxAction.is_published.is_(True),
                Payment.status == PaymentStatus.pending,
            )
        )
        payments = [action.payment for action in result.all()]
        results = await send_webhook_bulk(payments)
        for payment, is_webhook_ok in zip(payments, results):
            if is_webhook_ok:
                payment.processed_at = datetime.now()
                payment.status = PaymentStatus.succeeded
        await session.commit()


async def send_webhook_bulk(payments: list[Payment]) -> list[bool]:
    async with aiohttp.ClientSession() as http_session:
        tasks = [
            asyncio.create_task(send_webhook(session=http_session, url=payment.webhook_url))
            for payment in payments
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)

async def send_webhook(session: ClientSession, url: str) -> bool:
    try:
        async with session.post(url) as response:
            sleep(1)
            return True
    except Exception as e:
        logger.warning(f"Failed to send webhook payment to {url}: {e}")
        return True
