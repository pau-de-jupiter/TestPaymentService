from typing import Protocol

from app.domain.payment.entities import Payment
from app.application.payment.commands import (
    CommandCreatePayment,
    CommandUpdatePaymentStatus,
)
from app.application.payment.queries import GetPaymentById


class AbstractPaymentRepo(Protocol):
    '''Интерфейс репозитория платежей
    Домен описывает контракт — что нужно уметь делать'''

    async def create(self, data: CommandCreatePayment) -> Payment:
        ...

    async def get_by_id(self, query: GetPaymentById) -> Payment | None:
        ...

    async def get_by_idempotency_key(self, key: str) -> Payment | None:
        ...

    async def update_status(self, data: CommandUpdatePaymentStatus) -> Payment:
        ...
