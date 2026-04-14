from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue, ExchangeType

from app.config import settings

broker = RabbitBroker(url=settings.rabbitmq.dsn)

# Dead Letter Exchange
dlx = RabbitExchange(
    name='payments.dlx',
    type=ExchangeType.DIRECT,
    durable=True,
)

# Dead Letter Queue
dlq = RabbitQueue(
    name='payments.dead',
    routing_key='dead',
    durable=True,
    arguments={'x-queue-type': 'classic'},
)

# Основной exchange
payments_exchange = RabbitExchange(
    name='payments',
    type=ExchangeType.DIRECT,
    durable=True,
)

# Основная очередь:
payments_queue = RabbitQueue(
    name='payments.new',
    durable=True,
    arguments={
        'x-dead-letter-exchange': 'payments.dlx',
        'x-dead-letter-routing-key': 'dead',
        'x-queue-type': 'classic',
    },
)
