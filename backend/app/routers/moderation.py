import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_officer_or_admin
from app.core.security import ClerkUser
from app.schemas.moderation import (
    ModerationActionRequest,
    ModerationActionResponse,
    ReportCreateRequest,
    ReportResponse,
)
from app.services import moderation as moderation_service

router = APIRouter(tags=["moderation"])


@router.post("/reports", response_model=ReportResponse)
def create_report(
    payload: ReportCreateRequest,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> ReportResponse:
    return ReportResponse.model_validate(
        moderation_service.create_report(
            db,
            reporter_id=current_user.user_id,
            target_type=payload.target_type,
            target_id=payload.target_id,
            category=payload.category,
            reason=payload.reason,
        )
    )


@router.get("/moderation/queue", response_model=list[ReportResponse])
def moderation_queue(
    status: str = Query(default="open"),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    _: ClerkUser = Depends(require_officer_or_admin),
) -> list[ReportResponse]:
    reports = moderation_service.list_queue(db, status_filter=status, limit=limit)
    return [ReportResponse.model_validate(r) for r in reports]


@router.post("/moderation/{report_id}/action", response_model=ModerationActionResponse)
def moderation_action(
    report_id: uuid.UUID,
    payload: ModerationActionRequest,
    db: Session = Depends(get_db),
    moderator: ClerkUser = Depends(require_officer_or_admin),
) -> ModerationActionResponse:
    return ModerationActionResponse.model_validate(
        moderation_service.apply_action(
            db,
            moderator_id=moderator.user_id,
            report_id=report_id,
            action=payload.action,
            reason=payload.reason,
        )
    )
