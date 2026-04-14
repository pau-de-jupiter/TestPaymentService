from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

from app.config import settings


engine = create_async_engine(
    url=settings.psql_db.dsn,
    pool_size=settings.psql_db.min_pool_size,
    max_overflow=settings.psql_db.max_pool_size - settings.psql_db.min_pool_size,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
