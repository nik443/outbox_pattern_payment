import asyncio
from datetime import datetime
from random import randint, uniform

import aiohttp
from faststream.rabbit import RabbitMessage
from sqlalchemy import update

from application.core.db.models import Payment, PaymentStatus
from application.core.db.session import async_session_maker
from application.rabbitmq.broker import broker, new_payments_queue, dead_letter_queue, dlx_exchange


MAX_RETRIES = 3


@broker.subscriber(new_payments_queue)
async def process_payment(body: dict, msg: RabbitMessage):
    # 1. Номер текущей попытки из x-death (0 = первая)
    attempts = _get_attempts(msg)

    # 2. Эмуляция обработки (async!)
    await asyncio.sleep(randint(2, 5))
    is_success = uniform(0.01, 1) > 0.1

    if is_success:
        await _mark_succeeded(body)
        await _send_webhook(body)
        await msg.ack()
        return

    # 3. Неудача — инкремент счётчика в БД (для наблюдаемости)
    await _increment_attempts(body)

    next_attempt = attempts + 1

    if next_attempt > MAX_RETRIES:
        # Исчерпали попытки → финальный DLQ, статус failed
        await _mark_failed(body)
        await broker.publish(body, queue=dead_letter_queue)
        await msg.ack()          # убираем из основной очереди
        return

    # Иначе перекладываем в retry-очередь нужной «ступени» задержки
    await broker.publish(
        body,
        exchange=dlx_exchange,
        routing_key=f"retry.{next_attempt}",
    )
    await msg.ack()              # ответственность передана, исходное ack


def _get_attempts(msg: RabbitMessage) -> int:
    x_death = msg.headers.get("x-death") if msg.headers else None
    if not x_death:
        return 0
    return x_death[0].get("count", 0)


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


async def _increment_attempts(body: dict) -> None:
    async with async_session_maker() as session:
        await session.execute(
            update(Payment)
            .where(Payment.id == body.get("payment_id"))
            .values(processing_attempts=Payment.processing_attempts + 1)
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
    async with broker:
        print("Message wait")
        await broker.start()


if __name__ == "__main__":
    asyncio.run(main())