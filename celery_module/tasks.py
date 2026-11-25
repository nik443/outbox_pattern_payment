import asyncio
from celery import shared_task

from application.rabbitmq.producer import send_payment_to_queue


@shared_task
def check_outbox_actions():
    asyncio.run(send_payment_to_queue())
