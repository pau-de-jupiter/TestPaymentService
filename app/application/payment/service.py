from app.domain.payment.entities import Payment
from app.domain.payment.repository import AbstractPaymentRepo
from app.domain.outbox.repository import AbstractOutboxRepo
from app.domain.payment.exceptions import PaymentNotFound
from app.application.payment.commands import (
    CommandCreatePayment,
    CommandCreateOutboxEvent,
)
from app.application.payment.queries import GetPaymentById


class PaymentService:
    def __init__(
        self,
        payment_repo: AbstractPaymentRepo,
        outbox_repo: AbstractOutboxRepo,
    ) -> None:
        self._payment_repo = payment_repo
        self._outbox_repo = outbox_repo

    async def create_payment(self, data: CommandCreatePayment) -> Payment:
        '''Создать платеж.

        В одной транзакции:
        1. Проверить idempotency_key — если уже есть, вернуть существующий.
        2. Сохранить платеж со статусом pending.
        3. Записать событие в Outbox (гарантия доставки в RabbitMQ).
        '''
        existing = await self._payment_repo.get_by_idempotency_key(
            data.idempotency_key
        )
        if existing is not None:
            return existing

        payment = await self._payment_repo.create(data=data)

        outbox_cmd = CommandCreateOutboxEvent(
            payment_id=payment.id,
            payload={
                'payment_id': str(payment.id),
                'amount': str(payment.amount),
                'currency': payment.currency,
                'webhook_url': payment.webhook_url,
                'description': payment.description,
            },
        )
        await self._outbox_repo.create(data=outbox_cmd)

        return payment

    async def get_payment(self, query: GetPaymentById) -> Payment:
        '''Получить платеж по ID. Если не найден — PaymentNotFound.'''
        payment = await self._payment_repo.get_by_id(query=query)
        if payment is None:
            raise PaymentNotFound(payment_id=str(query.payment_id))
        return payment
