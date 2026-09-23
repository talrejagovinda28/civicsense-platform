"""Runtime DB schema helpers for additive V3 migrations.

Production may briefly run V3 code before alembic 009/010 is applied.
Callers should degrade gracefully instead of 500'ing public reads.
"""

from __future__ import annotations

from sqlalchemy import inspect
from sqlalchemy.orm import Session, load_only

_column_cache: dict[tuple[int, str, str], frozenset[str]] = {}


def _bind_key(db: Session) -> tuple[int, str]:
    bind = db.get_bind()
    return (id(bind), str(getattr(bind, "url", "unknown")))


def table_exists(db: Session, table_name: str) -> bool:
    return inspect(db.get_bind()).has_table(table_name)


def table_columns(db: Session, table_name: str) -> frozenset[str]:
    key = (*_bind_key(db), table_name)
    cached = _column_cache.get(key)
    if cached is not None:
        return cached
    bind = db.get_bind()
    if not inspect(bind).has_table(table_name):
        cols: frozenset[str] = frozenset()
    else:
        cols = frozenset(column["name"] for column in inspect(bind).get_columns(table_name))
    _column_cache[key] = cols
    return cols


def has_column(db: Session, table_name: str, column_name: str) -> bool:
    return column_name in table_columns(db, table_name)


def complaints_v3_ready(db: Session) -> bool:
    """True when migration 009 complaint columns exist."""
    return has_column(db, "complaints", "is_sensitive")


def complaint_images_v3_ready(db: Session) -> bool:
    return has_column(db, "complaint_images", "visibility")


def social_tables_ready(db: Session) -> bool:
    return (
        table_exists(db, "likes")
        and table_exists(db, "affected")
        and table_exists(db, "comments")
    )


def clear_schema_cache() -> None:
    _column_cache.clear()


def load_only_existing(model: type, column_names: frozenset[str]):
    """Build load_only() for mapped attrs that exist as DB columns."""
    attrs = [
        getattr(model, name)
        for name in column_names
        if hasattr(model, name)
    ]
    if not attrs:
        return None
    return load_only(*attrs)
