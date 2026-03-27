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
