import asyncio
import logging
from uuid import UUID

from faststream.rabbit import RabbitMessage

from app.domain.payment.value_objects import PaymentStatus
from app.application.payment.commands import CommandUpdatePaymentStatus
from app.infrastructure.database.session import AsyncSessionLocal
from app.infrastructure.database.repositories.payment import PaymentRepo
from app.infrastructure.broker.connection import (
    broker,
    payments_exchange,
    payments_queue,
    dlx,
    dlq,
)
from app.entrypoints.amqp.gateway import process_payment
from app.entrypoints.amqp.webhook import send_webhook

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


@broker.subscriber(payments_queue, exchange=payments_exchange)
async def handle_payment(body: dict, message: RabbitMessage) -> None:
    '''Consumer платежей
    Шлюз: однократный вызов, результат — бизнес-решение (не ретраим)
    Retry только для инфраструктурных сбоев при сохранении статуса в БД
    '''
    payment_id: str = body['payment_id']
    webhook_url: str = body['webhook_url']

    # Шаг 1: эмуляция шлюза
    # False (10%) = платеж отклонен — это бизнес-результат, не исключение
    # Ретраить не нужно: повторный вызов шлюза даст новый случайный результат
    success = await process_payment(payment_id=payment_id)
    new_status = PaymentStatus.SUCCEEDED if success else PaymentStatus.FAILED

    # Шаг 2: сохранить статус в БД
    # Инфраструктурная операция — может упасть - - retry - - DLQ
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            await _update_payment_status(UUID(payment_id), new_status)
            break
        except Exception:
            logger.exception(
                'Failed to update payment status, attempt %d/%d: payment_id=%s',
                attempt, MAX_RETRIES, payment_id,
            )
            if attempt == MAX_RETRIES:
                await _send_to_dlq(body=body, payment_id=payment_id)
                await message.ack()
                return
            await asyncio.sleep(2 ** (attempt - 1))

    # Шаг 3: Отправка webhook. URL, что привязан в платеж
    # Не роняем consumer если webhook недоступен — платеж уже обработан и сохранен
    await send_webhook(
        webhook_url=webhook_url,
        payload={'payment_id': payment_id, 'status': new_status},
    )

    await message.ack()


async def _update_payment_status(payment_id: UUID, status: PaymentStatus) -> None:
    async with AsyncSessionLocal() as session:
        await PaymentRepo(session).update_status(
            CommandUpdatePaymentStatus(payment_id=payment_id, status=status)
        )
        await session.commit()


async def _send_to_dlq(body: dict, payment_id: str) -> None:
    '''Явная отправка в DLQ + пометить платеж как failed'''
    try:
        await broker.publish(message=body, queue=dlq, exchange=dlx)
        await _update_payment_status(UUID(payment_id), PaymentStatus.FAILED)
        logger.error(
            'Payment moved to DLQ after %d failed DB attempts: payment_id=%s',
            MAX_RETRIES, payment_id,
        )
    except Exception:
        logger.exception('Failed to send payment to DLQ: payment_id=%s', payment_id)
