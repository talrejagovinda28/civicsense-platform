"""Verify all API endpoints respond correctly."""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

warnings.filterwarnings("ignore", category=DeprecationWarning)

from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.main import app  # noqa: E402

EXPECTED_API_PATHS = {
    "GET /api/v1/admin/stats",
    "GET /api/v1/health",
    "GET /api/v1/me",
    "GET /api/v1/categories",
    "GET /api/v1/complaints",
    "GET /api/v1/complaints/mine",
    "GET /api/v1/complaints/officer/queue",
    "GET /api/v1/complaints/{complaint_id}",
    "PATCH /api/v1/admin/users/{user_id}/role",
    "PATCH /api/v1/complaints/{complaint_id}/status",
    "POST /api/v1/complaints",
    "POST /api/v1/complaints/suggest-category",
    "POST /api/v1/uploads/cloudinary-signature",
}


def _collect_routes() -> set[str]:
    openapi = app.openapi()
    routes: set[str] = set()
    for path, methods in openapi["paths"].items():
        for method in methods:
            if method == "head":
                continue
            routes.add(f"{method.upper()} {path}")
    routes.add("GET /")
    return routes


def verify_routes_registered() -> None:
    routes = _collect_routes()
    missing = EXPECTED_API_PATHS - routes
    if missing:
        raise SystemExit(f"Missing routes: {sorted(missing)}")

    print("Routes OK:")
    for path in sorted(EXPECTED_API_PATHS):
        print(f"  {path}")


def _db_configured() -> bool:
    url = settings.DATABASE_URL
    placeholders = ("YOUR_PASSWORD", "YOUR_PROJECT", "localhost")
    return not any(value in url for value in placeholders)


def verify_endpoints(client: TestClient) -> None:
    response = client.get("/")
    if response.status_code != 200:
        raise SystemExit(f"GET / failed: {response.status_code}")
    data = response.json()
    if data != {"name": "CivicSense", "version": "0.1.0", "status": "running"}:
        raise SystemExit(f"GET / unexpected body: {data}")
    print("GET / — OK")

    response = client.get("/api/v1/health")
    if response.status_code != 200:
        raise SystemExit(f"GET /api/v1/health failed: {response.status_code}")
    health = response.json()
    if health.get("status") != "ok":
        raise SystemExit(f"GET /api/v1/health unexpected body: {health}")
    print(f"GET /api/v1/health — OK (database={health.get('database')})")

    response = client.get("/api/v1/me")
    if response.status_code not in {401, 403}:
        msg = f"GET /api/v1/me should require auth, got {response.status_code}"
        raise SystemExit(msg)
    print(f"GET /api/v1/me — OK ({response.status_code} without token)")

    response = client.post(
        "/api/v1/complaints/suggest-category", json={"photo_urls": []}
    )
    if response.status_code not in {401, 403, 422}:
        msg = (
            "POST /api/v1/complaints/suggest-category should reject unauthenticated "
            f"or invalid body, got {response.status_code}"
        )
        raise SystemExit(msg)
    print(
        "POST /api/v1/complaints/suggest-category — OK "
        f"({response.status_code} without token)"
    )

    response = client.post("/api/v1/complaints", json={})
    if response.status_code not in {401, 403, 422}:
        msg = (
            "POST /api/v1/complaints should reject unauthenticated or invalid body, "
            f"got {response.status_code}"
        )
        raise SystemExit(msg)
    print(f"POST /api/v1/complaints — OK ({response.status_code} without token)")

    response = client.post("/api/v1/uploads/cloudinary-signature")
    if response.status_code not in {401, 403}:
        msg = (
            "POST /api/v1/uploads/cloudinary-signature should require auth, "
            f"got {response.status_code}"
        )
        raise SystemExit(msg)
    print(
        "POST /api/v1/uploads/cloudinary-signature — OK "
        f"({response.status_code} without token)"
    )

    if not _db_configured():
        print(
            "\nDB endpoints skipped — set a real DATABASE_URL in .env for full verify."
        )
        return

    response = client.get("/api/v1/categories")
    if response.status_code != 200:
        raise SystemExit(f"GET /api/v1/categories failed: {response.status_code}")
    print(f"GET /api/v1/categories — OK ({len(response.json())} categories)")

    response = client.get("/api/v1/complaints")
    if response.status_code != 200:
        raise SystemExit(f"GET /api/v1/complaints failed: {response.status_code}")
    feed = response.json()
    if not {"items", "total", "skip", "limit"}.issubset(feed):
        raise SystemExit(f"GET /api/v1/complaints unexpected body keys: {feed.keys()}")
    print(f"GET /api/v1/complaints — OK (total={feed['total']})")

    response = client.get("/api/v1/complaints/mine")
    if response.status_code not in {401, 403}:
        msg = (
            "GET /api/v1/complaints/mine should require auth, "
            f"got {response.status_code}"
        )
        raise SystemExit(msg)
    print(f"GET /api/v1/complaints/mine — OK ({response.status_code} without token)")

    fake_id = "00000000-0000-0000-0000-000000000001"
    response = client.get(f"/api/v1/complaints/{fake_id}")
    if response.status_code != 404:
        msg = (
            "GET /api/v1/complaints/{id} should 404 for missing id, "
            f"got {response.status_code}"
        )
        raise SystemExit(msg)
    print("GET /api/v1/complaints/{id} — OK (404 for missing)")

    response = client.get("/api/v1/complaints/officer/queue")
    if response.status_code not in {401, 403}:
        msg = (
            "GET /api/v1/complaints/officer/queue should require auth, "
            f"got {response.status_code}"
        )
        raise SystemExit(msg)
    print(
        "GET /api/v1/complaints/officer/queue — OK "
        f"({response.status_code} without token)"
    )

    response = client.patch(
        f"/api/v1/complaints/{fake_id}/status",
        json={"status": "in_progress"},
    )
    if response.status_code not in {401, 403, 404, 422}:
        msg = (
            "PATCH /api/v1/complaints/{id}/status should reject unauthenticated "
            f"or invalid request, got {response.status_code}"
        )
        raise SystemExit(msg)
    print(
        "PATCH /api/v1/complaints/{id}/status — OK "
        f"({response.status_code} without token)"
    )

    response = client.get("/api/v1/admin/stats")
    if response.status_code not in {401, 403}:
        msg = (
            "GET /api/v1/admin/stats should require auth, "
            f"got {response.status_code}"
        )
        raise SystemExit(msg)
    print(f"GET /api/v1/admin/stats — OK ({response.status_code} without token)")

    response = client.patch(
        f"/api/v1/admin/users/{fake_id}/role",
        json={"role": "officer"},
    )
    if response.status_code not in {401, 403, 404, 422, 502, 503}:
        msg = (
            "PATCH /api/v1/admin/users/{id}/role should reject unauthenticated "
            f"or invalid request, got {response.status_code}"
        )
        raise SystemExit(msg)
    print(
        "PATCH /api/v1/admin/users/{id}/role — OK "
        f"({response.status_code} without token)"
    )


if __name__ == "__main__":
    verify_routes_registered()
    with TestClient(app) as client:
        verify_endpoints(client)
    print("\nAll endpoint checks passed.")
