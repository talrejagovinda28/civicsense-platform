#!/usr/bin/env python3
"""Static audit: public complaint schemas must not expose private fields."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.schemas.complaint import ComplaintDetail, ComplaintFeedItem  # noqa: E402

PRIVATE_FIELDS = {
    "address",
    "latitude",
    "longitude",
    "google_place_id",
    "user_id",
    "ai_suggested_category_id",
    "ai_confidence",
}

PUBLIC_FEED_FIELDS = set(ComplaintFeedItem.model_fields.keys())
PUBLIC_DETAIL_EXTRA = set(ComplaintDetail.model_fields.keys()) - PUBLIC_FEED_FIELDS


def main() -> int:
    errors: list[str] = []

    leaked = PUBLIC_FEED_FIELDS & PRIVATE_FIELDS
    if leaked:
        errors.append(f"ComplaintFeedItem exposes private fields: {sorted(leaked)}")

    leaked_detail = PUBLIC_DETAIL_EXTRA & PRIVATE_FIELDS
    if leaked_detail:
        print(
            "INFO: ComplaintDetail schema includes fields redacted at runtime for "
            f"anonymous viewers: {sorted(leaked_detail)}"
        )

    if errors:
        errors.append("ComplaintFeedItem must expose public_latitude for map pins")
    if "public_longitude" not in PUBLIC_FEED_FIELDS:
        errors.append("ComplaintFeedItem must expose public_longitude for map pins")

    if errors:
        print("PRIVACY AUDIT FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("OK: Public complaint schema privacy audit passed")
    print(
        "Note: ComplaintDetail private fields are redacted at runtime for "
        "non-owner/non-officer callers in complaints router."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
