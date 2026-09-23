"""Feed must not 500 when migration 009 columns are absent."""

from __future__ import annotations

import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.services.feed import build_feed
from app.services.schema_compat import clear_schema_cache, complaints_v3_ready


def _legacy_engine():
    """SQLite schema approximating pre-009 complaints (no is_sensitive / visibility)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE users (
                    id VARCHAR(255) PRIMARY KEY,
                    email VARCHAR(255),
                    role VARCHAR(50) NOT NULL DEFAULT 'citizen',
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE categories (
                    id CHAR(32) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    slug VARCHAR(100) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE complaints (
                    id CHAR(32) PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    category_id CHAR(32),
                    title VARCHAR(200) NOT NULL,
                    description TEXT NOT NULL,
                    status VARCHAR(30) NOT NULL,
                    address VARCHAR(500) NOT NULL,
                    ward VARCHAR(100),
                    city VARCHAR(100) NOT NULL,
                    latitude FLOAT,
                    longitude FLOAT,
                    public_latitude FLOAT,
                    public_longitude FLOAT,
                    anonymous_to_public BOOLEAN NOT NULL DEFAULT 0,
                    city_id CHAR(32),
                    electoral_ward_id CHAR(32),
                    department_id CHAR(32),
                    ward_office_id CHAR(32),
                    google_place_id VARCHAR(255),
                    ai_suggested_category_id CHAR(32),
                    ai_confidence FLOAT,
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE complaint_images (
                    id CHAR(32) PRIMARY KEY,
                    complaint_id CHAR(32) NOT NULL,
                    cloudinary_url VARCHAR(500) NOT NULL,
                    cloudinary_public_id VARCHAR(255) NOT NULL,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE cities (
                    id CHAR(32) PRIMARY KEY,
                    slug VARCHAR(50) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    state_name VARCHAR(100),
                    state_code VARCHAR(10),
                    country_code VARCHAR(10),
                    status VARCHAR(30),
                    municipality_name VARCHAR(200),
                    created_at DATETIME,
                    updated_at DATETIME
                )
                """
            )
        )
    return engine


def test_feed_works_without_v3_columns():
    clear_schema_cache()
    engine = _legacy_engine()
    SessionLocal = sessionmaker(bind=engine)
    db: Session = SessionLocal()
    try:
        assert complaints_v3_ready(db) is False
        complaint_id = uuid.uuid4()
        category_id = uuid.uuid4()
        now = "2026-09-01T10:00:00"
        db.execute(
            text(
                "INSERT INTO users (id, email, role, created_at, updated_at) "
                "VALUES ('user_1', 'a@b.c', 'citizen', :now, :now)"
            ),
            {"now": now},
        )
        db.execute(
            text(
                "INSERT INTO categories (id, name, slug, is_active, created_at, updated_at) "
                "VALUES (:id, 'Roads', 'roads', 1, :now, :now)"
            ),
            {"id": category_id.hex, "now": now},
        )
        db.execute(
            text(
                """
                INSERT INTO complaints (
                    id, user_id, category_id, title, description, status, address,
                    ward, city, public_latitude, public_longitude, anonymous_to_public,
                    created_at, updated_at
                ) VALUES (
                    :id, 'user_1', :cat, 'Pothole', 'Large pothole on FC Road',
                    'SUBMITTED', 'FC Road', 'Deccan', 'Pune', 18.52, 73.85, 0, :now, :now
                )
                """
            ),
            {"id": complaint_id.hex, "cat": category_id.hex, "now": now},
        )
        db.commit()

        result = build_feed(db, city_slug="pune", limit=10)
        assert len(result["items"]) == 1
        assert result["items"][0]["title"] == "Pothole"
        assert result["items"][0]["like_count"] == 0
    finally:
        db.close()
        engine.dispose()
        clear_schema_cache()
