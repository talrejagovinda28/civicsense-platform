from app.core.security import ClerkUser


def test_feed_items_include_complaint_id_and_exclude_sensitive(
    api_client,
    set_api_user,
    complaint,
    sensitive_complaint,
    db,
):
    set_api_user(None)
    db.commit()

    response = api_client.get("/api/v1/feed?city=pune")
    assert response.status_code == 200
    payload = response.json()
    assert payload["items"]

    complaint_ids = {item["complaint_id"] for item in payload["items"]}
    assert str(complaint.id) in complaint_ids
    assert str(sensitive_complaint.id) not in complaint_ids

    for item in payload["items"]:
        assert item["complaint_id"]
        assert item["kind"] in {"complaint", "update"}
        assert "like_count" in item
        assert "comment_count" in item
        assert "locality_label" in item
        assert item["responsibility_line"]


def test_public_complaints_list_excludes_sensitive(
    api_client,
    set_api_user,
    complaint,
    sensitive_complaint,
    db,
):
    set_api_user(None)
    db.commit()

    response = api_client.get("/api/v1/complaints?city=pune")
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert str(complaint.id) in ids
    assert str(sensitive_complaint.id) not in ids


def test_owner_sees_sensitive_in_complaints_list(
    api_client,
    set_api_user,
    sensitive_complaint,
    db,
):
    set_api_user(ClerkUser(user_id="user_owner", role="citizen"))
    db.commit()

    response = api_client.get("/api/v1/complaints?city=pune")
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert str(sensitive_complaint.id) in ids
