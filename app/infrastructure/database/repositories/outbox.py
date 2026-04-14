import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update, func

from app.domain.outbox.entities import OutboxEvent
from app.application.payment.commands import CommandCreateOutboxEvent
from app.infrastructure.database.models import OutboxEvent as OutboxEventORM

LOCK_TTL_SECONDS = 30


class OutboxRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: CommandCreateOutboxEvent) -> OutboxEvent:
        stmt = (
            insert(OutboxEventORM)
            .values(payment_id=data.payment_id, payload=data.payload)
            .returning(OutboxEventORM)
        )
        result = await self._session.execute(stmt)
        return self._to_domain(result.scalar_one())

    async def get_pending(self, batch_size: int = 10) -> list[OutboxEvent]:
        '''Claim-based locking: атомарно выбирает события и ставит locked_until.
        После закрытия сессии события остаются заблокированными до истечения TTL.
        Если poller упал — через 30 секунд события доступны снова.
        '''
        now = datetime.now(timezone.utc)
        lock_until = now + timedelta(seconds=LOCK_TTL_SECONDS)

        subquery = (
            select(OutboxEventORM.id)
            .where(OutboxEventORM.published.is_(False))
            .where(OutboxEventORM.failed.is_(False))
            .where(
                (OutboxEventORM.locked_until.is_(None)) |
                (OutboxEventORM.locked_until < now)
            )
            .order_by(OutboxEventORM.created_at)
            .limit(batch_size)
            .with_for_update(skip_locked=True)
            .scalar_subquery()
        )

        stmt = (
            update(OutboxEventORM)
            .where(OutboxEventORM.id.in_(subquery))
            .values(locked_until=lock_until)
            .returning(OutboxEventORM)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars().all()]

    async def mark_published(self, event_id: uuid.UUID) -> None:
        stmt = (
            update(OutboxEventORM)
            .where(OutboxEventORM.id == event_id)
            .values(published=True, locked_until=None)
        )
        await self._session.execute(stmt)

    async def increment_retry(self, event_id: uuid.UUID) -> int:
        '''Увеличить счётчик и выставить exponential backoff через locked_until
        Poller фильтрует locked_until < now — событие появится само в нужный момент.
        '''
        new_retry = OutboxEventORM.retry_count + 1
        stmt = (
            update(OutboxEventORM)
            .where(OutboxEventORM.id == event_id)
            .values(
                retry_count=new_retry,
                locked_until=func.now() + func.make_interval(0, 0, 0, 0, 0, 0, func.power(2, new_retry)),
            )
            .returning(OutboxEventORM.retry_count)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def mark_failed(self, event_id: uuid.UUID) -> None:
        stmt = (
            update(OutboxEventORM)
            .where(OutboxEventORM.id == event_id)
            .values(failed=True, locked_until=None)
        )
        await self._session.execute(stmt)

    def _to_domain(self, orm: OutboxEventORM) -> OutboxEvent:
        return OutboxEvent(
            id=orm.id,
            payment_id=orm.payment_id,
            payload=orm.payload,
            published=orm.published,
            failed=orm.failed,
            retry_count=orm.retry_count,
            locked_until=orm.locked_until,
        )
