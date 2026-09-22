import json
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.deps import get_current_user, get_db, require_admin
from app.core.security import ClerkUser
from app.main import app
from app.models.authority_channel import ChannelActivation, ChannelMode, ExternalChannel
from app.models.external_submission import ExternalSubmissionStatus
from app.models.submission import (
    ComplaintTimelineEvent,
    ExternalReference,
    SubmissionConsent,
    SubmissionIntent,
)
from app.services.external_submissions import to_external_submission_response
from app.services.submission_engine import IntentStatus, attach_reference


@pytest.fixture
def guided_consent(db, complaint, city):
    channel = ExternalChannel(
        city_id=city.id,
        channel_type="portal",
        destination="https://portal.example.test/grievance",
        mode=ChannelMode.GUIDED_PORTAL,
        activation=ChannelActivation.MANUAL,
        on_behalf_policy="allowed",
        enabled=True,
    )
    db.add(channel)
    db.flush()
    consent = SubmissionConsent(
        complaint_id=complaint.id,
        user_id=complaint.user_id,
        channel_id=channel.id,
        payload_hash="guided-hash",
        disclosure_json=json.dumps({"summary": "Test"}),
        version="1",
        authorized_at=datetime.now(UTC),
        scope="single_dispatch",
    )
    db.add(consent)
    db.flush()
    return consent, channel


@pytest.fixture
def guided_intent(db, complaint, guided_consent):
    consent, channel = guided_consent
    intent = SubmissionIntent(
        complaint_id=complaint.id,
        consent_id=consent.id,
        channel_id=channel.id,
        destination_snapshot=channel.destination,
        payload_hash=consent.payload_hash,
        idempotency_key="guided-intent-key",
        status=IntentStatus.USER_ACTION_REQUIRED,
    )
    db.add(intent)
    db.flush()
    return intent


def test_attach_reference_stores_unverified(db, complaint, guided_intent):
    ref = attach_reference(
        db,
        user_id=complaint.user_id,
        intent_id=guided_intent.id,
        reference_value="PMC-12345",
        reference_type="official_token",
    )
    assert ref.reference_type == "user_provided_unverified"
    assert ref.verified_at is None

    events = db.scalars(
        select(ComplaintTimelineEvent).where(
            ComplaintTimelineEvent.complaint_id == complaint.id
        )
    ).all()
    event_types = {event.event_type for event in events}
    assert "user_provided_unverified_reference" in event_types


def test_save_external_token_includes_user_reported_note(db, complaint):
    from app.core.security import ClerkUser
    from app.schemas.external_submission import ExternalSubmissionTokenRequest
    from app.services.external_submissions import save_external_token

    record = save_external_token(
        db,
        complaint,
        ClerkUser(user_id=complaint.user_id, role="citizen"),
        ExternalSubmissionTokenRequest(external_token="PMC-99999"),
    )
    response = to_external_submission_response(record)
    assert record.status == ExternalSubmissionStatus.TOKEN_RECEIVED
    assert response.reference_note is not None
    assert "User-reported" in response.reference_note


def test_admin_verify_reference(db, complaint, guided_intent):
    ref = attach_reference(
        db,
        user_id=complaint.user_id,
        intent_id=guided_intent.id,
        reference_value="PMC-VERIFY-ME",
    )

    def override_db():
        yield db

    def override_admin():
        return ClerkUser(user_id="admin_1", role="admin")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[require_admin] = override_admin
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/submissions/{guided_intent.id}/verify-reference",
                json={"reference_id": str(ref.id)},
            )
        assert response.status_code == 200
        assert response.json()["verified_at"] is not None
    finally:
        app.dependency_overrides.clear()

    verified = db.get(ExternalReference, ref.id)
    assert verified.verified_at is not None
