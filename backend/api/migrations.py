"""Migration log routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api import ok, err
from backend.db.session import get_db
from backend.models.migration_log import MigrationLog
from backend.schemas.migration_log import MigrationLogRead

router = APIRouter(prefix="/api/migrations", tags=["migrations"])


@router.get("")
async def list_migrations(
    status: str | None = None,
    workload_id: UUID | None = None,
    limit: int = Query(default=50),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MigrationLog).order_by(desc(MigrationLog.created_at)).limit(limit)
    if status:
        stmt = stmt.where(MigrationLog.status == status)
    if workload_id:
        stmt = stmt.where(MigrationLog.workload_id == workload_id)

    rows = (await db.execute(stmt)).scalars().all()
    return ok([MigrationLogRead.model_validate(r).model_dump(mode="json") for r in rows])


@router.patch("/{migration_id}/approve")
async def approve_migration(migration_id: UUID, db: AsyncSession = Depends(get_db)):
    ml = await db.get(MigrationLog, migration_id)
    if not ml:
        return err("Migration not found")
    ml.status = "approved"
    await db.commit()
    await db.refresh(ml)
    return ok(MigrationLogRead.model_validate(ml).model_dump(mode="json"))


@router.patch("/{migration_id}/execute")
async def execute_migration(migration_id: UUID, db: AsyncSession = Depends(get_db)):
    ml = await db.get(MigrationLog, migration_id)
    if not ml:
        return err("Migration not found")
    ml.status = "executed"
    await db.commit()
    await db.refresh(ml)
    return ok(MigrationLogRead.model_validate(ml).model_dump(mode="json"))
