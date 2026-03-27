"""Alembic env.py — async migration runner for NimbusGuard.

Imports all models via backend.models so that autogenerate detects them.
Reads DATABASE_URL from the environment (falls back to alembic.ini value).
"""

import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# ---------------------------------------------------------------------------
# Ensure imports resolve correctly in both contexts:
#   1. From repo root:  `backend.models.base`  (backend/ is a package)
#   2. Inside container: `/app` is the backend, so we add `/app/..`
#      but that would look for backend/ outside.  Instead we add /app
#      as a fallback and also try a direct import.
# ---------------------------------------------------------------------------
# Add the repo root (parent of backend/) so `backend.models` resolves.
_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

# Also add the container workdir parent in case we're inside Docker
# where /app = backend contents.  We create a synthetic `backend` by
# treating /app/.. as the root.
_container_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _container_root not in sys.path:
    sys.path.insert(0, _container_root)

# Import all models so Base.metadata is fully populated
from backend.models import Base  # noqa: E402

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata

# Override sqlalchemy.url with DATABASE_URL env var when available
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — emit SQL to stdout."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Helper executed inside the async connection context."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations."""
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
