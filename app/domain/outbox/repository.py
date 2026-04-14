from typing import Protocol
from uuid import UUID

from app.domain.outbox.entities import OutboxEvent
from app.application.payment.commands import CommandCreateOutboxEvent


class AbstractOutboxRepo(Protocol):
    '''Интерфейс репозитория Outbox
    Домен описывает контракт — что нужно уметь делать'''

    async def create(self, data: CommandCreateOutboxEvent) -> OutboxEvent:
        ...

    async def get_pending(self, batch_size: int) -> list[OutboxEvent]:
        '''Получить непубликованные события'''
        ...

    async def mark_published(self, event_id: UUID) -> None:
        '''Пометить событие как опубликованное'''
        ...

    async def increment_retry(self, event_id: UUID) -> int:
        '''Увеличить счетчик попыток. Возвращает новое значение'''
        ...

    async def mark_failed(self, event_id: UUID) -> None:
        ...
