from app.core.security import ClerkUser


def test_like_returns_engagement_counts(
    api_client,
    set_api_user,
    complaint,
    db,
):
    set_api_user(ClerkUser(user_id="liker_1", role="citizen"))
    db.commit()

    response = api_client.put(f"/api/v1/complaints/{complaint.id}/like")
    assert response.status_code == 200
    data = response.json()
    assert data["like_count"] == 1
    assert data["affected_count"] == 0
    assert data["comment_count"] == 0
    assert data["viewer_liked"] is True
    assert data["viewer_affected"] is False


def test_unlike_returns_engagement_counts(
    api_client,
    set_api_user,
    complaint,
    db,
):
    set_api_user(ClerkUser(user_id="liker_1", role="citizen"))
    db.commit()

    api_client.put(f"/api/v1/complaints/{complaint.id}/like")
    response = api_client.delete(f"/api/v1/complaints/{complaint.id}/like")
    assert response.status_code == 200
    data = response.json()
    assert data["like_count"] == 0
    assert data["viewer_liked"] is False


def test_engagement_endpoint_for_anonymous(
    api_client,
    set_api_user,
    complaint,
    db,
):
    set_api_user(ClerkUser(user_id="liker_1", role="citizen"))
    db.commit()
    api_client.put(f"/api/v1/complaints/{complaint.id}/like")

    set_api_user(None)
    response = api_client.get(f"/api/v1/complaints/{complaint.id}/engagement")
    assert response.status_code == 200
    data = response.json()
    assert data["like_count"] == 1
    assert data["viewer_liked"] is False
    assert data["viewer_affected"] is False
