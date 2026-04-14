from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update

from app.domain.payment.entities import Payment
from app.application.payment.commands import CommandCreatePayment, CommandUpdatePaymentStatus
from app.application.payment.queries import GetPaymentById
from app.infrastructure.database.models import Payment as PaymentORM


class PaymentRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: CommandCreatePayment) -> Payment:
        stmt = (
            insert(PaymentORM)
            .values(**self._to_orm(data))
            .returning(PaymentORM)
        )
        result = await self._session.execute(stmt)
        return self._to_domain(result.scalar_one())

    async def get_by_id(self, query: GetPaymentById) -> Payment | None:
        stmt = select(PaymentORM).where(PaymentORM.id == query.payment_id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_by_idempotency_key(self, key: str) -> Payment | None:
        stmt = select(PaymentORM).where(PaymentORM.idempotency_key == key)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def update_status(self, data: CommandUpdatePaymentStatus) -> Payment:
        stmt = (
            update(PaymentORM)
            .where(PaymentORM.id == data.payment_id)
            .values(status=data.status, processed_at=datetime.now(timezone.utc))
            .returning(PaymentORM)
        )
        result = await self._session.execute(stmt)
        return self._to_domain(result.scalar_one())

    def _to_orm(self, data: CommandCreatePayment) -> dict:
        return {
            'idempotency_key': data.idempotency_key,
            'amount': data.amount,
            'currency': data.currency,
            'description': data.description,
            'metadata_': data.metadata,
            'webhook_url': data.webhook_url,
        }

    def _to_domain(self, orm: PaymentORM) -> Payment:
        return Payment(
            id=orm.id,
            idempotency_key=orm.idempotency_key,
            amount=orm.amount,
            currency=orm.currency,
            description=orm.description,
            metadata=orm.metadata_,
            status=orm.status,
            webhook_url=orm.webhook_url,
            created_at=orm.created_at,
            processed_at=orm.processed_at,
        )
