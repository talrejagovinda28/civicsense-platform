#!/usr/bin/env python3
"""Validate CivicSense Pune civic data counts and configuration."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import create_engine, func, select, text

BACKEND_ROOT = Path(__file__).resolve().parents[1]
GEOJSON_PATH = BACKEND_ROOT / "app" / "data" / "cities" / "pune" / "electoral_wards_2025.geojson"


def _load_geojson_count() -> int:
    data = json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))
    return len(data.get("features", []))


def main() -> int:
    errors: list[str] = []

    feature_count = _load_geojson_count()
    if feature_count != 41:
        errors.append(f"GeoJSON feature count expected 41, got {feature_count}")

    try:
        from app.core.config import settings
        from app.models.category import Category
        from app.models.city import City
        from app.models.electoral_ward import ElectoralWard
        from app.models.public_official import OfficialJurisdiction
        from app.models.routing import CategoryRoutingRule, RoutingChannel
        from app.models.ward_office import WardOffice
        from sqlalchemy.orm import Session

        engine = create_engine(settings.database_url)
        with Session(engine) as db:
            pune = db.scalar(select(City).where(City.slug == "pune"))
            if pune is None:
                errors.append("Pune city record missing")
            else:
                ward_count = db.scalar(
                    select(func.count())
                    .select_from(ElectoralWard)
                    .where(ElectoralWard.city_id == pune.id)
                )
                if ward_count != 41:
                    errors.append(f"electoral_wards expected 41, got {ward_count}")

                office_count = db.scalar(
                    select(func.count())
                    .select_from(WardOffice)
                    .where(WardOffice.city_id == pune.id)
                )
                if office_count != 15:
                    errors.append(f"ward_offices expected 15, got {office_count}")

                rep_count = db.scalar(select(func.count()).select_from(OfficialJurisdiction))
                if rep_count != 165:
                    errors.append(f"official_jurisdictions expected 165, got {rep_count}")

                active_channels = db.scalar(
                    select(func.count())
                    .select_from(RoutingChannel)
                    .where(
                        RoutingChannel.city_id == pune.id,
                        RoutingChannel.is_active.is_(True),
                    )
                )
                if not active_channels:
                    errors.append("No active routing channels for Pune")

                categories = db.scalars(select(Category).where(Category.is_active.is_(True))).all()
                for category in categories:
                    mapped = db.scalar(
                        select(CategoryRoutingRule.id).where(
                            CategoryRoutingRule.city_id == pune.id,
                            CategoryRoutingRule.category_id == category.id,
                        )
                    )
                    if mapped is None:
                        errors.append(f"Category '{category.slug}' has no routing rule")

            preview_count = db.scalar(
                select(func.count()).select_from(City).where(City.status == "preview")
            )
            if preview_count != 5:
                errors.append(f"preview cities expected 5, got {preview_count}")

    except Exception as exc:  # noqa: BLE001 - validation script
        errors.append(f"Database validation skipped/failed: {exc}")

    if errors:
        print("VALIDATION FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("OK: CivicSense Pune data validation passed")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(BACKEND_ROOT))
    raise SystemExit(main())
