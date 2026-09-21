import pytest
from fastapi import HTTPException

from app.services.messaging import create_direct
from app.services.reputation import COMPLAINT_XP, DM_UNLOCK, grant_xp


def test_dm_requires_xp(db):
    with pytest.raises(HTTPException) as exc:
        create_direct(db, sender_id="low_xp_user", recipient_id="recipient_user")
    assert exc.value.status_code == 403

    grant_xp(
        db,
        user_id="eligible_user",
        event_key="complaint:gate-1",
        kind="complaint",
        delta=DM_UNLOCK,
    )
    db.commit()

    result = create_direct(db, sender_id="eligible_user", recipient_id="recipient_user")
    assert result["type"] in {"conversation", "request"}
