import os

from faststream.rabbit import RabbitBroker, RabbitQueue, RabbitExchange, ExchangeType
from faststream.rabbit.schemas.queue import ClassicQueueArgs

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

broker = RabbitBroker(url=RABBITMQ_URL)

main_exchange = RabbitExchange("payments.exchange", type=ExchangeType.DIRECT)
retry_exchange = RabbitExchange("retry.exchange", type=ExchangeType.DIRECT)
dlx_exchange = RabbitExchange("payments.dlx", type=ExchangeType.DIRECT)


new_payments_queue = RabbitQueue(
    "payments.new",
    durable=True,
    routing_key="payments.new",
    arguments=ClassicQueueArgs(
        **{
            "x-dead-letter-exchange": "payments.dlx",
            "x-dead-letter-routing-key": "dead_letter",
        }
    ),
)

retry_queue_1 = RabbitQueue(
    "payments.retry.1",
    durable=True,
    routing_key="retry.1",
    arguments=ClassicQueueArgs(
        **{
            "x-message-ttl": 5000,
            "x-dead-letter-exchange": "payments.exchange",
            "x-dead-letter-routing-key": "payments.new",
        }
    ),
)
retry_queue_2 = RabbitQueue(
    "payments.retry.2",
    durable=True,
    routing_key="retry.2",
    arguments=ClassicQueueArgs(
        **{
            "x-message-ttl": 10000,
            "x-dead-letter-exchange": "payments.exchange",
            "x-dead-letter-routing-key": "payments.new",
        }
    ),
)
retry_queue_3 = RabbitQueue(
    "payments.retry.3",
    durable=True,
    routing_key="retry.3",
    arguments=ClassicQueueArgs(
        **{
            "x-message-ttl": 20000,
            "x-dead-letter-exchange": "payments.exchange",
            "x-dead-letter-routing-key": "payments.new",
        }
    ),
)

dead_letter_queue = RabbitQueue("payments.dead_letter.new", durable=True, routing_key="dead_letter")


