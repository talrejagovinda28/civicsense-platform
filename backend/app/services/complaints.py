import logging
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import ClerkUser
from app.models.category import Category
from app.models.complaint import Complaint, ComplaintStatus
from app.models.complaint_image import ComplaintImage
from app.models.complaint_status_history import ComplaintStatusHistory
from app.schemas.complaint_create import (
    ComplaintCreate,
    SuggestCategoryResponse,
)
from app.schemas.complaint_status import StatusUpdateRequest

logger = logging.getLogger(__name__)

MAX_COMPLAINTS_PER_HOUR = 5
STUB_AI_CONFIDENCE = 0.85

PUNE_LAT_MIN = 18.41
PUNE_LAT_MAX = 18.64
PUNE_LNG_MIN = 73.73
PUNE_LNG_MAX = 73.98

OFFICER_TRANSITIONS: dict[ComplaintStatus, set[ComplaintStatus]] = {
    ComplaintStatus.SUBMITTED: {ComplaintStatus.IN_PROGRESS},
    ComplaintStatus.IN_PROGRESS: {ComplaintStatus.RESOLVED},
    ComplaintStatus.RESOLVED: {ComplaintStatus.CLOSED},
    ComplaintStatus.CLOSED: set(),
}

ADMIN_EXTRA_TRANSITIONS: dict[ComplaintStatus, set[ComplaintStatus]] = {
    ComplaintStatus.SUBMITTED: {ComplaintStatus.CLOSED},
}


def _get_active_category(db: Session, category_id: uuid.UUID) -> Category:
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.is_active.is_(True),
        )
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or inactive category",
        )
    return category


def _enforce_rate_limit(db: Session, user_id: str) -> None:
    one_hour_ago = datetime.now(UTC) - timedelta(hours=1)
    count = (
        db.scalar(
            select(func.count())
            .select_from(Complaint)
            .where(
                Complaint.user_id == user_id,
                Complaint.created_at >= one_hour_ago,
            )
        )
        or 0
    )
    if count >= MAX_COMPLAINTS_PER_HOUR:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded: max 5 complaints per hour",
        )


def _warn_if_outside_pune(latitude: float, longitude: float) -> None:
    in_bounds = (
        PUNE_LAT_MIN <= latitude <= PUNE_LAT_MAX
        and PUNE_LNG_MIN <= longitude <= PUNE_LNG_MAX
    )
    if not in_bounds:
        logger.warning(
            "Complaint location outside Pune bounding box: lat=%s, lng=%s",
            latitude,
            longitude,
        )


def generate_title(category_name: str, address: str) -> str:
    landmark = address.split(",")[0].strip()
    if not landmark:
        landmark = address.strip()
    title = f"{category_name} near {landmark}"
    return title[:200]


def _allowed_next_statuses(
    current: ComplaintStatus,
    role: str,
) -> set[ComplaintStatus]:
    allowed = set(OFFICER_TRANSITIONS.get(current, set()))
    if role == "admin":
        allowed |= ADMIN_EXTRA_TRANSITIONS.get(current, set())
    return allowed


def _record_status_history(
    db: Session,
    complaint: Complaint,
    new_status: ComplaintStatus,
    updated_by: str,
    note: str | None,
) -> None:
    history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        status=new_status,
        note=note,
        updated_by=updated_by,
    )
    db.add(history)
    complaint.status = new_status


def update_complaint_status(
    db: Session,
    complaint: Complaint,
    current_user: ClerkUser,
    payload: StatusUpdateRequest,
) -> Complaint:
    allowed = _allowed_next_statuses(complaint.status, current_user.role)
    if payload.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot transition from {complaint.status.value} "
                f"to {payload.status.value}"
            ),
        )

    _record_status_history(
        db,
        complaint,
        payload.status,
        current_user.user_id,
        payload.note,
    )
    db.commit()
    db.refresh(complaint)

    logger.info(
        "Complaint %s status updated to %s by %s",
        complaint.id,
        payload.status.value,
        current_user.user_id,
    )
    return complaint


def suggest_category(db: Session, photo_urls: list[str]) -> SuggestCategoryResponse:
    del photo_urls  # reserved for future AI vision integration

    category = db.scalar(
        select(Category).where(
            Category.slug == "other",
            Category.is_active.is_(True),
        )
    )
    if category is None:
        category = db.scalar(
            select(Category)
            .where(Category.is_active.is_(True))
            .order_by(Category.name)
            .limit(1)
        )

    if category is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No complaint categories are configured",
        )

    logger.info("AI stub suggested category: %s", category.slug)
    return SuggestCategoryResponse(
        category_id=category.id,
        category_name=category.name,
        confidence=STUB_AI_CONFIDENCE,
    )


def create_complaint(
    db: Session,
    current_user: ClerkUser,
    payload: ComplaintCreate,
) -> Complaint:
    _enforce_rate_limit(db, current_user.user_id)
    _warn_if_outside_pune(payload.latitude, payload.longitude)

    category = _get_active_category(db, payload.category_id)

    if payload.ai_suggested_category_id is not None:
        _get_active_category(db, payload.ai_suggested_category_id)

    title = payload.title or generate_title(category.name, payload.address)

    complaint = Complaint(
        user_id=current_user.user_id,
        title=title,
        description=payload.description,
        status=ComplaintStatus.SUBMITTED,
        category_id=payload.category_id,
        ai_suggested_category_id=payload.ai_suggested_category_id,
        ai_confidence=payload.ai_confidence,
        latitude=payload.latitude,
        longitude=payload.longitude,
        google_place_id=payload.google_place_id,
        address=payload.address,
        ward=payload.ward,
        city=payload.city,
    )

    for image in payload.images:
        complaint.images.append(
            ComplaintImage(
                cloudinary_url=image.cloudinary_url,
                cloudinary_public_id=image.cloudinary_public_id,
                sort_order=image.sort_order,
            )
        )

    db.add(complaint)
    db.flush()

    _record_status_history(
        db,
        complaint,
        ComplaintStatus.SUBMITTED,
        current_user.user_id,
        "Complaint submitted",
    )
    db.commit()
    db.refresh(complaint)

    logger.info("Complaint created: %s by user %s", complaint.id, current_user.user_id)
    return complaint
