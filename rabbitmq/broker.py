import os

from faststream.rabbit import RabbitBroker, RabbitQueue, RabbitExchange, ExchangeType
from faststream.rabbit.schemas.queue import ClassicQueueArgs

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

broker = RabbitBroker(url=RABBITMQ_URL)

# Обменники
main_exchange = RabbitExchange("payments.exchange", type=ExchangeType.DIRECT)
dlx_exchange = RabbitExchange("payments.dlx", type=ExchangeType.DIRECT)


# Основная очередь: при reject(requeue=False) уходит в DLX с key "retry"
new_payments_queue = RabbitQueue(
    "payments.new",
    durable=True,
    routing_key="payments.new",
    arguments=ClassicQueueArgs(
        **{
            "x-dead-letter-exchange": "payments.dlx",
            "x-dead-letter-routing-key": "retry",
        }
    ),
)

# Retry-очереди с нарастающим TTL (экспонента)
retry_queues = {
    1: RabbitQueue(
        "payments.retry.1", durable=True, routing_key="retry.1",
        arguments=ClassicQueueArgs(
            **{
                "x-message-ttl": 5000,
                "x-dead-letter-exchange": "payments.dlx",
                "x-dead-letter-routing-key": "payments.new",
            }
        ),
    ),
    2: RabbitQueue(
        "payments.retry.2", durable=True, routing_key="retry.2",
        arguments=ClassicQueueArgs(
            **{
                "x-message-ttl": 25000,
                "x-dead-letter-exchange": "payments.dlx",
                "x-dead-letter-routing-key": "payments.new",
            }
        ),
    ),
    3: RabbitQueue(
        "payments.retry.3", durable=True, routing_key="retry.3",
        arguments=ClassicQueueArgs(
            **{
                "x-message-ttl": 125000,
                "x-dead-letter-exchange": "payments.dlx",
                "x-dead-letter-routing-key": "payments.new",
            }
        ),
    ),
}

# Финальный DLQ (тупик, без DLX и TTL)
dead_letter_queue = RabbitQueue("payments.dead_letter.new", durable=True)


