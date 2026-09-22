from __future__ import annotations

import json
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.submission import ComplaintTimelineEvent, TimelineVisibility
from app.services.access import assert_complaint_case_access, is_privileged_role


def _viewer_visibility_levels(
    *,
    user_id: str | None,
    role: str | None,
    complaint_owner_id: str,
) -> set[str]:
    if user_id == complaint_owner_id or is_privileged_role(role):
        return {
            TimelineVisibility.PUBLIC,
            TimelineVisibility.OWNER,
            TimelineVisibility.INTERNAL,
        }
    return {TimelineVisibility.PUBLIC}


def list_timeline_events(
    db: Session,
    *,
    complaint,
    user_id: str | None,
    role: str | None,
) -> list[dict]:
    assert_complaint_case_access(db, complaint, user_id, role)

    allowed = _viewer_visibility_levels(
        user_id=user_id,
        role=role,
        complaint_owner_id=complaint.user_id,
    )
    events = db.scalars(
        select(ComplaintTimelineEvent)
        .where(ComplaintTimelineEvent.complaint_id == complaint.id)
        .order_by(ComplaintTimelineEvent.created_at.asc())
    ).all()

    items: list[dict] = []
    for event in events:
        if event.visibility not in allowed:
            continue
        payload = None
        if event.public_payload_redacted:
            try:
                payload = json.loads(event.public_payload_redacted)
            except json.JSONDecodeError:
                payload = {"raw": event.public_payload_redacted}
        items.append(
            {
                "id": event.id,
                "event_type": event.event_type,
                "actor_kind": event.actor_kind,
                "authenticity_level": event.authenticity_level,
                "public_payload": payload,
                "created_at": event.created_at,
            }
        )
    return items
