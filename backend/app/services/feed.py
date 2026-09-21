from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, inspect, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.city import City
from app.models.community import FeedEvent
from app.models.complaint import Complaint


def _table_exists(db: Session, table_name: str) -> bool:
    return inspect(db.bind).has_table(table_name)


def _public_complaint_item(complaint: Complaint) -> dict:
    images = sorted(complaint.images, key=lambda img: img.sort_order)
    return {
        "id": complaint.id,
        "kind": "original",
        "title": complaint.title,
        "caption": complaint.public_caption or complaint.title,
        "status": complaint.status.value if hasattr(complaint.status, "value") else complaint.status,
        "ward": complaint.ward,
        "city": complaint.city,
        "category_id": complaint.category_id,
        "public_latitude": complaint.public_latitude,
        "public_longitude": complaint.public_longitude,
        "created_at": complaint.created_at,
        "published_at": complaint.created_at,
        "image_count": len(images),
        "thumbnail_url": images[0].cloudinary_url if images else None,
    }


def build_feed(
    db: Session,
    *,
    city_slug: str,
    mode: str = "blend",
    cursor: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    limit: int = 30,
    viewer_id: str | None = None,
) -> dict:
    del mode, lat, lng, viewer_id  # reserved for future ranking

    city = db.scalar(select(City).where(City.slug == city_slug))
    city_filter = Complaint.city_id == city.id if city else Complaint.city == city_slug.title()

    cursor_created: datetime | None = None
    cursor_id: uuid.UUID | None = None
    if cursor:
        parts = cursor.split("|", 1)
        if len(parts) == 2:
            cursor_created = datetime.fromisoformat(parts[0])
            cursor_id = uuid.UUID(parts[1])

    if _table_exists(db, "feed_events"):
        stmt = (
            select(FeedEvent, Complaint)
            .join(Complaint, FeedEvent.complaint_id == Complaint.id)
            .where(
                FeedEvent.visibility == "public",
                Complaint.is_sensitive.is_(False),
                city_filter,
            )
            .options(joinedload(Complaint.images), joinedload(Complaint.category))
            .order_by(FeedEvent.published_at.desc(), FeedEvent.id.desc())
            .limit(limit + 1)
        )
        if cursor_created and cursor_id:
            stmt = stmt.where(
                or_(
                    FeedEvent.published_at < cursor_created,
                    and_(FeedEvent.published_at == cursor_created, FeedEvent.id < cursor_id),
                )
            )
        rows = db.execute(stmt).unique().all()
        items = []
        for event, complaint in rows[:limit]:
            base = _public_complaint_item(complaint)
            base["kind"] = event.kind
            base["published_at"] = event.published_at
            base["feed_event_id"] = event.id
            items.append(base)
        next_cursor = None
        if len(rows) > limit:
            last_event = rows[limit - 1][0]
            next_cursor = f"{last_event.published_at.isoformat()}|{last_event.id}"
        return {"items": items, "next_cursor": next_cursor}

    stmt = (
        select(Complaint)
        .where(Complaint.is_sensitive.is_(False), city_filter)
        .options(joinedload(Complaint.images), joinedload(Complaint.category))
        .order_by(Complaint.created_at.desc(), Complaint.id.desc())
        .limit(limit + 1)
    )
    if cursor_created and cursor_id:
        stmt = stmt.where(
            or_(
                Complaint.created_at < cursor_created,
                and_(Complaint.created_at == cursor_created, Complaint.id < cursor_id),
            )
        )

    complaints = db.scalars(stmt).unique().all()
    items = [_public_complaint_item(c) for c in complaints[:limit]]
    next_cursor = None
    if len(complaints) > limit:
        last = complaints[limit - 1]
        next_cursor = f"{last.created_at.isoformat()}|{last.id}"
    return {"items": items, "next_cursor": next_cursor}
