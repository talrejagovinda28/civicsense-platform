import json
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from app.models.complaint import Complaint, ComplaintStatus
from app.models.submission import SubmissionConsent
from app.services.submission_engine import create_intent_and_dispatch


@pytest.fixture
def other_complaint(db, city, category):
    row = Complaint(
        user_id="user_other",
        title="Other user complaint",
        description="Another pothole",
        status=ComplaintStatus.SUBMITTED,
        category_id=category.id,
        address="MG Road, Pune",
        city="Pune",
        city_id=city.id,
        is_sensitive=False,
    )
    db.add(row)
    db.flush()
    return row


@pytest.fixture
def other_consent(db, other_complaint, test_channel):
    row = SubmissionConsent(
        complaint_id=other_complaint.id,
        user_id=other_complaint.user_id,
        channel_id=test_channel.id,
        payload_hash="other-hash",
        disclosure_json=json.dumps({"summary": "Other user complaint"}),
        version="1",
        authorized_at=datetime.now(UTC),
        scope="single_dispatch",
    )
    db.add(row)
    db.flush()
    return row


def test_idempotency_key_cannot_be_replayed_by_other_user(
    db, complaint, consent, other_complaint, other_consent
):
    key = "shared-idempotency-key"
    create_intent_and_dispatch(
        db,
        user_id=complaint.user_id,
        complaint_id=complaint.id,
        consent_id=consent.id,
        idempotency_key=key,
        _test_scenario="timeout_unknown",
    )

    with pytest.raises(HTTPException) as exc_info:
        create_intent_and_dispatch(
            db,
            user_id=other_complaint.user_id,
            complaint_id=other_complaint.id,
            consent_id=other_consent.id,
            idempotency_key=key,
            _test_scenario="timeout_unknown",
        )

    assert exc_info.value.status_code == 409
