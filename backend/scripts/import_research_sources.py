"""
Admin-reviewed research CSV importer.

Upserts authority_sources with status=research_only.
NEVER enables external_channels or invents contacts as live recipients.

Usage (isolated DB only):
  py -m scripts.import_research_sources --dry-run
  py -m scripts.import_research_sources --apply
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESEARCH_DIR = ROOT / "data" / "research"
AUDIT_PATH = ROOT / "data" / "import_audit.json"


def _hash_row(row: dict[str, str]) -> str:
    payload = json.dumps(row, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def load_csv(name: str) -> list[dict[str, str]]:
    path = RESEARCH_DIR / name
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build_source_records() -> list[dict]:
    records: list[dict] = []
    mapping = [
        ("reporting_channels_RESEARCH_ONLY.csv", "reporting_channel"),
        ("pmc_ward_offices_RESEARCH_ONLY.csv", "ward_office"),
        ("elected_RESEARCH_ONLY.csv", "elected"),
        ("appointed_officers_RESEARCH_ONLY.csv", "appointed_officer"),
        ("critical_gaps_RESEARCH_ONLY.csv", "critical_gap"),
    ]
    for filename, evidence_type in mapping:
        for row in load_csv(filename):
            origin = (
                row.get("source_url")
                or row.get("url")
                or row.get("source")
                or f"research://{filename}"
            )
            title = (
                row.get("title")
                or row.get("name")
                or row.get("office_name")
                or row.get("channel_name")
                or row.get("gap")
                or evidence_type
            )
            records.append(
                {
                    "origin_url": origin[:500],
                    "title": str(title)[:300],
                    "publisher": "CivicSense research pack 2026-09-22",
                    "evidence_type": evidence_type,
                    "validation_note": f"row_hash={_hash_row(row)}; RESEARCH_ONLY; not for auto-routing",
                    "status": "research_only",
                    "content_fingerprint": _hash_row(row),
                }
            )
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true", help="Write authority_sources rows")
    args = parser.parse_args()

    records = build_source_records()
    print(f"Prepared {len(records)} research-only source records")

    if args.apply:
        from sqlalchemy import select

        from app.db.session import SessionLocal
        from app.models.authority_channel import AuthoritySource, AuthoritySourceStatus

        db = SessionLocal()
        inserted = 0
        skipped = 0
        try:
            for item in records:
                existing = db.scalar(
                    select(AuthoritySource).where(
                        AuthoritySource.origin_url == item["origin_url"],
                        AuthoritySource.title == item["title"],
                    )
                )
                if existing:
                    skipped += 1
                    continue
                db.add(
                    AuthoritySource(
                        origin_url=item["origin_url"],
                        title=item["title"],
                        publisher=item["publisher"],
                        evidence_type=item["evidence_type"],
                        validation_note=item["validation_note"],
                        status=AuthoritySourceStatus.RESEARCH_ONLY,
                        checked_at=datetime.now(timezone.utc),
                    )
                )
                inserted += 1
            db.commit()
            print(f"Inserted {inserted}, skipped duplicates {skipped}")
            print("WARNING: No external_channels were enabled.")
        finally:
            db.close()
    else:
        print("Dry-run only. Pass --apply against an isolated DB to persist research sources.")

    AUDIT_PATH.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "prepared_records": len(records),
                "applied": bool(args.apply),
                "policy": "RESEARCH_ONLY",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
