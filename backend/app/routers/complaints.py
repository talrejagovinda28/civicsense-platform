import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.deps import (
    get_current_user,
    get_db,
    get_optional_user,
    require_officer_or_admin,
)
from app.core.security import ClerkUser
from app.models.complaint import Complaint, ComplaintStatus
from app.schemas.complaint import (
    ComplaintDetail,
    ComplaintFeedItem,
    PaginatedComplaints,
)
from app.schemas.complaint_create import (
    ComplaintCreate,
    SuggestCategoryRequest,
    SuggestCategoryResponse,
)
from app.schemas.complaint_status import StatusUpdateRequest
from app.services.complaints import (
    create_complaint,
    suggest_category,
    update_complaint_status,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/complaints", tags=["complaints"])

DESCRIPTION_PREVIEW_LENGTH = 150
OPEN_STATUSES = (ComplaintStatus.SUBMITTED, ComplaintStatus.IN_PROGRESS)


def _truncate(text: str, max_length: int = DESCRIPTION_PREVIEW_LENGTH) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."


def _to_feed_item(complaint: Complaint, *, truncate: bool) -> ComplaintFeedItem:
    description = (
        _truncate(complaint.description) if truncate else complaint.description
    )
    return ComplaintFeedItem(
        id=complaint.id,
        title=complaint.title,
        description=description,
        status=complaint.status,
        category=complaint.category,
        ward=complaint.ward,
        city=complaint.city,
        images=sorted(complaint.images, key=lambda image: image.sort_order),
        created_at=complaint.created_at,
    )


def _can_view_full(complaint: Complaint, user: ClerkUser | None) -> bool:
    if user is None:
        return False
    if user.role in {"officer", "admin"}:
        return True
    return complaint.user_id == user.user_id


def _to_detail(complaint: Complaint, user: ClerkUser | None) -> ComplaintDetail:
    full_access = _can_view_full(complaint, user)
    return ComplaintDetail(
        id=complaint.id,
        title=complaint.title,
        description=complaint.description,
        status=complaint.status,
        category=complaint.category,
        ward=complaint.ward,
        city=complaint.city,
        images=sorted(complaint.images, key=lambda image: image.sort_order),
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
        address=complaint.address if full_access else None,
        latitude=complaint.latitude if full_access else None,
        longitude=complaint.longitude if full_access else None,
        google_place_id=complaint.google_place_id if full_access else None,
        user_id=complaint.user_id if full_access else None,
        ai_suggested_category_id=(
            complaint.ai_suggested_category_id if full_access else None
        ),
        ai_confidence=complaint.ai_confidence if full_access else None,
        status_history=sorted(
            complaint.status_history, key=lambda item: item.created_at
        ),
    )


def _complaint_stmt():
    return select(Complaint).options(
        joinedload(Complaint.category),
        joinedload(Complaint.images),
        joinedload(Complaint.status_history),
    )


def _get_complaint_or_404(db: Session, complaint_id: uuid.UUID) -> Complaint:
    stmt = _complaint_stmt().where(Complaint.id == complaint_id)
    complaint = db.scalars(stmt).unique().first()
    if complaint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found",
        )
    return complaint


@router.get("", response_model=PaginatedComplaints)
def list_complaints(
    db: Session = Depends(get_db),
    city: str = Query(default="Pune"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> PaginatedComplaints:
    total = (
        db.scalar(
            select(func.count()).select_from(Complaint).where(Complaint.city == city)
        )
        or 0
    )

    stmt = (
        _complaint_stmt()
        .where(Complaint.city == city)
        .order_by(Complaint.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    complaints = db.scalars(stmt).unique().all()

    logger.info("Public feed: %d complaints (city=%s)", total, city)
    return PaginatedComplaints(
        items=[_to_feed_item(c, truncate=True) for c in complaints],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/mine", response_model=list[ComplaintFeedItem])
def list_my_complaints(
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> list[ComplaintFeedItem]:
    stmt = (
        _complaint_stmt()
        .where(Complaint.user_id == current_user.user_id)
        .order_by(Complaint.created_at.desc())
    )
    complaints = db.scalars(stmt).unique().all()

    logger.info("User %s listed %d complaints", current_user.user_id, len(complaints))
    return [_to_feed_item(c, truncate=False) for c in complaints]


@router.get("/officer/queue", response_model=list[ComplaintFeedItem])
def list_officer_queue(
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(require_officer_or_admin),
    city: str = Query(default="Pune"),
) -> list[ComplaintFeedItem]:
    del current_user
    stmt = (
        _complaint_stmt()
        .where(
            Complaint.city == city,
            Complaint.status.in_(OPEN_STATUSES),
        )
        .order_by(Complaint.created_at.asc())
    )
    complaints = db.scalars(stmt).unique().all()
    logger.info("Officer queue: %d open complaints (city=%s)", len(complaints), city)
    return [_to_feed_item(c, truncate=False) for c in complaints]


@router.post("/suggest-category", response_model=SuggestCategoryResponse)
def suggest_complaint_category(
    payload: SuggestCategoryRequest,
    db: Session = Depends(get_db),
    _: ClerkUser = Depends(get_current_user),
) -> SuggestCategoryResponse:
    return suggest_category(db, payload.photo_urls)


@router.post("", response_model=ComplaintDetail, status_code=status.HTTP_201_CREATED)
def create_complaint_endpoint(
    payload: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> ComplaintDetail:
    complaint = create_complaint(db, current_user, payload)
    loaded = _get_complaint_or_404(db, complaint.id)
    return _to_detail(loaded, current_user)


@router.get("/{complaint_id}", response_model=ComplaintDetail)
def get_complaint(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: ClerkUser | None = Depends(get_optional_user),
) -> ComplaintDetail:
    complaint = _get_complaint_or_404(db, complaint_id)
    return _to_detail(complaint, current_user)


@router.patch("/{complaint_id}/status", response_model=ComplaintDetail)
def update_complaint_status_endpoint(
    complaint_id: uuid.UUID,
    payload: StatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(require_officer_or_admin),
) -> ComplaintDetail:
    complaint = _get_complaint_or_404(db, complaint_id)
    update_complaint_status(db, complaint, current_user, payload)
    loaded = _get_complaint_or_404(db, complaint_id)
    return _to_detail(loaded, current_user)
