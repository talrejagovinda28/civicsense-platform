import pytest
from fastapi.testclient import TestClient

from app.core.deps import get_current_user, get_db
from app.core.security import ClerkUser
from app.main import app
from app.models.resolution import ResolutionEvidence
from app.services.resolution import independent_review


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


def test_officer_cannot_verify_without_evidence(api_client, complaint):
    _set_user("officer_no_evidence", "officer")
    response = api_client.post(
        f"/api/v1/complaints/{complaint.id}/resolution-review",
        json={"decision": "verified_resolved", "reason": "Looks fixed"},
    )
    assert response.status_code == 422


def test_officer_cannot_verify_own_evidence(db, complaint):
    evidence = ResolutionEvidence(
        complaint_id=complaint.id,
        submitter_id="officer_self",
        submitter_role="officer",
        assertion="I fixed it",
    )
    db.add(evidence)
    db.flush()

    with pytest.raises(__import__("fastapi").HTTPException) as exc_info:
        independent_review(
            db,
            reviewer_id="officer_self",
            reviewer_role="officer",
            complaint_id=complaint.id,
            evidence_id=evidence.id,
            decision="verified_resolved",
        )
    assert exc_info.value.status_code == 403


def test_officer_can_verify_with_other_evidence(db, complaint):
    evidence = ResolutionEvidence(
        complaint_id=complaint.id,
        submitter_id="citizen_fixer",
        submitter_role="citizen",
        assertion="Photo shows repair completed",
    )
    db.add(evidence)
    db.flush()

    review = independent_review(
        db,
        reviewer_id="officer_reviewer",
        reviewer_role="officer",
        complaint_id=complaint.id,
        evidence_id=evidence.id,
        decision="verified_resolved",
    )
    assert review.decision == "verified_resolved"


def test_admin_can_verify_without_evidence(db, complaint):
    review = independent_review(
        db,
        reviewer_id="admin_1",
        reviewer_role="admin",
        complaint_id=complaint.id,
        evidence_id=None,
        decision="verified_resolved",
    )
    assert review.decision == "verified_resolved"
