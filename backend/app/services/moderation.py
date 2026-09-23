from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.community import Comment, ModerationStatus
from app.models.moderation import ModerationAction, ModerationReport, ModerationReportStatus


def create_report(
    db: Session,
    *,
    reporter_id: str,
    target_type: str,
    target_id: str,
    category: str,
    reason: str,
) -> ModerationReport:
    report = ModerationReport(
        reporter_id=reporter_id,
        target_type=target_type,
        target_id=target_id,
        category=category,
        reason=reason.strip(),
        status=ModerationReportStatus.OPEN,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def list_queue(db: Session, *, status_filter: str = "open", limit: int = 50) -> list[ModerationReport]:
    return list(
        db.scalars(
            select(ModerationReport)
            .where(ModerationReport.status == status_filter)
            .order_by(ModerationReport.created_at.asc())
            .limit(limit)
        )
    )


def apply_action(
    db: Session,
    *,
    moderator_id: str,
    report_id: uuid.UUID,
    action: str,
    reason: str | None = None,
) -> ModerationAction:
    report = db.get(ModerationReport, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    mod_action = ModerationAction(
        moderator_id=moderator_id,
        target_type=report.target_type,
        target_id=report.target_id,
        action=action,
        reason=reason or "",
    )
    db.add(mod_action)

    if action == "hide" and report.target_type == "comment":
        comment = db.get(Comment, uuid.UUID(report.target_id))
        if comment is not None:
            comment.moderation_status = ModerationStatus.HIDDEN
    elif action == "restore" and report.target_type == "comment":
        comment = db.get(Comment, uuid.UUID(report.target_id))
        if comment is not None:
            comment.moderation_status = ModerationStatus.VISIBLE

    report.status = ModerationReportStatus.RESOLVED
    db.commit()
    db.refresh(mod_action)
    return mod_action
