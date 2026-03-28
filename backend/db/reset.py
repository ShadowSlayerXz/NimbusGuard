"""Reset database — drop all tables, recreate, and reseed.

Run:  docker-compose exec backend python -m backend.db.reset
"""

from __future__ import annotations

import asyncio
import subprocess
import sys


async def reset() -> None:
    print("=== NimbusGuard DB Reset ===")

    # 1. Drop all tables via Alembic
    print("Running: alembic downgrade base")
    r1 = subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "base"],
        capture_output=True, text=True,
    )
    if r1.returncode != 0:
        print(f"alembic downgrade failed:\n{r1.stderr}")
        # Fallback: try to proceed anyway
    else:
        print("Tables dropped.")

    # 2. Recreate all tables via Alembic
    print("Running: alembic upgrade head")
    r2 = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True, text=True,
    )
    if r2.returncode != 0:
        print(f"alembic upgrade failed:\n{r2.stderr}")
        sys.exit(1)
    print("Tables recreated.")

    # 3. Run seed
    print("Running seed...")
    from backend.db.seed import seed
    await seed()

    print()
    print("=== Reset complete ===")


if __name__ == "__main__":
    asyncio.run(reset())
