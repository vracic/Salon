from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings


# Convert a sync-style DSN to asyncpg-style for SQLAlchemy async engine
ASYNC_DATABASE_URL = (
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
)

engine = create_async_engine(ASYNC_DATABASE_URL, future=True, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
