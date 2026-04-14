from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_session
from app.infrastructure.database.repositories.payment import PaymentRepo
from app.infrastructure.database.repositories.outbox import OutboxRepo
from app.application.payment.service import PaymentService


async def get_payment_service(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[PaymentService, None]:
    '''Используется Unit of Work для управления транзакции
    Payment + OutboxEvent сохраняются в одной транзакции:
    - commit  — если хендлер завершился без исключений
    - rollback — если хендлер выбросил исключение
    '''
    payment_repo = PaymentRepo(session=session)
    outbox_repo = OutboxRepo(session=session)
    service = PaymentService(payment_repo=payment_repo, outbox_repo=outbox_repo)

    try:
        yield service
        await session.commit()
    except Exception:
        await session.rollback()
        raise
