import pytest
import pytest_asyncio
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.app.db.base_class import Base
from backend.app.services.cache import redis_client

import backend.app.models
from backend.app.core.config import settings

DATABASE_URL_TEST = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:"
    f"{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:"
    f"{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

engine = create_async_engine(DATABASE_URL_TEST, echo=False)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session(setup_db):
    async with TestingSessionLocal() as session:
        async with session.begin_nested():
            try:
                yield session
            finally:
                await session.rollback()

@pytest_asyncio.fixture(autouse=True)
async def clean_redis():
    await redis_client.flushdb()