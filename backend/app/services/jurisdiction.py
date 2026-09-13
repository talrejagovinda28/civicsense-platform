from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from shapely.geometry import Point, shape
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.city import City
from app.models.electoral_ward import ElectoralWard

PUNE_GEOJSON = (
    Path(__file__).resolve().parents[1] / "data" / "cities" / "pune" / "electoral_wards_2025.geojson"
)


@dataclass(frozen=True)
class ParsedWardGeometry:
    ward_no: int
    geometry_feature_id: str
    polygon: object


@lru_cache(maxsize=4)
def _load_city_geometries(city_slug: str) -> tuple[ParsedWardGeometry, ...]:
    if city_slug != "pune":
        return ()
    data = json.loads(PUNE_GEOJSON.read_text(encoding="utf-8"))
    parsed: list[ParsedWardGeometry] = []
    for feature in data.get("features", []):
        props = feature.get("properties") or {}
        ward_no = int(props["ward_no"])
        feature_id = str(props.get("geometry_feature_id") or f"pune-ward-{ward_no}")
        parsed.append(
            ParsedWardGeometry(
                ward_no=ward_no,
                geometry_feature_id=feature_id,
                polygon=shape(feature["geometry"]),
            )
        )
    return tuple(parsed)


def get_city_geojson(city_slug: str) -> dict:
    if city_slug != "pune":
        return {"type": "FeatureCollection", "features": []}
    return json.loads(PUNE_GEOJSON.read_text(encoding="utf-8"))


def resolve_electoral_ward(
    db: Session,
    *,
    city_slug: str,
    latitude: float,
    longitude: float,
) -> tuple[ElectoralWard | None, str | None]:
    city = db.scalar(select(City).where(City.slug == city_slug))
    if city is None:
        return None, "City not found"

    point = Point(longitude, latitude)
    matched_ward_no: int | None = None
    for ward_geometry in _load_city_geometries(city_slug):
        if ward_geometry.polygon.contains(point) or ward_geometry.polygon.touches(point):
            matched_ward_no = ward_geometry.ward_no
            break

    if matched_ward_no is None:
        return None, (
            "Location is outside the currently supported municipal ward boundaries."
        )

    ward = db.scalar(
        select(ElectoralWard).where(
            ElectoralWard.city_id == city.id,
            ElectoralWard.ward_no == matched_ward_no,
        )
    )
    return ward, None
