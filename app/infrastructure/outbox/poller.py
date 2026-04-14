import asyncio
import logging
from uuid import UUID

from app.config import settings
from app.domain.payment.value_objects import PaymentStatus
from app.domain.outbox.entities import OutboxEvent
from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.database.repositories.outbox import OutboxRepo
from app.infrastructure.database.repositories.payment import PaymentRepo
from app.application.payment.commands import CommandUpdatePaymentStatus
from app.infrastructure.broker.connection import broker, payments_exchange, payments_queue

logger = logging.getLogger(__name__)

MAX_OUTBOX_RETRIES = 3


async def run_outbox_poller() -> None:
    '''Фоновый таск: читает unpublished события из БД и публикует в RabbitMQ.
    Запускается один раз в lifespan FastAPI.
    '''
    logger.info('Outbox poller started')

    while True:
        try:
            await _process_batch()
        except Exception:
            logger.exception('Outbox poller iteration failed')
        finally:
            await asyncio.sleep(settings.outbox_poll_interval)


async def _process_batch() -> None:
    async with AsyncSessionLocal() as session:
        events = await OutboxRepo(session).get_pending(batch_size=10)
        await session.commit()

    for event in events:
        await _process_event(event)


async def _process_event(event: OutboxEvent) -> None:
    try:
        await broker.publish(
            message=event.payload,
            queue=payments_queue,
            exchange=payments_exchange,
        )
        await _mark_published(event.id)
        logger.info('Outbox event published: event_id=%s payment_id=%s', event.id, event.payment_id)

    except Exception:
        logger.exception('Failed to publish outbox event: event_id=%s', event.id)
        await _handle_failure(event)


async def _mark_published(event_id: UUID) -> None:
    async with AsyncSessionLocal() as session:
        await OutboxRepo(session).mark_published(event_id=event_id)
        await session.commit()


async def _handle_failure(event: OutboxEvent) -> None:
    '''Инкремент ретраев при ошибках'''
    async with AsyncSessionLocal() as session:
        retry_count = await OutboxRepo(session).increment_retry(event_id=event.id)
        await session.commit()

    logger.warning(
        'Outbox event publish failed, retry %d/%d: event_id=%s',
        retry_count, MAX_OUTBOX_RETRIES, event.id,
    )

    if retry_count < MAX_OUTBOX_RETRIES:
        return

    async with AsyncSessionLocal() as session:
        await OutboxRepo(session).mark_failed(event_id=event.id)
        await PaymentRepo(session).update_status(
            CommandUpdatePaymentStatus(
                payment_id=event.payment_id,
                status=PaymentStatus.FAILED,
            )
        )
        await session.commit()

    logger.error(
        'Outbox event permanently failed, payment marked as failed: '
        'event_id=%s payment_id=%s',
        event.id, event.payment_id,
    )
