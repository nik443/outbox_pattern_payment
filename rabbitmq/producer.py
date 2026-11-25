import asyncio
from loguru import logger

from sqlalchemy import select
from sqlalchemy.orm import load_only, selectinload

from application.core.db.models import OutboxAction, ActionType, Payment
from application.core.db.session import async_session_maker
from application.rabbitmq.broker import broker, new_payments_queue, main_exchange


async def send_payment_to_queue() -> None:
    async with async_session_maker() as session:
        async with session.begin():
            result = await session.scalars(
                select(OutboxAction)
                .options(
                    load_only(
                        OutboxAction.payment_id,
                    ),
                    selectinload(OutboxAction.payment),
                )
                .where(
                    OutboxAction.is_published.is_(False),
                    OutboxAction.action_type == ActionType.create,
                )
                .order_by(OutboxAction.created_at.asc())
                .limit(100)
                .with_for_update(skip_locked=True)
            )
            actions = result.all()

            unsend_actions = []
            try:
                async with broker as broker_connection:
                    for action in actions:
                        await broker_connection.publish(
                            message={
                                "payment_id": action.payment_id,
                            },
                            exchange=main_exchange.name,
                            routing_key="payments.new",
                        )
                        action.is_published = True
            except Exception as e:
                logger.error(f"Error on send message to queue {new_payments_queue}: {e}")
                unsend_actions.extend(action for action in actions if not action.is_published)


async def main() -> None:
    async with broker as broker_connection:
        await broker_connection.declare_exchange(main_exchange)
        await broker_connection.declare_queue(new_payments_queue)
    await send_payment_to_queue()


if __name__ == "__main__":
    asyncio.run(main())