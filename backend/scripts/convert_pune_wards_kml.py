#!/usr/bin/env python3
"""One-time converter: OpenCity Pune electoral wards KML -> GeoJSON (WGS84)."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}


def parse_coordinates(text: str) -> list[list[float]]:
    coords: list[list[float]] = []
    for token in text.strip().split():
        parts = token.split(",")
        if len(parts) < 2:
            continue
        lng, lat = float(parts[0]), float(parts[1])
        coords.append([lng, lat])
    return coords


def geometry_from_placemark(placemark: ET.Element) -> dict | None:
    rings: list[list[list[float]]] = []
    for polygon in placemark.findall(".//kml:Polygon", KML_NS):
        ring = polygon.find(".//kml:LinearRing/kml:coordinates", KML_NS)
        if ring is None:
            ring = polygon.find(".//kml:coordinates", KML_NS)
        if ring is None or not ring.text:
            continue
        ring_coords = parse_coordinates(ring.text)
        if len(ring_coords) >= 4:
            rings.append(ring_coords)
    if not rings:
        return None
    if len(rings) == 1:
        return {"type": "Polygon", "coordinates": rings}
    return {"type": "MultiPolygon", "coordinates": [[ring] for ring in rings]}


def ward_no_from_placemark(placemark: ET.Element, fallback_index: int) -> int:
    qwr = placemark.find(".//kml:SimpleData[@name='qwr']", KML_NS)
    if qwr is not None and qwr.text:
        return int(float(qwr.text))
    placemark_id = placemark.get("id") or ""
    match = re.search(r"\.(\d+)$", placemark_id)
    if match:
        return int(match.group(1))
    return fallback_index


def convert(kml_path: Path, geojson_path: Path) -> int:
    root = ET.parse(kml_path).getroot()
    features: list[dict] = []

    for index, placemark in enumerate(root.findall(".//kml:Placemark", KML_NS), start=1):
        geometry = geometry_from_placemark(placemark)
        if geometry is None:
            continue
        ward_no = ward_no_from_placemark(placemark, index)

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "ward_no": ward_no,
                    "name": f"Ward {ward_no}",
                    "geometry_feature_id": f"pune-ward-{ward_no}",
                },
                "geometry": geometry,
            }
        )

    collection = {"type": "FeatureCollection", "features": features}
    geojson_path.parent.mkdir(parents=True, exist_ok=True)
    geojson_path.write_text(json.dumps(collection, indent=2), encoding="utf-8")
    return len(features)


if __name__ == "__main__":
    base = Path(__file__).resolve().parents[1] / "app" / "data" / "cities" / "pune"
    kml = base / "source" / "pune_wards_2025.kml"
    out = base / "electoral_wards_2025.geojson"
    count = convert(kml, out)
    print(f"Wrote {count} features to {out}")
