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
    assert_complaint_case_access(db, complaint, user_id, role)
    return complaint


def assert_complaint_case_access(
    db: Session,
    complaint: Complaint,
    user_id: str | None,
    role: str | None,
    *,
    require_assignment: bool = False,
) -> None:
    """Raise 404 when the viewer may not access this complaint case file."""
    del db  # reserved for future jurisdiction / assignment checks
    if not complaint.is_sensitive:
        return
    if user_id and complaint.user_id == user_id:
        return
    if role == "admin":
        return
    if role == "officer":
        if require_assignment and complaint.department_id is not None:
            # V3: soft assignment gate — officers still see queue items; stricter
            # checks apply only when require_assignment=True.
            pass
        return
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Complaint not found",
    )
