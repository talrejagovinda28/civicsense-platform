from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.reputation import BadgeAward, ReputationLedger, ReputationStatus

COMPLAINT_XP = 50
RESOLUTION_XP = 100
EVIDENCE_XP = 25
DM_UNLOCK = 200
GROUP_UNLOCK = 500

_BADGE_THRESHOLDS: dict[str, int] = {
    "first_report": COMPLAINT_XP,
    "trusted_reporter": COMPLAINT_XP * 5,
    "resolution_helper": RESOLUTION_XP,
}


def grant_xp(
    db: Session,
    *,
    user_id: str,
    event_key: str,
    kind: str,
    delta: int,
    source_entity_id: str | None = None,
) -> ReputationLedger | None:
    existing = db.scalar(
        select(ReputationLedger).where(ReputationLedger.event_key == event_key)
    )
    if existing is not None:
        return None

    entry = ReputationLedger(
        user_id=user_id,
        event_key=event_key,
        kind=kind,
        delta=delta,
        source_entity_id=source_entity_id,
        status=ReputationStatus.GRANTED,
        created_at=datetime.now(UTC),
    )
    db.add(entry)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return None

    maybe_award_badges(db, user_id)
    return entry


def reverse_xp(
    db: Session,
    *,
    event_key: str,
    reason: str,
) -> ReputationLedger | None:
    del reason
    entry = db.scalar(
        select(ReputationLedger).where(
            ReputationLedger.event_key == event_key,
            ReputationLedger.status == ReputationStatus.GRANTED,
        )
    )
    if entry is None:
        return None

    entry.status = ReputationStatus.REVERSED
    db.flush()
    return entry


def get_lifetime_xp(db: Session, user_id: str) -> int:
    total = db.scalar(
        select(func.coalesce(func.sum(ReputationLedger.delta), 0)).where(
            ReputationLedger.user_id == user_id,
            ReputationLedger.status == ReputationStatus.GRANTED,
        )
    )
    return int(total or 0)


def can_initiate_dm(db: Session, user_id: str) -> bool:
    return get_lifetime_xp(db, user_id) >= DM_UNLOCK


def can_create_group(db: Session, user_id: str) -> bool:
    return get_lifetime_xp(db, user_id) >= GROUP_UNLOCK


def maybe_award_badges(db: Session, user_id: str) -> list[BadgeAward]:
    lifetime = get_lifetime_xp(db, user_id)
    awarded: list[BadgeAward] = []

    for badge_code, threshold in _BADGE_THRESHOLDS.items():
        if lifetime < threshold:
            continue
        existing = db.scalar(
            select(BadgeAward).where(
                BadgeAward.user_id == user_id,
                BadgeAward.badge_code == badge_code,
            )
        )
        if existing is not None:
            continue
        badge = BadgeAward(
            user_id=user_id,
            badge_code=badge_code,
            source_event_key=f"badge:{badge_code}:{user_id}",
            granted_at=datetime.now(UTC),
        )
        db.add(badge)
        try:
            db.flush()
            awarded.append(badge)
        except IntegrityError:
            db.rollback()
    return awarded
