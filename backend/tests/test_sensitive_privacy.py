from app.core.security import ClerkUser


def test_anonymous_cannot_access_sensitive_complaint(
    api_client,
    set_api_user,
    complaint,
    sensitive_complaint,
    db,
):
    set_api_user(None)
    db.commit()

    list_response = api_client.get("/api/v1/complaints?city=pune")
    assert list_response.status_code == 200
    listed_ids = {item["id"] for item in list_response.json()["items"]}
    assert str(complaint.id) in listed_ids
    assert str(sensitive_complaint.id) not in listed_ids

    get_response = api_client.get(f"/api/v1/complaints/{sensitive_complaint.id}")
    assert get_response.status_code == 404

    like_response = api_client.put(f"/api/v1/complaints/{sensitive_complaint.id}/like")
    assert like_response.status_code in {401, 403}

    comments_response = api_client.get(
        f"/api/v1/complaints/{sensitive_complaint.id}/comments"
    )
    assert comments_response.status_code == 404


def test_owner_can_access_sensitive_complaint(
    api_client,
    set_api_user,
    sensitive_complaint,
    db,
):
    set_api_user(ClerkUser(user_id="user_owner", role="citizen"))
    db.commit()

    list_response = api_client.get("/api/v1/complaints?city=pune")
    assert list_response.status_code == 200
    listed_ids = {item["id"] for item in list_response.json()["items"]}
    assert str(sensitive_complaint.id) in listed_ids

    get_response = api_client.get(f"/api/v1/complaints/{sensitive_complaint.id}")
    assert get_response.status_code == 200
    assert get_response.json()["title"] == sensitive_complaint.title


def test_other_citizen_cannot_access_sensitive_complaint(
    api_client,
    set_api_user,
    sensitive_complaint,
    db,
):
    set_api_user(ClerkUser(user_id="other_citizen", role="citizen"))
    db.commit()

    list_response = api_client.get("/api/v1/complaints?city=pune")
    assert list_response.status_code == 200
    listed_ids = {item["id"] for item in list_response.json()["items"]}
    assert str(sensitive_complaint.id) not in listed_ids

    get_response = api_client.get(f"/api/v1/complaints/{sensitive_complaint.id}")
    assert get_response.status_code == 404

    like_response = api_client.put(f"/api/v1/complaints/{sensitive_complaint.id}/like")
    assert like_response.status_code == 404

    comment_response = api_client.post(
        f"/api/v1/complaints/{sensitive_complaint.id}/comments",
        json={"body": "Should not post"},
    )
    assert comment_response.status_code == 404
