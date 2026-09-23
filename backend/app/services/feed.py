from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.city import City
from app.models.community import FeedEvent, FeedEventKind
from app.models.complaint import Complaint
from app.models.complaint_image import ComplaintImage, MediaVisibility
from app.services.schema_compat import (
    complaint_images_v3_ready,
    complaints_v3_ready,
    load_only_existing,
    table_columns,
    table_exists,
)
from app.services.social import get_engagement_counts

DESCRIPTION_PREVIEW_LENGTH = 150
RESPONSIBILITY_LINE = "Responsibility being verified"


def _truncate(text: str, max_length: int = DESCRIPTION_PREVIEW_LENGTH) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."


def _map_feed_kind(event_kind: str) -> str:
    if event_kind == FeedEventKind.MILESTONE:
        return "update"
    return "complaint"


def _public_description(complaint: Complaint, *, v3_ready: bool) -> str:
    if v3_ready:
        text = complaint.public_caption or complaint.description
    else:
        text = complaint.description
    return _truncate(text)


def _locality_label(complaint: Complaint) -> str | None:
    return complaint.ward or complaint.city


def _complaint_query_options(db: Session):
    options: list = []
    complaint_load = load_only_existing(Complaint, table_columns(db, "complaints"))
    if complaint_load is not None:
        options.append(complaint_load)

    image_load = load_only_existing(ComplaintImage, table_columns(db, "complaint_images"))
    images_opt = joinedload(Complaint.images)
    if image_load is not None:
        images_opt = images_opt.options(image_load)
    options.append(images_opt)
    options.append(joinedload(Complaint.category))
    return options


def _public_images(complaint: Complaint, *, images_v3: bool) -> list:
    images = sorted(complaint.images, key=lambda img: img.sort_order)
    if not images_v3:
        return images
    return [img for img in images if img.visibility == MediaVisibility.PUBLIC]


def _build_feed_item(
    db: Session,
    *,
    item_id: uuid.UUID,
    complaint: Complaint,
    kind: str,
    published_at: datetime,
    viewer_id: str | None,
    v3_ready: bool,
    images_v3: bool,
) -> dict:
    public_images = _public_images(complaint, images_v3=images_v3)
    image_url = public_images[0].cloudinary_url if public_images else None
    engagement = get_engagement_counts(db, complaint_id=complaint.id, viewer_id=viewer_id)
    category_name = complaint.category.name if complaint.category else None

    return {
        "id": item_id,
        "complaint_id": complaint.id,
        "kind": kind,
        "title": complaint.title,
        "description": _public_description(complaint, v3_ready=v3_ready),
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

    v3_ready = complaints_v3_ready(db)
    images_v3 = complaint_images_v3_ready(db)
    query_options = _complaint_query_options(db)

    # Select only id so incomplete/partial city tables do not break the feed.
    city_id = db.scalar(select(City.id).where(City.slug == city_slug))
    if city_id is not None:
        city_filter = Complaint.city_id == city_id
    else:
        city_filter = Complaint.city.ilike(city_slug.replace("-", " "))

    cursor_created: datetime | None = None
    cursor_id: uuid.UUID | None = None
    if cursor:
        parts = cursor.split("|", 1)
        if len(parts) == 2:
            cursor_created = datetime.fromisoformat(parts[0])
            cursor_id = uuid.UUID(parts[1])

    if table_exists(db, "feed_events") and v3_ready:
        stmt = (
            select(FeedEvent, Complaint)
            .join(Complaint, FeedEvent.complaint_id == Complaint.id)
            .where(
                FeedEvent.visibility == "public",
                Complaint.is_sensitive.is_(False),
                city_filter,
            )
            .options(*query_options)
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
                    v3_ready=v3_ready,
                    images_v3=images_v3,
                )
            )
        next_cursor = None
        if len(rows) > limit:
            last_event = rows[limit - 1][0]
            next_cursor = f"{last_event.published_at.isoformat()}|{last_event.id}"
        if items or cursor_created:
            return {"items": items, "next_cursor": next_cursor}

    stmt = select(Complaint).where(city_filter).options(*query_options)
    if v3_ready:
        stmt = stmt.where(Complaint.is_sensitive.is_(False))
    stmt = stmt.order_by(Complaint.created_at.desc(), Complaint.id.desc()).limit(limit + 1)
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
            v3_ready=v3_ready,
            images_v3=images_v3,
        )
        for complaint in complaints[:limit]
    ]
    next_cursor = None
    if len(complaints) > limit:
        last = complaints[limit - 1]
        next_cursor = f"{last.created_at.isoformat()}|{last.id}"
    return {"items": items, "next_cursor": next_cursor}
