from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, inspect, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.city import City
from app.models.community import FeedEvent, FeedEventKind
from app.models.complaint import Complaint
from app.services.social import get_engagement_counts

DESCRIPTION_PREVIEW_LENGTH = 150
RESPONSIBILITY_LINE = "Responsibility being verified"


def _table_exists(db: Session, table_name: str) -> bool:
    return inspect(db.bind).has_table(table_name)


def _truncate(text: str, max_length: int = DESCRIPTION_PREVIEW_LENGTH) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."


def _map_feed_kind(event_kind: str) -> str:
    if event_kind == FeedEventKind.MILESTONE:
        return "update"
    return "complaint"


def _public_description(complaint: Complaint) -> str:
    text = complaint.public_caption or complaint.description
    return _truncate(text)


def _locality_label(complaint: Complaint) -> str | None:
    return complaint.ward or complaint.city


def _build_feed_item(
    db: Session,
    *,
    item_id: uuid.UUID,
    complaint: Complaint,
    kind: str,
    published_at: datetime,
    viewer_id: str | None,
) -> dict:
    images = sorted(complaint.images, key=lambda img: img.sort_order)
    image_url = images[0].cloudinary_url if images else None
    engagement = get_engagement_counts(db, complaint_id=complaint.id, viewer_id=viewer_id)
    category_name = complaint.category.name if complaint.category else None

    return {
        "id": item_id,
        "complaint_id": complaint.id,
        "kind": kind,
        "title": complaint.title,
        "description": _public_description(complaint),
        "status": complaint.status.value if hasattr(complaint.status, "value") else complaint.status,
        "category_name": category_name,
        "locality_label": _locality_label(complaint),
        "responsibility_line": RESPONSIBILITY_LINE,
        "image_url": image_url,
        "thumbnail_url": image_url,
        "like_count": engagement.like_count,
        "affected_count": engagement.affected_count,
        "comment_count": engagement.comment_count,
        "viewer_liked": engagement.viewer_liked,
        "viewer_affected": engagement.viewer_affected,
        "created_at": complaint.created_at,
        "published_at": published_at,
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
    del mode, lat, lng

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
            items.append(
                _build_feed_item(
                    db,
                    item_id=event.id,
                    complaint=complaint,
                    kind=_map_feed_kind(event.kind),
                    published_at=event.published_at,
                    viewer_id=viewer_id,
                )
            )
        next_cursor = None
        if len(rows) > limit:
            last_event = rows[limit - 1][0]
            next_cursor = f"{last_event.published_at.isoformat()}|{last_event.id}"
        if items or cursor_created:
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
    items = [
        _build_feed_item(
            db,
            item_id=complaint.id,
            complaint=complaint,
            kind="complaint",
            published_at=complaint.created_at,
            viewer_id=viewer_id,
        )
        for complaint in complaints[:limit]
    ]
    next_cursor = None
    if len(complaints) > limit:
        last = complaints[limit - 1]
        next_cursor = f"{last.created_at.isoformat()}|{last.id}"
    return {"items": items, "next_cursor": next_cursor}
