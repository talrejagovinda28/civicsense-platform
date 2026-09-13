"use client";

import { GoogleMap, useJsApiLoader } from "@react-google-maps/api";
import { useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";

import { useCity } from "@/features/cities/city-context";
import { ComplaintFeedItem, getWardGeoJson } from "@/lib/api";

import { ComplaintMarkers } from "./complaint-markers";

type CivicMapProps = {
  complaints: ComplaintFeedItem[];
  selectedComplaintId?: string | null;
  onSelectComplaint?: (complaint: ComplaintFeedItem) => void;
  className?: string;
};

const MAP_LIBRARIES: ("places")[] = ["places"];

export function CivicMap({
  complaints,
  selectedComplaintId,
  onSelectComplaint,
  className = "h-full w-full",
}: CivicMapProps) {
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ?? "";
  const { selectedCity, citySlug, isReportingEnabled } = useCity();
  const [map, setMap] = useState<google.maps.Map | null>(null);
  const dataLayerRef = useRef<google.maps.Data | null>(null);

  const center = selectedCity
    ? { lat: selectedCity.center_lat, lng: selectedCity.center_lng }
    : { lat: 18.5204, lng: 73.8567 };

  const zoom = selectedCity?.default_zoom ?? 12;
  const isPreview = selectedCity?.status === "preview" || !isReportingEnabled;

  const geoJsonQuery = useQuery({
    queryKey: ["ward-geojson", citySlug],
    queryFn: () => getWardGeoJson(citySlug),
    enabled: Boolean(selectedCity?.supports_ward_map),
    staleTime: 60 * 60 * 1000,
  });

  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: apiKey,
    libraries: MAP_LIBRARIES,
  });

  const onLoad = useCallback((loadedMap: google.maps.Map) => {
    setMap(loadedMap);
  }, []);

  const onUnmount = useCallback(() => {
    dataLayerRef.current?.setMap(null);
    dataLayerRef.current = null;
    setMap(null);
  }, []);

  useEffect(() => {
    if (!map || !geoJsonQuery.data) {
      return;
    }

    dataLayerRef.current?.setMap(null);

    const dataLayer = new google.maps.Data({ map });
    dataLayer.addGeoJson(geoJsonQuery.data);
    dataLayer.setStyle({
      fillColor: "#2563eb",
      fillOpacity: 0.06,
      strokeColor: "#2563eb",
      strokeWeight: 1,
      strokeOpacity: 0.45,
    });
    dataLayerRef.current = dataLayer;

    return () => {
      dataLayer.setMap(null);
    };
  }, [map, geoJsonQuery.data]);

  if (!apiKey) {
    return (
      <div className={`flex items-center justify-center bg-[var(--surface-muted)] ${className}`}>
        <div className="max-w-sm px-6 text-center">
          <p className="font-medium text-civic-navy">Map unavailable</p>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Set <code className="text-xs">NEXT_PUBLIC_GOOGLE_MAPS_API_KEY</code> to enable
            the civic map. Complaints are still listed in the panel.
          </p>
        </div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className={`flex items-center justify-center bg-red-50 ${className}`}>
        <p className="px-6 text-sm text-red-700">
          Failed to load Google Maps. Check your API key configuration.
        </p>
      </div>
    );
  }

  if (!isLoaded) {
    return (
      <div className={`flex items-center justify-center bg-[var(--surface-muted)] ${className}`}>
        <p className="text-sm text-[var(--muted)]">Loading map…</p>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      <GoogleMap
        mapContainerClassName="h-full w-full"
        center={center}
        zoom={zoom}
        onLoad={onLoad}
        onUnmount={onUnmount}
        options={{
          streetViewControl: false,
          mapTypeControl: false,
          fullscreenControl: true,
        }}
      >
        <ComplaintMarkers
          map={map}
          complaints={complaints}
          selectedId={selectedComplaintId}
          onSelect={onSelectComplaint}
        />
      </GoogleMap>

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
