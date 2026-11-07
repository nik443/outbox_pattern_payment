import asyncio
import aiohttp
from datetime import datetime
from time import sleep
from random import randint, uniform

from sqlalchemy import update, select

from application.core.db.models import Payment, PaymentStatus
from application.core.db.session import async_session_maker
from application.rabbitmq.broker import broker, new_payments_queue


@broker.subscriber(new_payments_queue)
async def process_payment_process(body: dict):
    sleep(randint(2, 5))
    is_success = uniform(0.01, 1) > 0.1

    if is_success:
        updated_value = {"status": PaymentStatus.succeeded, "processed_at": datetime.now()}
    else:
        updated_value = {"processing_attempts": body.get("processing_attempts", 0) + 1}

    async with async_session_maker() as session:
        result = await session.execute(
            select(Payment).where(Payment.id == body.get("payment_id"))
        )
        payment = result.scalar_one_or_none()
        if not payment:
            return

        await session.execute(
            update(Payment)
            .where(Payment.id == body.get("payment_id"))
            .values(**updated_value)
        )
        await session.commit()

        async with aiohttp.ClientSession() as http_session:
            async with http_session.post(payment.webhook_url) as response:
                response.raise_for_status()


async def main():
    async with broker:
        print("Message wait")
        await broker.start()


if __name__ == "__main__":
    asyncio.run(main())