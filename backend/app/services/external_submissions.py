from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import ClerkUser
from app.models.complaint import Complaint
from app.models.external_submission import ExternalSubmission, ExternalSubmissionStatus
from app.schemas.external_submission import (
    ExternalSubmissionResponse,
    ExternalSubmissionStartRequest,
    ExternalSubmissionTokenRequest,
)


def get_or_create_external_submission(
    db: Session,
    complaint: Complaint,
) -> ExternalSubmission:
    record = db.scalar(
        select(ExternalSubmission).where(ExternalSubmission.complaint_id == complaint.id)
    )
    if record is not None:
        return record
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
    """Persist a user-reported external token without claiming verified registration."""
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


USER_REPORTED_REFERENCE_NOTE = (
    "User-reported reference; not verified by CivicSense or the government portal."
)


def to_external_submission_response(record: ExternalSubmission) -> ExternalSubmissionResponse:
    note = (
        USER_REPORTED_REFERENCE_NOTE
        if record.status == ExternalSubmissionStatus.TOKEN_RECEIVED
        else None
    )
    return ExternalSubmissionResponse(
        id=record.id,
        complaint_id=record.complaint_id,
        routing_channel_id=record.routing_channel_id,
        provider=record.provider,
        status=record.status,
        external_token=record.external_token,
        status_url=record.status_url,
        forwarded_at=record.forwarded_at,
        token_received_at=record.token_received_at,
        reference_note=note,
    )
