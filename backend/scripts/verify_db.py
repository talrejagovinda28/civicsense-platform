"""Verify complaint module database models and optional live DB connection."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as: py scripts/verify_db.py
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import create_engine, func, inspect, select, text  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models import Category, Complaint, ComplaintImage  # noqa: F401, E402

EXPECTED_TABLES = {"categories", "complaints", "complaint_images"}


def verify_metadata() -> None:
    tables = set(Base.metadata.tables.keys())
    missing = EXPECTED_TABLES - tables

    if missing:
        raise SystemExit(f"Missing tables in metadata: {missing}")

    print("Metadata OK — tables registered:")
    for name in sorted(EXPECTED_TABLES):
        table = Base.metadata.tables[name]
        columns = [col.name for col in table.columns]
        print(f"  {name}: {', '.join(columns)}")


def verify_live_db() -> None:
    live_engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
    )

    with live_engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    inspector = inspect(live_engine)
    existing = set(inspector.get_table_names())
    missing = EXPECTED_TABLES - existing
    if missing:
        raise SystemExit(
            f"DB connected but tables missing: {missing}. Run: alembic upgrade head"
        )

    db = SessionLocal()
    try:
        count = db.scalar(select(func.count()).select_from(Category)) or 0
        print(f"Live DB OK — {count} categories seeded")
        if count < 7:
            print("  WARNING: expected 7 Pune categories")
        categories = db.scalars(select(Category).order_by(Category.slug)).all()
        for category in categories:
            print(f"  - {category.slug}: {category.name} ({category.id})")
    finally:
        db.close()


if __name__ == "__main__":
    verify_metadata()
    if "--live" not in sys.argv:
        print("\nMetadata-only check passed.")
        print("After configuring .env, run:")
        print("  py -m alembic upgrade head")
        print("  py scripts/verify_db.py --live")
        sys.exit(0)

    try:
        verify_live_db()
    except Exception as exc:
        print(f"\nLive DB check failed: {exc}")
        print("Ensure DATABASE_URL is set and run: alembic upgrade head")
        sys.exit(1)
