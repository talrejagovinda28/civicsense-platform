#!/usr/bin/env python3
"""Validate Pune electoral ward GeoJSON package."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from shapely.geometry import shape
    from shapely.validation import explain_validity
except ImportError:
    print("ERROR: shapely is required. Install with: pip install shapely")
    sys.exit(1)

PUNE_LAT_MIN, PUNE_LAT_MAX = 18.0, 19.0
PUNE_LNG_MIN, PUNE_LNG_MAX = 73.0, 74.5


def main() -> int:
    geojson_path = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "data"
        / "cities"
        / "pune"
        / "electoral_wards_2025.geojson"
    )
    data = json.loads(geojson_path.read_text(encoding="utf-8"))
    features = data.get("features", [])
    errors: list[str] = []

    if data.get("type") != "FeatureCollection":
        errors.append("Root must be a FeatureCollection")
    if len(features) != 41:
        errors.append(f"Expected 41 features, found {len(features)}")

    ward_numbers: set[int] = set()
    for index, feature in enumerate(features, start=1):
        props = feature.get("properties") or {}
        ward_no = props.get("ward_no")
        if ward_no is None:
            errors.append(f"Feature {index} missing ward_no")
            continue
        if ward_no in ward_numbers:
            errors.append(f"Duplicate ward_no: {ward_no}")
        ward_numbers.add(int(ward_no))

        geom = feature.get("geometry")
        if geom.get("type") not in {"Polygon", "MultiPolygon"}:
            errors.append(f"Ward {ward_no}: invalid geometry type")
            continue
        polygon = shape(geom)
        if polygon.is_empty:
            errors.append(f"Ward {ward_no}: empty geometry")
        elif not polygon.is_valid:
            errors.append(f"Ward {ward_no}: {explain_validity(polygon)}")
        bounds = polygon.bounds
        if not (PUNE_LNG_MIN <= bounds[0] <= PUNE_LNG_MAX and PUNE_LAT_MIN <= bounds[1] <= PUNE_LAT_MAX):
            errors.append(f"Ward {ward_no}: coordinates outside plausible Pune bounds")

    if errors:
        print("VALIDATION FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"OK: {len(features)} Pune electoral ward features validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
