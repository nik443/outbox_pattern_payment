import asyncio
from datetime import datetime
from random import randint, uniform
from loguru import logger

import aiohttp
from faststream.rabbit import RabbitMessage
from sqlalchemy import update

from application.core.db.models import Payment, PaymentStatus
from application.core.db.session import async_session_maker
from application.rabbitmq.broker import broker, new_payments_queue, dead_letter_queue, dlx_exchange, retry_queue_1, \
    retry_queue_2, retry_queue_3, main_exchange, retry_exchange

MAX_RETRIES = 3


@broker.subscriber(new_payments_queue, exchange=main_exchange)
async def process_payment(body: dict, msg: RabbitMessage):
    attempts = msg.headers.get("x-retry-count", 0)
    logger.info(f"Payment {body.get("payment_id")}: processing")

    # Эмуляция обработки (async!)
    await asyncio.sleep(randint(2, 5))
    is_success = uniform(0.01, 1) > 0.5

    if is_success:
        logger.info(f"Payment {body.get("payment_id")} was processed successfully")
        await _mark_succeeded(body)
        try:
            await _send_webhook(body)
        except Exception:
            pass
        return

    logger.info(f"Payment {body.get("payment_id")} was processed failure")
    next_attempt = attempts + 1

    if next_attempt > MAX_RETRIES:
        await _mark_failed(body)
        await broker.publish(
            message=body,
            exchange=dlx_exchange,
            routing_key="dead_letter",
        )
        return

    await broker.publish(
        body,
        exchange=retry_exchange,
        routing_key=f"retry.{next_attempt}",
        headers={"x-retry-count": next_attempt},
    )


@broker.subscriber(dead_letter_queue, exchange=dlx_exchange)
async def process_dead_letter(body: dict, msg: RabbitMessage):
    logger.info(f"Process dead letter message {body}")


async def _mark_succeeded(body: dict) -> None:
    async with async_session_maker() as session:
        await session.execute(
            update(Payment)
            .where(Payment.id == body.get("payment_id"))
            .values(
                status=PaymentStatus.succeeded,
                processed_at=datetime.now(),
            )
        )
        await session.commit()


async def _mark_failed(body: dict) -> None:
    async with async_session_maker() as session:
        await session.execute(
            update(Payment)
            .where(Payment.id == body.get("payment_id"))
            .values(status=PaymentStatus.failed)
        )
        await session.commit()


async def _send_webhook(body: dict) -> None:
    async with async_session_maker() as session:
        payment = await session.get(Payment, body.get("payment_id"))
        if payment is None:
            return
        webhook_url = payment.webhook_url

    async with aiohttp.ClientSession() as http_session:
        async with http_session.post(webhook_url) as response:
            response.raise_for_status()


async def main():
    async with broker as broker_connection:
        await broker_connection.declare_queue(dead_letter_queue)

        await broker_connection.declare_exchange(dlx_exchange)

        # Явные привязки: declare_* возвращают aio_pika-объекты
        q1 = await broker_connection.declare_queue(retry_queue_1)
        q2 = await broker_connection.declare_queue(retry_queue_2)
        q3 = await broker_connection.declare_queue(retry_queue_3)
        retry_ex = await broker_connection.declare_exchange(retry_exchange)

        await q1.bind(retry_ex, routing_key="retry.1")
        await q2.bind(retry_ex, routing_key="retry.2")
        await q3.bind(retry_ex, routing_key="retry.3")
        print("Message wait")
        await broker_connection.start()


if __name__ == "__main__":
    asyncio.run(main())