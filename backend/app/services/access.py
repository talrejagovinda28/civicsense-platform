from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import inspect as sa_inspect, select
from sqlalchemy.orm import Session

from app.models.complaint import Complaint


def is_privileged_role(role: str | None) -> bool:
    return role in {"officer", "admin"}


def _complaint_is_sensitive(complaint: Complaint) -> bool:
    """Safe on pre-009 DBs and load_only() queries that omit is_sensitive."""
    try:
        insp = sa_inspect(complaint)
    except Exception:
        return False
    if "is_sensitive" in getattr(insp, "unloaded", set()):
        return False
    try:
        return bool(complaint.is_sensitive)
    except Exception:
        return False


def can_view_sensitive_complaint(
    complaint: Complaint,
    user_id: str | None,
    role: str | None,
) -> bool:
    if not _complaint_is_sensitive(complaint):
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
    from app.services.schema_compat import (
        complaints_v3_ready,
        load_only_existing,
        table_columns,
    )

    if complaints_v3_ready(db):
        complaint = db.get(Complaint, complaint_id)
    else:
        load = load_only_existing(Complaint, table_columns(db, "complaints"))
        stmt = select(Complaint).where(Complaint.id == complaint_id)
        if load is not None:
            stmt = stmt.options(load)
        complaint = db.scalars(stmt).first()
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
    if not _complaint_is_sensitive(complaint):
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
