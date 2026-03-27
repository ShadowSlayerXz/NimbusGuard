# NimbusGuard — Build Log

> This file tracks the outcome of every task. Append new entries at the bottom.

---

## Task 1 — Project Scaffold
**Status**: ✅ Complete
**Date**: 2026-03-28

### Files Created
- docker-compose.yml
- .env.example
- .env (copy of .env.example for local dev)
- .gitignore
- backend/main.py
- backend/db/session.py
- backend/db/__init__.py
- backend/__init__.py
- backend/requirements.txt
- backend/Dockerfile
- backend/.dockerignore
- frontend/src/app/page.tsx (placeholder)
- frontend/Dockerfile
- frontend/.dockerignore
- logs/build.md

### Test Results
- [x] docker-compose up --build → success
- [x] GET /health → { "data": { "status": "ok" }, "error": null, "timestamp": "..." } → success
- [x] Frontend loads at localhost:3000 → success (NimbusGuard heading displayed)

### Errors Encountered
**Error**: `port is already allocated for 0.0.0.0:5432`
**File**: docker-compose.yml (postgres service)
**Fix Applied**: Stopped conflicting `hms_db` container that was occupying port 5432
**Fix Status**: Resolved

**Error**: `the attribute 'version' is obsolete` (Docker Compose warning)
**File**: docker-compose.yml
**Fix Applied**: Removed `version: "3.9"` line from docker-compose.yml
**Fix Status**: Resolved

### Notes
- Used `--src-dir` flag with create-next-app; pages live under `frontend/src/app/`
  rather than `frontend/app/`. This is the standard Next.js 14+ convention.
- Tailwind CSS v4 was installed by create-next-app (latest default).
- All 4 containers running: nimbusguard-postgres, nimbusguard-redis,
  nimbusguard-backend, nimbusguard-frontend.
- TimescaleDB extension confirmed present in postgres container.

---

## Task 2 — Database Models + Migrations
**Status**: ✅ Complete
**Date**: 2026-03-28

### Files Created
- backend/models/__init__.py
- backend/models/base.py
- backend/models/risk_event.py
- backend/models/region_risk_score.py
- backend/models/workload.py
- backend/models/simulation_result.py
- backend/models/migration_log.py
- backend/db/migrations/env.py
- backend/db/migrations/script.py.mako
- backend/db/migrations/versions/add5f11b634a_initial_schema.py
- backend/db/migrations/versions/.gitkeep
- backend/alembic.ini (Docker)
- alembic.ini (local dev)

### Test Results
- [x] alembic upgrade head → success
- [x] all 5 tables present in postgres → success (risk_events, region_risk_scores, workloads, simulation_results, migration_logs)
- [x] region_risk_scores is a hypertable → success (1 dimension on computed_at)

### Errors Encountered
**Error**: `cannot create a unique index without the column "computed_at" (used in partitioning)`
**File**: backend/models/region_risk_score.py + migration file
**Fix Applied**: Changed PK to composite `(id, computed_at)` — TimescaleDB requires the partitioning column in the primary key
**Fix Status**: Resolved

**Error**: `socket.gaierror: No address associated with hostname`
**File**: backend/alembic.ini
**Fix Applied**: Changed default sqlalchemy.url hostname from `localhost` to `postgres` (Docker service name)
**Fix Status**: Resolved

### Notes
- Separated `Base` into `backend/models/base.py` to avoid circular imports
  between `__init__.py` (which re-exports models) and models (which import Base).
- Backend Dockerfile restructured to copy code into `/app/backend/` so
  `backend.*` import paths work identically in Docker and locally.
- Two alembic.ini files: root (localhost, for local dev) and backend/ (postgres hostname, for Docker).

