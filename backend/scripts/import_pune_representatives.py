#!/usr/bin/env python3
"""Import Pune 2026 elected representatives from OpenCity CSV."""

from __future__ import annotations

import csv
import uuid
from datetime import datetime, timezone
from pathlib import Path

SOURCE_URL = (
    "https://data.opencity.in/dataset/pmc-election-results-2026/resource/"
    "ac74e3a3-0fce-4ce5-bcdf-b3b6271ae722"
)
VERIFIED_AT = datetime(2026, 1, 15, tzinfo=timezone.utc)


def load_representative_rows(csv_path: Path) -> list[dict]:
    rows: list[dict] = []
    current_ward_no: int | None = None
    current_ward_name = ""

    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            ward_no_raw = (row.get("Ward No.") or "").strip()
            if ward_no_raw:
                current_ward_no = int(float(ward_no_raw))
            ward_name = (row.get("Ward Name") or "").strip()
            if ward_name:
                current_ward_name = ward_name
            if current_ward_no is None:
                continue

            rows.append(
                {
                    "ward_no": current_ward_no,
                    "ward_name": current_ward_name,
                    "seat_label": (row.get("Seat") or "").strip(),
                    "reservation": (row.get("Reservation") or "").strip() or None,
                    "full_name": (row.get("Elected Candidate Name") or "").strip(),
                    "party": (row.get("Party") or "").strip() or None,
                }
            )
    return rows


def build_official_records(
    *,
    city_id: uuid.UUID,
    ward_id_by_number: dict[int, uuid.UUID],
    csv_path: Path,
) -> tuple[list[dict], list[dict]]:
    officials: list[dict] = []
    jurisdictions: list[dict] = []

    for row in load_representative_rows(csv_path):
        ward_id = ward_id_by_number.get(row["ward_no"])
        if ward_id is None:
            raise ValueError(f"Missing electoral ward for ward_no={row['ward_no']}")

        official_id = uuid.uuid4()
        officials.append(
            {
                "id": official_id,
                "city_id": city_id,
                "full_name": row["full_name"],
                "party": row["party"],
                "source_url": SOURCE_URL,
                "source_license": "Public Domain",
                "verified_at": VERIFIED_AT,
            }
        )
        jurisdictions.append(
            {
                "id": uuid.uuid4(),
                "public_official_id": official_id,
                "electoral_ward_id": ward_id,
                "seat_label": row["seat_label"],
                "reservation": row["reservation"],
                "term_label": "2026-2031",
            }
        )

    return officials, jurisdictions


if __name__ == "__main__":
    csv_file = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "data"
        / "cities"
        / "pune"
        / "source"
        / "pmc_election_results_2026.csv"
    )
    rows = load_representative_rows(csv_file)
    print(f"Loaded {len(rows)} representative rows from CSV")
