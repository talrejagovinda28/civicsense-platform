import pytest
from fastapi.testclient import TestClient

from app.core.deps import get_current_user, get_db
from app.core.security import ClerkUser
from app.main import app


@pytest.fixture
def api_client(db):
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def _set_user(user_id: str, role: str) -> None:
    app.dependency_overrides[get_current_user] = lambda: ClerkUser(user_id=user_id, role=role)


def test_stranger_cannot_submit_resolution_evidence(api_client, complaint):
    _set_user("stranger_user", "citizen")
    response = api_client.post(
        f"/api/v1/complaints/{complaint.id}/resolution-evidence",
        json={"assertion": "I fixed it somehow"},
    )
    assert response.status_code in {403, 404}


def test_owner_can_submit_resolution_evidence(api_client, complaint):
    _set_user(complaint.user_id, "citizen")
    response = api_client.post(
        f"/api/v1/complaints/{complaint.id}/resolution-evidence",
        json={"assertion": "Pothole refilled by ward team"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["submitter_id"] == complaint.user_id
    assert body["assertion"]
