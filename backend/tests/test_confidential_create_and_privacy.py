import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.core.security import ClerkUser
from app.models.complaint_image import ComplaintImage, MediaVisibility
from app.models.submission import ComplaintTimelineEvent


def _complaint_payload(category_id, *, is_sensitive=False, anonymous_to_public=False):
    return {
        "description": "Confidential bribery report with enough detail for validation",
        "category_id": str(category_id),
        "address": "Near PMC office, Pune",
        "city": "Pune",
        "city_slug": "pune",
        "is_sensitive": is_sensitive,
        "anonymous_to_public": anonymous_to_public,
        "public_caption": "Sensitive civic issue in Pune" if is_sensitive else None,
        "images": [
            {
                "cloudinary_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
                "cloudinary_public_id": "sample",
                "sort_order": 0,
            }
        ],
    }


def test_create_sensitive_complaint_sets_private_images(
    api_client, set_api_user, city, category, db
):
    set_api_user(ClerkUser(user_id="reporter_sensitive", role="citizen"))
    db.commit()

    response = api_client.post(
        "/api/v1/complaints",
        json=_complaint_payload(category.id, is_sensitive=True, anonymous_to_public=True),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["user_id"] is None

    complaint_id = uuid.UUID(body["id"])
    images = db.scalars(
        select(ComplaintImage).where(ComplaintImage.complaint_id == complaint_id)
    ).all()
    assert len(images) == 1
    assert images[0].visibility == MediaVisibility.PRIVATE


def test_officer_queue_includes_sensitive_public_excludes(
    api_client, set_api_user, sensitive_complaint, complaint, db
):
    set_api_user(ClerkUser(user_id="officer_1", role="officer"))
    db.commit()

    queue = api_client.get("/api/v1/complaints/officer/queue?city=Pune")
    assert queue.status_code == 200
    queue_ids = {item["id"] for item in queue.json()}
    assert str(sensitive_complaint.id) in queue_ids
    assert str(complaint.id) in queue_ids

    set_api_user(None)
    public = api_client.get("/api/v1/complaints?city=pune")
    assert public.status_code == 200
    public_ids = {item["id"] for item in public.json()["items"]}
    assert str(sensitive_complaint.id) not in public_ids
    assert str(complaint.id) in public_ids


def test_sensitive_timeline_404_for_unauthorized(
    api_client, set_api_user, sensitive_complaint, db
):
    db.add(
        ComplaintTimelineEvent(
            complaint_id=sensitive_complaint.id,
            actor_id="user_owner",
            actor_kind="citizen",
            event_type="submission_consent_created",
            authenticity_level="system_derived",
            public_payload_redacted=json.dumps({"channel_id": "test"}),
            visibility="public",
            created_at=datetime.now(UTC),
        )
    )
    db.commit()

    set_api_user(None)
    response = api_client.get(f"/api/v1/complaints/{sensitive_complaint.id}/timeline")
    assert response.status_code == 404

    set_api_user(ClerkUser(user_id="user_owner", role="citizen"))
    response = api_client.get(f"/api/v1/complaints/{sensitive_complaint.id}/timeline")
    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1


def test_officer_sees_sensitive_timeline(
    api_client, set_api_user, sensitive_complaint, db
):
    db.add(
        ComplaintTimelineEvent(
            complaint_id=sensitive_complaint.id,
            actor_id="user_owner",
            actor_kind="citizen",
            event_type="submission_consent_created",
            authenticity_level="system_derived",
            public_payload_redacted=json.dumps({"note": "internal"}),
            visibility="owner",
            created_at=datetime.now(UTC),
        )
    )
    db.commit()

    set_api_user(ClerkUser(user_id="officer_1", role="officer"))
    response = api_client.get(f"/api/v1/complaints/{sensitive_complaint.id}/timeline")
    assert response.status_code == 200
    assert response.json()["items"]
