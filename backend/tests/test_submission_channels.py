from fastapi.testclient import TestClient

from app.core.deps import get_current_user, get_db
from app.core.security import ClerkUser
from app.main import app
from app.models.authority_channel import ChannelActivation, ChannelMode, ExternalChannel


def test_list_submission_channels_for_owner(db, complaint, city, test_channel):
    # Extra disabled channel should not appear as enabled; DISABLED skipped entirely.
    disabled = ExternalChannel(
        city_id=city.id,
        channel_type="portal",
        destination="https://disabled.example.test",
        mode=ChannelMode.GUIDED_PORTAL,
        activation=ChannelActivation.DISABLED,
        on_behalf_policy="allowed",
        enabled=False,
    )
    db.add(disabled)
    db.flush()

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: ClerkUser(
        user_id=complaint.user_id, role="citizen"
    )
    try:
        with TestClient(app) as client:
            response = client.get(f"/api/v1/complaints/{complaint.id}/submission-channels")
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)
        assert any(item["id"] == str(test_channel.id) for item in body)
        match = next(item for item in body if item["id"] == str(test_channel.id))
        assert match["enabled"] is True
        assert not any(item["id"] == str(disabled.id) for item in body)
    finally:
        app.dependency_overrides.clear()


def test_list_submission_channels_rejects_stranger(db, complaint):
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: ClerkUser(
        user_id="stranger", role="citizen"
    )
    try:
        with TestClient(app) as client:
            response = client.get(f"/api/v1/complaints/{complaint.id}/submission-channels")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_consent_rejects_ineligible_channel(db, complaint, city):
    channel = ExternalChannel(
        city_id=city.id,
        channel_type="email",
        destination="off@example.test",
        mode=ChannelMode.EMAIL,
        activation=ChannelActivation.TEST_ONLY,
        on_behalf_policy="allowed",
        enabled=False,
    )
    db.add(channel)
    db.flush()

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: ClerkUser(
        user_id=complaint.user_id, role="citizen"
    )
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/complaints/{complaint.id}/authorization",
                json={
                    "channel_id": str(channel.id),
                    "disclosure_json": {"summary": "x"},
                },
            )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
