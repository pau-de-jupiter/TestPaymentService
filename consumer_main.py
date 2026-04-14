import asyncio
import logging

from app.infrastructure.broker.connection import broker
from app.entrypoints.amqp import consumer  # noqa: F401 — registers @broker.subscriber

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    await broker.start()
    try:
        await asyncio.Future()
    finally:
        await broker.close()


if __name__ == '__main__':
    asyncio.run(main())
