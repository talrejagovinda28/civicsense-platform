"use client";

import type { GeoJSONSource, Map as MapLibreMap, MapGeoJSONFeature, MapLayerMouseEvent } from "maplibre-gl";
import { useEffect } from "react";

import { ComplaintFeedItem, STATUS_COLORS } from "@/lib/api";

import { MAP_DEFAULT_FONTS } from "./tile-config";

const SOURCE_ID = "complaints";
const CLUSTER_LAYER_ID = "complaint-clusters";
const CLUSTER_COUNT_LAYER_ID = "complaint-cluster-count";
const POINT_LAYER_ID = "complaint-points";

type ComplaintMapLayersProps = {
  map: MapLibreMap | null;
  complaints: ComplaintFeedItem[];
  selectedId?: string | null;
  onSelect?: (complaint: ComplaintFeedItem) => void;
};

function complaintsToGeoJson(
  complaints: ComplaintFeedItem[],
  selectedId?: string | null,
): GeoJSON.FeatureCollection {
  return {
    type: "FeatureCollection",
    features: complaints
      .filter(
        (complaint) =>
          complaint.public_latitude !== null && complaint.public_longitude !== null,
      )
      .map((complaint) => ({
        type: "Feature" as const,
        geometry: {
          type: "Point" as const,
          coordinates: [complaint.public_longitude!, complaint.public_latitude!],
        },
        properties: {
          id: complaint.id,
          status: complaint.status,
          title: complaint.title,
          color: STATUS_COLORS[complaint.status] ?? "#64748b",
          selected: selectedId === complaint.id,
        },
      })),
  };
}

function removeComplaintLayers(map: MapLibreMap) {
  for (const layerId of [POINT_LAYER_ID, CLUSTER_COUNT_LAYER_ID, CLUSTER_LAYER_ID]) {
    if (map.getLayer(layerId)) {
      map.removeLayer(layerId);
    }
  }
  if (map.getSource(SOURCE_ID)) {
    map.removeSource(SOURCE_ID);
  }
}

export function ComplaintMapLayers({
  map,
  complaints,
  selectedId,
  onSelect,
}: ComplaintMapLayersProps) {
  useEffect(() => {
    if (!map) {
      return;
    }

    const data = complaintsToGeoJson(complaints, selectedId);
    const existing = map.getSource(SOURCE_ID) as GeoJSONSource | undefined;

    if (existing) {
      existing.setData(data);
      return;
    }

    map.addSource(SOURCE_ID, {
      type: "geojson",
      data,
      cluster: true,
      clusterMaxZoom: 14,
      clusterRadius: 50,
    });

    map.addLayer({
      id: CLUSTER_LAYER_ID,
      type: "circle",
      source: SOURCE_ID,
      filter: ["has", "point_count"],
      paint: {
        "circle-color": "#2563eb",
        "circle-radius": ["step", ["get", "point_count"], 16, 10, 20, 25, 24],
        "circle-opacity": 0.85,
        "circle-stroke-width": 2,
        "circle-stroke-color": "#ffffff",
      },
    });

    map.addLayer({
      id: CLUSTER_COUNT_LAYER_ID,
      type: "symbol",
      source: SOURCE_ID,
      filter: ["has", "point_count"],
      layout: {
        "text-field": ["get", "point_count_abbreviated"],
        "text-font": [...MAP_DEFAULT_FONTS],
        "text-size": 12,
      },
      paint: {
        "text-color": "#ffffff",
      },
    });

    map.addLayer({
      id: POINT_LAYER_ID,
      type: "circle",
      source: SOURCE_ID,
      filter: ["!", ["has", "point_count"]],
      paint: {
        "circle-color": [
          "case",
          ["get", "selected"],
          "#1e293b",
          ["get", "color"],
        ],
        "circle-radius": ["case", ["get", "selected"], 10, 8],
        "circle-stroke-width": 2,
        "circle-stroke-color": "#ffffff",
      },
    });

    return () => {
      removeComplaintLayers(map);
    };
  }, [map, complaints, selectedId]);

  useEffect(() => {
    if (!map || !onSelect) {
      return;
    }

    const handleClick = (event: MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      if (!feature?.properties?.id) {
        return;
      }

      const complaint = complaints.find((item) => item.id === feature.properties?.id);
      if (complaint) {
        onSelect(complaint);
      }
    };

    const handleClusterClick = (event: MapLayerMouseEvent) => {
      const features = map.queryRenderedFeatures(event.point, {
        layers: [CLUSTER_LAYER_ID],
      }) as MapGeoJSONFeature[];
      const clusterId = features[0]?.properties?.cluster_id;
      const source = map.getSource(SOURCE_ID) as GeoJSONSource | undefined;
      if (clusterId === undefined || !source || !features[0]) {
        return;
      }

      source.getClusterExpansionZoom(clusterId).then((nextZoom) => {
        const coordinates = (features[0].geometry as GeoJSON.Point).coordinates as [
          number,
          number,
        ];
        map.easeTo({
          center: coordinates,
          zoom: nextZoom ?? map.getZoom() + 1,
        });
      });
    };

    map.on("click", POINT_LAYER_ID, handleClick);
    map.on("click", CLUSTER_LAYER_ID, handleClusterClick);
    map.on("mouseenter", POINT_LAYER_ID, () => {
      map.getCanvas().style.cursor = "pointer";
    });
    map.on("mouseleave", POINT_LAYER_ID, () => {
      map.getCanvas().style.cursor = "";
    });
    map.on("mouseenter", CLUSTER_LAYER_ID, () => {
      map.getCanvas().style.cursor = "pointer";
    });
    map.on("mouseleave", CLUSTER_LAYER_ID, () => {
      map.getCanvas().style.cursor = "";
    });

    return () => {
      map.off("click", POINT_LAYER_ID, handleClick);
      map.off("click", CLUSTER_LAYER_ID, handleClusterClick);
    };
  }, [map, complaints, onSelect]);

  return null;
}
