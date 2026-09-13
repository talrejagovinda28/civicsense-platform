from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import ClerkUser
from app.models.complaint import Complaint
from app.models.external_submission import ExternalSubmission, ExternalSubmissionStatus
from app.schemas.external_submission import (
    ExternalSubmissionStartRequest,
    ExternalSubmissionTokenRequest,
)


def get_or_create_external_submission(
    db: Session,
    complaint: Complaint,
) -> ExternalSubmission:
    if complaint.external_submission is not None:
        return complaint.external_submission
    record = ExternalSubmission(complaint_id=complaint.id)
    db.add(record)
    db.flush()
    return record


def start_external_handoff(
    db: Session,
    complaint: Complaint,
    current_user: ClerkUser,
    payload: ExternalSubmissionStartRequest,
) -> ExternalSubmission:
    if complaint.user_id != current_user.user_id and current_user.role not in {
        "officer",
        "admin",
    }:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    record = get_or_create_external_submission(db, complaint)
    record.status = ExternalSubmissionStatus.HANDOFF_STARTED
    record.routing_channel_id = payload.routing_channel_id
    record.forwarded_at = datetime.now(UTC)
    db.commit()
    db.refresh(record)
    return record


def save_external_token(
    db: Session,
    complaint: Complaint,
    current_user: ClerkUser,
    payload: ExternalSubmissionTokenRequest,
) -> ExternalSubmission:
    if complaint.user_id != current_user.user_id and current_user.role not in {
        "officer",
        "admin",
    }:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    record = get_or_create_external_submission(db, complaint)
    record.external_token = payload.external_token.strip()
    record.status_url = payload.status_url
    record.status = ExternalSubmissionStatus.TOKEN_RECEIVED
    record.token_received_at = datetime.now(UTC)
    db.commit()
    db.refresh(record)
    return record
