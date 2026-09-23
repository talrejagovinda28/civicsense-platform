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


def test_citizen_cannot_call_independent_review(api_client, complaint):
    _set_user("citizen_reviewer", "citizen")
    response = api_client.post(
        f"/api/v1/complaints/{complaint.id}/resolution-review",
        json={"decision": "verified_resolved", "reason": "looks fixed"},
    )
    assert response.status_code == 403


def test_evidence_submit_rejects_spoofed_submitter_role(api_client, complaint):
    _set_user(complaint.user_id, "citizen")
    response = api_client.post(
        f"/api/v1/complaints/{complaint.id}/resolution-evidence",
        json={
            "assertion": "Fixed the pothole",
            "submitter_role": "officer",
        },
    )
    assert response.status_code == 422
