import json
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.core.security import ClerkUser
from app.main import app
from app.models.authority_channel import ChannelActivation, ChannelMode, ExternalChannel
from app.models.submission import SubmissionConsent
from app.services.submission_engine import IntentStatus, create_intent_and_dispatch


@pytest.fixture
def disabled_channel(db, city):
    row = ExternalChannel(
        city_id=city.id,
        channel_type="email",
        destination="disabled@example.test",
        mode=ChannelMode.EMAIL,
        activation=ChannelActivation.DISABLED,
        on_behalf_policy="allowed",
        enabled=False,
    )
    db.add(row)
    db.flush()
    return row


@pytest.fixture
def disabled_consent(db, complaint, disabled_channel):
    row = SubmissionConsent(
        complaint_id=complaint.id,
        user_id=complaint.user_id,
        channel_id=disabled_channel.id,
        payload_hash="disabled-hash",
        disclosure_json=json.dumps({"summary": "Disabled channel test"}),
        version="1",
        authorized_at=datetime.now(UTC),
        scope="single_dispatch",
    )
    db.add(row)
    db.flush()
    return row


def test_disabled_channel_dispatch_fails_in_production(
    db, complaint, disabled_consent, monkeypatch
):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "CIVICSENSE_ALLOW_FAKE_ADAPTERS", False)

    result = create_intent_and_dispatch(
        db,
        user_id=complaint.user_id,
        complaint_id=complaint.id,
        consent_id=disabled_consent.id,
        idempotency_key="prod-disabled-001",
        _test_scenario="accept_registered",
    )
    assert result["code"] == "CHANNEL_NOT_ENABLED"
    assert result["status"] == IntentStatus.FAILED


def test_dispatch_rejects_test_scenario_field(db, complaint, consent, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "CIVICSENSE_ALLOW_FAKE_ADAPTERS", False)

    def override_db():
        yield db

    def override_user():
        return ClerkUser(user_id=complaint.user_id, role="citizen")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/complaints/{complaint.id}/submissions",
                json={
                    "consent_id": str(consent.id),
                    "idempotency_key": "api-scenario-reject",
                    "test_scenario": "accept_registered",
                },
            )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
