import os

from faststream.rabbit import RabbitBroker, RabbitQueue


broker = RabbitBroker(url=os.environ.get("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/"))
new_payments_queue = RabbitQueue("payments.new")
dead_letter_queue = RabbitQueue("payments.dead_letter.new")
