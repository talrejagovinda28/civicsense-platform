import json
from datetime import UTC, datetime

import pytest

from app.models.authority_channel import ChannelActivation, ChannelMode, ExternalChannel
from app.models.submission import SubmissionConsent
from app.services.adapters.registry import ChannelNotEnabled, get_adapter
from app.services.submission_engine import IntentStatus, create_intent_and_dispatch


@pytest.fixture
def disabled_guided_channel(db, city):
    row = ExternalChannel(
        city_id=city.id,
        channel_type="portal",
        destination="https://pmc.example.test/grievance",
        mode=ChannelMode.GUIDED_PORTAL,
        activation=ChannelActivation.DISABLED,
        on_behalf_policy="allowed",
        enabled=False,
    )
    db.add(row)
    db.flush()
    return row


@pytest.fixture
def disabled_guided_consent(db, complaint, disabled_guided_channel):
    row = SubmissionConsent(
        complaint_id=complaint.id,
        user_id=complaint.user_id,
        channel_id=disabled_guided_channel.id,
        payload_hash="disabled-guided-hash",
        disclosure_json=json.dumps({"summary": "PMC handoff"}),
        version="1",
        authorized_at=datetime.now(UTC),
        scope="single_dispatch",
    )
    db.add(row)
    db.flush()
    return row


@pytest.fixture
def enabled_guided_channel(db, city):
    row = ExternalChannel(
        city_id=city.id,
        channel_type="portal",
        destination="https://pmc.example.test/grievance-live",
        mode=ChannelMode.GUIDED_PORTAL,
        activation=ChannelActivation.MANUAL,
        on_behalf_policy="allowed",
        enabled=True,
    )
    db.add(row)
    db.flush()
    return row


@pytest.fixture
def enabled_guided_consent(db, complaint, enabled_guided_channel):
    row = SubmissionConsent(
        complaint_id=complaint.id,
        user_id=complaint.user_id,
        channel_id=enabled_guided_channel.id,
        payload_hash="enabled-guided-hash",
        disclosure_json=json.dumps({"summary": "PMC handoff live"}),
        version="1",
        authorized_at=datetime.now(UTC),
        scope="single_dispatch",
    )
    db.add(row)
    db.flush()
    return row


def test_disabled_guided_channel_returns_not_enabled(db, complaint, disabled_guided_consent):
    result = create_intent_and_dispatch(
        db,
        user_id=complaint.user_id,
        complaint_id=complaint.id,
        consent_id=disabled_guided_consent.id,
        idempotency_key="disabled-guided-001",
    )
    assert result["code"] == "CHANNEL_NOT_ENABLED"
    assert result["status"] == IntentStatus.FAILED


def test_disabled_guided_get_adapter_raises(db, disabled_guided_channel):
    with pytest.raises(ChannelNotEnabled):
        get_adapter(disabled_guided_channel)


def test_enabled_guided_channel_user_action_required(db, complaint, enabled_guided_consent):
    result = create_intent_and_dispatch(
        db,
        user_id=complaint.user_id,
        complaint_id=complaint.id,
        consent_id=enabled_guided_consent.id,
        idempotency_key="enabled-guided-001",
    )
    assert result.get("code") is None
    assert result["status"] == IntentStatus.USER_ACTION_REQUIRED
    assert result["outcome_state"] == "user_action_required"
