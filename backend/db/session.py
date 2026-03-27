"""Async SQLAlchemy engine + session dependency for FastAPI."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://nimbusguard:nimbusguard@localhost:5432/nimbusguard",
)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def new_session():
    """Create a fresh engine+session — safe for Celery workers.

    Each call creates its own engine so there are no event-loop
    conflicts when called from different forked processes.
    """
    _engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    _factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    async with _factory() as session:
        try:
            yield session
        finally:
            await _engine.dispose()
