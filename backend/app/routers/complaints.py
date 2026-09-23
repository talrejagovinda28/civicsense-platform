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
from app.models.complaint_image import ComplaintImage, MediaVisibility
from app.services.access import assert_complaint_case_access, is_privileged_role
from app.core.security import ClerkUser
from app.models.category import Category
from app.models.city import City
from app.models.complaint import Complaint, ComplaintStatus
from app.services.schema_compat import (
    complaint_images_v3_ready,
    complaints_v3_ready,
    load_only_existing,
    table_columns,
)
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
from app.schemas.complaint_status import StatusHistoryResponse, StatusUpdateRequest
from app.schemas.external_submission import (
    ExternalSubmissionResponse,
    ExternalSubmissionStartRequest,
    ExternalSubmissionTokenRequest,
)
from app.schemas.timeline import TimelineEventResponse, TimelineListResponse
from app.services.complaints import (
    create_complaint,
    suggest_category,
    update_complaint_status,
)
from app.services.external_submissions import (
    save_external_token,
    start_external_handoff,
    to_external_submission_response,
)
from app.services.timeline import list_timeline_events

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/complaints", tags=["complaints"])

DESCRIPTION_PREVIEW_LENGTH = 150
OPEN_STATUSES = (ComplaintStatus.SUBMITTED, ComplaintStatus.IN_PROGRESS)


def _truncate(text: str, max_length: int = DESCRIPTION_PREVIEW_LENGTH) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."


def _visible_images(complaint: Complaint, *, full_access: bool, images_v3: bool = True) -> list:
    images = sorted(complaint.images, key=lambda image: image.sort_order)
    if full_access or not images_v3:
        return images
    return [image for image in images if image.visibility == MediaVisibility.PUBLIC]


def _to_feed_item(
    complaint: Complaint,
    *,
    truncate: bool,
    full_access: bool = False,
    images_v3: bool = True,
) -> ComplaintFeedItem:
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
        images=_visible_images(
            complaint, full_access=full_access, images_v3=images_v3
        ),
        created_at=complaint.created_at,
        public_latitude=complaint.public_latitude,
        public_longitude=complaint.public_longitude,
        electoral_ward_id=complaint.electoral_ward_id,
        category_id=complaint.category_id,
    )


def _can_view_full(complaint: Complaint, user: ClerkUser | None) -> bool:
    if user is None:
        return False
    if is_privileged_role(user.role):
        return True
    return complaint.user_id == user.user_id


def _sensitive_visibility_filter(user: ClerkUser | None, *, v3_ready: bool):
    if not v3_ready:
        return True
    if user is None or not is_privileged_role(user.role):
        if user is None:
            return Complaint.is_sensitive.is_(False)
        return (Complaint.is_sensitive.is_(False)) | (
            Complaint.user_id == user.user_id
        )
    return True


def _approximate_location_label(complaint: Complaint) -> str | None:
    if complaint.ward:
        return complaint.ward
    if complaint.city:
        return complaint.city
    return None


def _status_history(
    complaint: Complaint,
    *,
    full_access: bool,
) -> list[StatusHistoryResponse]:
    items = sorted(complaint.status_history, key=lambda entry: entry.created_at)
    return [
        StatusHistoryResponse(
            id=item.id,
            status=item.status,
            note=item.note if full_access else None,
            updated_by=item.updated_by if full_access else "civicsense",
            created_at=item.created_at,
        )
        for item in items
    ]


def _to_detail(
    complaint: Complaint,
    user: ClerkUser | None,
    *,
    images_v3: bool = True,
) -> ComplaintDetail:
    full_access = _can_view_full(complaint, user)
    return ComplaintDetail(
        id=complaint.id,
        title=complaint.title,
        description=complaint.description,
        status=complaint.status,
        category=complaint.category,
        ward=complaint.ward,
        city=complaint.city,
        images=_visible_images(
            complaint, full_access=full_access, images_v3=images_v3
        ),
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
        address=complaint.address if full_access else None,
        latitude=complaint.latitude if full_access else None,
        longitude=complaint.longitude if full_access else None,
        google_place_id=complaint.google_place_id if full_access else None,
        user_id=(
            complaint.user_id
            if full_access and not complaint.anonymous_to_public
            else None
        ),
        ai_suggested_category_id=(
            complaint.ai_suggested_category_id if full_access else None
        ),
        ai_confidence=complaint.ai_confidence if full_access else None,
        status_history=_status_history(complaint, full_access=full_access),
        electoral_ward_id=complaint.electoral_ward_id,
        department_id=complaint.department_id,
        ward_office_id=complaint.ward_office_id,
        city_id=complaint.city_id,
        public_latitude=complaint.public_latitude,
        public_longitude=complaint.public_longitude,
        external_submission=(
            to_external_submission_response(complaint.external_submission)
            if complaint.external_submission
            else None
        ),
        approximate_location_label=(
            _approximate_location_label(complaint) if not full_access else complaint.ward
        ),
    )


def _complaint_stmt(db: Session | None = None):
    options: list = [
        joinedload(Complaint.category),
        joinedload(Complaint.status_history),
        joinedload(Complaint.external_submission),
    ]
    if db is not None:
        complaint_load = load_only_existing(Complaint, table_columns(db, "complaints"))
        if complaint_load is not None:
            options.insert(0, complaint_load)
        image_load = load_only_existing(
            ComplaintImage, table_columns(db, "complaint_images")
        )
        images_opt = joinedload(Complaint.images)
        if image_load is not None:
            images_opt = images_opt.options(image_load)
        options.append(images_opt)
    else:
        options.append(joinedload(Complaint.images))
    return select(Complaint).options(*options)


def _apply_complaint_filters(
    stmt,
    *,
    city_slug: str | None,
    electoral_ward_id: uuid.UUID | None,
    status_filter: ComplaintStatus | None,
    category_id: uuid.UUID | None,
):
    if city_slug:
        normalized = city_slug.strip().lower()
        stmt = stmt.join(City, Complaint.city_id == City.id, isouter=True).where(
            (City.slug == normalized) | (Complaint.city.ilike(normalized.replace("-", " ")))
        )
    if electoral_ward_id:
        stmt = stmt.where(Complaint.electoral_ward_id == electoral_ward_id)
    if status_filter:
        stmt = stmt.where(Complaint.status == status_filter)
    if category_id:
        stmt = stmt.where(Complaint.category_id == category_id)
    return stmt


def _get_complaint_or_404(db: Session, complaint_id: uuid.UUID) -> Complaint:
    stmt = _complaint_stmt(db).where(Complaint.id == complaint_id)
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
    current_user: ClerkUser | None = Depends(get_optional_user),
    city: str = Query(default="pune"),
    electoral_ward_id: uuid.UUID | None = Query(default=None),
    status_filter: ComplaintStatus | None = Query(default=None, alias="status"),
    category_id: uuid.UUID | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> PaginatedComplaints:
    v3_ready = complaints_v3_ready(db)
    images_v3 = complaint_images_v3_ready(db)
    visibility = _sensitive_visibility_filter(current_user, v3_ready=v3_ready)
    # Count with PK only so pre-009 DBs are not queried for V3 columns.
    base_stmt = select(Complaint.id)
    if visibility is not True:
        base_stmt = base_stmt.where(visibility)
    filtered_stmt = _apply_complaint_filters(
        base_stmt,
        city_slug=city,
        electoral_ward_id=electoral_ward_id,
        status_filter=status_filter,
        category_id=category_id,
    )
    total = db.scalar(select(func.count()).select_from(filtered_stmt.subquery())) or 0

    stmt = _apply_complaint_filters(
        _complaint_stmt(db),
        city_slug=city,
        electoral_ward_id=electoral_ward_id,
        status_filter=status_filter,
        category_id=category_id,
    )
    if visibility is not True:
        stmt = stmt.where(visibility)
    stmt = stmt.order_by(Complaint.created_at.desc()).offset(skip).limit(limit)
    complaints = db.scalars(stmt).unique().all()

    logger.info("Public feed: %d complaints (city=%s)", total, city)
    return PaginatedComplaints(
        items=[
            _to_feed_item(c, truncate=True, images_v3=images_v3) for c in complaints
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/mine", response_model=list[ComplaintFeedItem])
def list_my_complaints(
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> list[ComplaintFeedItem]:
    images_v3 = complaint_images_v3_ready(db)
    stmt = (
        _complaint_stmt(db)
        .where(Complaint.user_id == current_user.user_id)
        .order_by(Complaint.created_at.desc())
    )
    complaints = db.scalars(stmt).unique().all()

    logger.info("User %s listed %d complaints", current_user.user_id, len(complaints))
    return [
        _to_feed_item(c, truncate=False, full_access=True, images_v3=images_v3)
        for c in complaints
    ]


@router.get("/officer/queue", response_model=list[ComplaintFeedItem])
def list_officer_queue(
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(require_officer_or_admin),
    city: str = Query(default="Pune"),
) -> list[ComplaintFeedItem]:
    del current_user
    images_v3 = complaint_images_v3_ready(db)
    stmt = (
        _complaint_stmt(db)
        .where(
            Complaint.city == city,
            Complaint.status.in_(OPEN_STATUSES),
        )
        .order_by(Complaint.created_at.asc())
    )
    complaints = db.scalars(stmt).unique().all()
    logger.info("Officer queue: %d open complaints (city=%s)", len(complaints), city)
    return [
        _to_feed_item(c, truncate=False, full_access=True, images_v3=images_v3)
        for c in complaints
    ]


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
    try:
        complaint = create_complaint(db, current_user, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    loaded = _get_complaint_or_404(db, complaint.id)
    return _to_detail(
        loaded, current_user, images_v3=complaint_images_v3_ready(db)
    )


@router.get("/{complaint_id}", response_model=ComplaintDetail)
def get_complaint(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: ClerkUser | None = Depends(get_optional_user),
) -> ComplaintDetail:
    complaint = _get_complaint_or_404(db, complaint_id)
    viewer_id = current_user.user_id if current_user else None
    viewer_role = current_user.role if current_user else None
    assert_complaint_case_access(db, complaint, viewer_id, viewer_role)
    return _to_detail(
        complaint, current_user, images_v3=complaint_images_v3_ready(db)
    )


@router.get("/{complaint_id}/timeline", response_model=TimelineListResponse)
def get_complaint_timeline(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: ClerkUser | None = Depends(get_optional_user),
) -> TimelineListResponse:
    complaint = _get_complaint_or_404(db, complaint_id)
    viewer_id = current_user.user_id if current_user else None
    viewer_role = current_user.role if current_user else None
    items = list_timeline_events(
        db,
        complaint=complaint,
        user_id=viewer_id,
        role=viewer_role,
    )
    return TimelineListResponse(
        items=[TimelineEventResponse(**item) for item in items],
    )


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
    return _to_detail(
        loaded, current_user, images_v3=complaint_images_v3_ready(db)
    )


@router.post(
    "/{complaint_id}/external-submission/start",
    response_model=ExternalSubmissionResponse,
)
def start_external_submission_endpoint(
    complaint_id: uuid.UUID,
    payload: ExternalSubmissionStartRequest,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> ExternalSubmissionResponse:
    complaint = _get_complaint_or_404(db, complaint_id)
    record = start_external_handoff(db, complaint, current_user, payload)
    return to_external_submission_response(record)


@router.patch(
    "/{complaint_id}/external-submission/token",
    response_model=ExternalSubmissionResponse,
)
def save_external_submission_token_endpoint(
    complaint_id: uuid.UUID,
    payload: ExternalSubmissionTokenRequest,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> ExternalSubmissionResponse:
    complaint = _get_complaint_or_404(db, complaint_id)
    record = save_external_token(db, complaint, current_user, payload)
    return to_external_submission_response(record)
