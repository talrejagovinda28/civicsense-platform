import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.security import ClerkUser
from app.schemas.resolution import (
    EvidenceResponse,
    EvidenceSubmitRequest,
    IndependentReviewRequest,
    ReporterConfirmRequest,
    ReviewResponse,
    VerificationResponse,
)
from app.services import resolution as resolution_service

router = APIRouter(tags=["resolution"])


@router.post("/complaints/{complaint_id}/resolution-evidence", response_model=EvidenceResponse)
def submit_resolution_evidence(
    complaint_id: uuid.UUID,
    payload: EvidenceSubmitRequest,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> EvidenceResponse:
    return EvidenceResponse.model_validate(
        resolution_service.submit_evidence(
            db,
            user_id=current_user.user_id,
            complaint_id=complaint_id,
            assertion=payload.assertion,
            submitter_role=payload.submitter_role,
            media_url=payload.media_url,
        )
    )


@router.post("/complaints/{complaint_id}/resolution-confirmation", response_model=VerificationResponse)
def reporter_resolution_confirmation(
    complaint_id: uuid.UUID,
    payload: ReporterConfirmRequest,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> VerificationResponse:
    return VerificationResponse.model_validate(
        resolution_service.reporter_confirm(
            db,
            user_id=current_user.user_id,
            complaint_id=complaint_id,
            confirmed=payload.confirmed,
            reason=payload.reason,
        )
    )


@router.post("/complaints/{complaint_id}/resolution-review", response_model=ReviewResponse)
def independent_resolution_review(
    complaint_id: uuid.UUID,
    payload: IndependentReviewRequest,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> ReviewResponse:
    return ReviewResponse.model_validate(
        resolution_service.independent_review(
            db,
            reviewer_id=current_user.user_id,
            reviewer_role=current_user.role,
            complaint_id=complaint_id,
            evidence_id=payload.evidence_id,
            decision=payload.decision,
            reason=payload.reason,
        )
    )
