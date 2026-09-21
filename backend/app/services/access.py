from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.complaint import Complaint


def is_privileged_role(role: str | None) -> bool:
    return role in {"officer", "admin"}


def can_view_sensitive_complaint(
    complaint: Complaint,
    user_id: str | None,
    role: str | None,
) -> bool:
    if not complaint.is_sensitive:
        return True
    if is_privileged_role(role):
        return True
    if user_id and complaint.user_id == user_id:
        return True
    return False


def assert_complaint_socially_visible(
    db: Session,
    complaint_id: uuid.UUID,
    user_id: str | None,
    role: str | None,
) -> Complaint:
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found",
        )
    if not can_view_sensitive_complaint(complaint, user_id, role):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found",
        )
    return complaint
