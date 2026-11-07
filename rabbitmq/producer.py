import asyncio
from loguru import logger

from sqlalchemy import select
from sqlalchemy.orm import load_only, selectinload

from application.core.db.models import OutboxAction, ActionType, Payment
from application.core.db.session import async_session_maker
from application.rabbitmq.broker import broker, new_payments_queue, dead_letter_queue


async def send_payment_to_queue() -> None:
    async with async_session_maker() as session:
        async with session.begin():
            result = await session.scalars(
                select(OutboxAction)
                .options(
                    load_only(
                        OutboxAction.payment_id,
                        OutboxAction.repeat_count,
                    ),
                    selectinload(OutboxAction.payment).load_only(
                        Payment.processing_attempts,
                    ),
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
                async with broker:
                    for action in actions:
                        await broker.publish(
                            message={
                                "payment_id": action.payment_id,
                                "processing_attempts": action.payment.processing_attempts,
                            },
                            queue=new_payments_queue if action.repeat_count < 3 else dead_letter_queue,
                        )
                        action.is_published = True
            except Exception as e:
                logger.error(f"Error on send message to queue {new_payments_queue}: {e}")
                unsend_actions.extend(action for action in actions if not action.is_published)

            for action in unsend_actions:
                action.repeat_count += 1



if __name__ == "__main__":
    async def main() -> None:
        await send_payment_to_queue()

    asyncio.run(main())