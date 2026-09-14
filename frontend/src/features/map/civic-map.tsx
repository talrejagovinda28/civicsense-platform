"use client";

import maplibregl, { type Map as MapLibreMap } from "maplibre-gl";
import { useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";

import { useCity } from "@/features/cities/city-context";
import {
  ComplaintFeedItem,
  getCityWards,
  getWardGeoJson,
} from "@/lib/api";

import { ComplaintMapLayers } from "./complaint-markers";
import { MapAttribution } from "./map-attribution";
import {
  createBaseMapStyle,
  DEFAULT_PUNE_CENTER,
  DEFAULT_PUNE_ZOOM,
} from "./tile-config";

export type SelectedWard = {
  id: string;
  wardNo: number;
  name: string;
};

type CivicMapProps = {
  complaints: ComplaintFeedItem[];
  selectedComplaintId?: string | null;
  onSelectComplaint?: (complaint: ComplaintFeedItem) => void;
  selectedWard?: SelectedWard | null;
  onSelectWard?: (ward: SelectedWard | null) => void;
  className?: string;
};

const COMPLAINT_LAYER_IDS = [
  "complaint-points",
  "complaint-cluster-count",
  "complaint-clusters",
] as const;

function moveComplaintLayersToTop(map: MapLibreMap) {
  for (const layerId of COMPLAINT_LAYER_IDS) {
    if (map.getLayer(layerId)) {
      map.moveLayer(layerId);
    }
  }
}
const WARD_SOURCE_ID = "electoral-wards";
const WARD_FILL_LAYER_ID = "electoral-wards-fill";
const WARD_LINE_LAYER_ID = "electoral-wards-line";

function removeWardLayers(map: MapLibreMap) {
  for (const layerId of [WARD_FILL_LAYER_ID, WARD_LINE_LAYER_ID]) {
    if (map.getLayer(layerId)) {
      map.removeLayer(layerId);
    }
  }
  if (map.getSource(WARD_SOURCE_ID)) {
    map.removeSource(WARD_SOURCE_ID);
  }
}

export function CivicMap({
  complaints,
  selectedComplaintId,
  onSelectComplaint,
  selectedWard,
  onSelectWard,
  className = "h-full w-full",
}: CivicMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const hoveredWardIdRef = useRef<string | number | null>(null);
  const selectedWardFeatureIdRef = useRef<string | number | null>(null);

  const { selectedCity, citySlug, isReportingEnabled } = useCity();
  const [mapReady, setMapReady] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const center = selectedCity
    ? { lat: selectedCity.center_lat, lng: selectedCity.center_lng }
    : DEFAULT_PUNE_CENTER;
  const zoom = selectedCity?.default_zoom ?? DEFAULT_PUNE_ZOOM;
  const isPreview = selectedCity?.status === "preview" || !isReportingEnabled;

  const geoJsonQuery = useQuery({
    queryKey: ["ward-geojson", citySlug],
    queryFn: () => getWardGeoJson(citySlug),
    enabled: Boolean(selectedCity?.supports_ward_map),
    staleTime: 60 * 60 * 1000,
  });

  const wardsQuery = useQuery({
    queryKey: ["city-wards", citySlug],
    queryFn: () => getCityWards(citySlug),
    enabled: Boolean(selectedCity?.supports_ward_map),
    staleTime: 60 * 60 * 1000,
  });

  const wardByFeatureId = useCallback(
    (featureId: string | number): SelectedWard | null => {
      const wards = wardsQuery.data ?? [];
      const featureKey = String(featureId);
      const wardNoMatch = featureKey.match(/(\d+)$/);
      const wardNo = wardNoMatch ? Number(wardNoMatch[1]) : null;
      if (wardNo === null) {
        return null;
      }
      const ward = wards.find((item) => item.ward_no === wardNo);
      if (!ward) {
        return null;
      }
      return { id: ward.id, wardNo: ward.ward_no, name: ward.name };
    },
    [wardsQuery.data],
  );

  useEffect(() => {
    if (!containerRef.current || mapRef.current) {
      return;
    }

    try {
      const map = new maplibregl.Map({
        container: containerRef.current,
        style: createBaseMapStyle(),
        center: [center.lng, center.lat],
        zoom,
        attributionControl: false,
      });

      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
      map.on("load", () => {
        setMapReady(true);
      });
      map.on("error", (event) => {
        if (event.error?.message) {
          setLoadError(event.error.message);
        }
      });

      mapRef.current = map;
    } catch (error) {
      setLoadError(
        error instanceof Error ? error.message : "Failed to initialize map.",
      );
    }

    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
      setMapReady(false);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- map instance is created once per mount
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady) {
      return;
    }

    map.easeTo({
      center: [center.lng, center.lat],
      zoom,
      duration: 500,
    });
  }, [center.lat, center.lng, zoom, mapReady]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || !geoJsonQuery.data) {
      return;
    }

    removeWardLayers(map);

    map.addSource(WARD_SOURCE_ID, {
      type: "geojson",
      data: geoJsonQuery.data as GeoJSON.FeatureCollection,
      generateId: true,
      promoteId: "geometry_feature_id",
    });

    map.addLayer({
      id: WARD_FILL_LAYER_ID,
      type: "fill",
      source: WARD_SOURCE_ID,
      paint: {
        "fill-color": [
          "case",
          ["boolean", ["feature-state", "selected"], false],
          "#1d4ed8",
          ["boolean", ["feature-state", "hover"], false],
          "#3b82f6",
          "#2563eb",
        ],
        "fill-opacity": [
          "case",
          ["boolean", ["feature-state", "selected"], false],
          0.22,
          ["boolean", ["feature-state", "hover"], false],
          0.14,
          0.06,
        ],
      },
    });

    map.addLayer({
      id: WARD_LINE_LAYER_ID,
      type: "line",
      source: WARD_SOURCE_ID,
      paint: {
        "line-color": [
          "case",
          ["boolean", ["feature-state", "selected"], false],
          "#1e40af",
          ["boolean", ["feature-state", "hover"], false],
          "#2563eb",
          "#2563eb",
        ],
        "line-width": [
          "case",
          ["boolean", ["feature-state", "selected"], false],
          2,
          ["boolean", ["feature-state", "hover"], false],
          1.5,
          1,
        ],
        "line-opacity": 0.55,
      },
    });

    const clearHover = () => {
      if (hoveredWardIdRef.current !== null) {
        map.setFeatureState(
          { source: WARD_SOURCE_ID, id: hoveredWardIdRef.current },
          { hover: false },
        );
        hoveredWardIdRef.current = null;
      }
    };

    const handleMouseMove = (event: maplibregl.MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      if (!feature?.id) {
        clearHover();
        return;
      }

      if (hoveredWardIdRef.current !== feature.id) {
        clearHover();
        hoveredWardIdRef.current = feature.id;
        map.setFeatureState({ source: WARD_SOURCE_ID, id: feature.id }, { hover: true });
      }
    };

    const handleMouseLeave = () => {
      clearHover();
      map.getCanvas().style.cursor = "";
    };

    const handleWardClick = (event: maplibregl.MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      if (!feature?.id || !onSelectWard) {
        return;
      }

      const ward = wardByFeatureId(feature.id);
      if (!ward) {
        return;
      }

      if (selectedWardFeatureIdRef.current !== null) {
        map.setFeatureState(
          { source: WARD_SOURCE_ID, id: selectedWardFeatureIdRef.current },
          { selected: false },
        );
      }

      const isSameWard = selectedWard?.id === ward.id;
      if (isSameWard) {
        selectedWardFeatureIdRef.current = null;
        onSelectWard(null);
        return;
      }

      selectedWardFeatureIdRef.current = feature.id;
      map.setFeatureState({ source: WARD_SOURCE_ID, id: feature.id }, { selected: true });
      onSelectWard(ward);
    };

    map.on("mousemove", WARD_FILL_LAYER_ID, handleMouseMove);
    map.on("mouseleave", WARD_FILL_LAYER_ID, handleMouseLeave);
    map.on("mouseenter", WARD_FILL_LAYER_ID, () => {
      map.getCanvas().style.cursor = "pointer";
    });
    map.on("click", WARD_FILL_LAYER_ID, handleWardClick);
    moveComplaintLayersToTop(map);

    return () => {
      map.off("mousemove", WARD_FILL_LAYER_ID, handleMouseMove);
      map.off("mouseleave", WARD_FILL_LAYER_ID, handleMouseLeave);
      map.off("click", WARD_FILL_LAYER_ID, handleWardClick);
      removeWardLayers(map);
      hoveredWardIdRef.current = null;
      selectedWardFeatureIdRef.current = null;
    };
  }, [geoJsonQuery.data, mapReady, onSelectWard, selectedWard?.id, wardByFeatureId]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || !selectedWard) {
      return;
    }

    const feature = (geoJsonQuery.data as GeoJSON.FeatureCollection | undefined)?.features.find(
      (item) => Number(item.properties?.ward_no) === selectedWard.wardNo,
    );
    if (!feature?.properties?.geometry_feature_id) {
      return;
    }

    const featureId = feature.properties.geometry_feature_id as string;
    if (selectedWardFeatureIdRef.current !== null) {
      map.setFeatureState(
        { source: WARD_SOURCE_ID, id: selectedWardFeatureIdRef.current },
        { selected: false },
      );
    }
    selectedWardFeatureIdRef.current = featureId;
    map.setFeatureState({ source: WARD_SOURCE_ID, id: featureId }, { selected: true });
  }, [geoJsonQuery.data, mapReady, selectedWard]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapReady || !selectedComplaintId) {
      return;
    }

    const complaint = complaints.find((item) => item.id === selectedComplaintId);
    if (
      !complaint ||
      complaint.public_latitude === null ||
      complaint.public_longitude === null
    ) {
      return;
    }

    map.easeTo({
      center: [complaint.public_longitude, complaint.public_latitude],
      zoom: Math.max(map.getZoom(), 14),
      duration: 600,
    });
  }, [complaints, mapReady, selectedComplaintId]);

  if (loadError) {
    return (
      <div className={`flex items-center justify-center bg-red-50 ${className}`}>
        <p className="px-6 text-sm text-red-700">Failed to load map: {loadError}</p>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      <div ref={containerRef} className="h-full w-full" aria-label="Civic map" />
      <MapAttribution />

      {!mapReady && (
        <div className="absolute inset-0 flex items-center justify-center bg-[var(--surface-muted)]">
          <p className="text-sm text-[var(--muted)]">Loading map…</p>
        </div>
      )}

      <ComplaintMapLayers
        map={mapReady ? mapRef.current : null}
        complaints={complaints}
        selectedId={selectedComplaintId}
        onSelect={onSelectComplaint}
      />

      {selectedWard && (
        <div className="absolute left-2 top-2 z-10 max-w-xs rounded-lg border border-civic bg-white/95 px-3 py-2 text-sm shadow-civic-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-[var(--primary)]">
            Selected ward
          </p>
          <p className="font-medium text-civic-navy">
            Ward {selectedWard.wardNo} — {selectedWard.name}
          </p>
        </div>
      )}

      {isPreview && (
        <div className="pointer-events-none absolute inset-0 flex items-end justify-center bg-slate-900/20 p-4 sm:items-center">
          <div className="pointer-events-auto max-w-md rounded-xl border border-civic bg-white/95 p-5 shadow-civic-lg backdrop-blur-sm">
            <p className="text-xs font-semibold uppercase tracking-wide text-[var(--primary)]">
              Preview mode
            </p>
            <h3 className="mt-1 text-lg font-semibold text-civic-navy">
              {selectedCity?.name ?? "This city"} is coming soon
            </h3>
            <p className="mt-2 text-sm text-[var(--muted)]">
              Explore the map and browse public issues. Reporting will open when this city
              goes live.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
