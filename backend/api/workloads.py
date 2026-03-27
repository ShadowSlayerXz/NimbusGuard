"""Workload routes — CRUD operations."""

from __future__ import annotations

import uuid
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api import ok, err
from backend.db.session import get_db
from backend.models.workload import Workload
from backend.schemas.workload import WorkloadCreate, WorkloadRead, WorkloadUpdate

router = APIRouter(prefix="/api/workloads", tags=["workloads"])


@router.get("")
async def list_workloads(db: AsyncSession = Depends(get_db)):
    stmt = select(Workload)
    rows = (await db.execute(stmt)).scalars().all()
    return ok([WorkloadRead.model_validate(r).model_dump(mode="json") for r in rows])


@router.get("/{workload_id}")
async def get_workload(workload_id: UUID, db: AsyncSession = Depends(get_db)):
    wl = await db.get(Workload, workload_id)
    if not wl:
        return err("Workload not found")
    return ok(WorkloadRead.model_validate(wl).model_dump(mode="json"))


@router.post("")
async def create_workload(body: WorkloadCreate, db: AsyncSession = Depends(get_db)):
    wl = Workload(id=uuid.uuid4(), **body.model_dump())
    db.add(wl)
    await db.commit()
    await db.refresh(wl)
    return ok(WorkloadRead.model_validate(wl).model_dump(mode="json"))


@router.patch("/{workload_id}")
async def update_workload(
    workload_id: UUID,
    body: WorkloadUpdate,
    db: AsyncSession = Depends(get_db),
):
    wl = await db.get(Workload, workload_id)
    if not wl:
        return err("Workload not found")

    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(wl, field, value)

    await db.commit()
    await db.refresh(wl)
    return ok(WorkloadRead.model_validate(wl).model_dump(mode="json"))


@router.delete("/{workload_id}")
async def delete_workload(workload_id: UUID, db: AsyncSession = Depends(get_db)):
    wl = await db.get(Workload, workload_id)
    if not wl:
        return err("Workload not found")
    await db.delete(wl)
    await db.commit()
    return ok({"deleted": True})
