from sqlalchemy import func, select

from app.models.reputation import ReputationLedger
from app.services.reputation import COMPLAINT_XP, grant_xp, reverse_xp, get_lifetime_xp


def test_grant_xp_idempotent(db):
    user_id = "user_xp_test"
    first = grant_xp(
        db,
        user_id=user_id,
        event_key="complaint:123",
        kind="complaint",
        delta=COMPLAINT_XP,
        source_entity_id="123",
    )
    db.commit()
    assert first is not None

    second = grant_xp(
        db,
        user_id=user_id,
        event_key="complaint:123",
        kind="complaint",
        delta=COMPLAINT_XP,
        source_entity_id="123",
    )
    db.commit()
    assert second is None

    count = db.scalar(select(func.count()).select_from(ReputationLedger))
    assert count == 1
    assert get_lifetime_xp(db, user_id) == COMPLAINT_XP


def test_reverse_xp_reduces_lifetime(db):
    user_id = "user_reverse"
    grant_xp(
        db,
        user_id=user_id,
        event_key="complaint:456",
        kind="complaint",
        delta=COMPLAINT_XP,
    )
    db.commit()
    reverse_xp(db, event_key="complaint:456", reason="abuse confirmed")
    db.commit()
    assert get_lifetime_xp(db, user_id) == 0
