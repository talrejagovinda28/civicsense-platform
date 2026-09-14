"use client";

import maplibregl, { type Map as MapLibreMap, type Marker } from "maplibre-gl";
import { useCallback, useEffect, useRef, useState } from "react";

import { MapAttribution } from "@/features/map/map-attribution";
import {
  createBaseMapStyle,
  DEFAULT_PUNE_CENTER,
  DEFAULT_PUNE_ZOOM,
} from "@/features/map/tile-config";

export type MapLocation = {
  latitude: number | null;
  longitude: number | null;
  address: string;
  googlePlaceId: string | null;
  ward?: string | null;
};

type MapPickerProps = {
  latitude: number | null;
  longitude: number | null;
  address: string | null;
  ward: string | null;
  onLocationChange: (location: MapLocation) => void;
};

/**
 * Optional reverse geocoder hook point for a future provider.
 * Returns null today so address stays manual unless a geocoder is plugged in.
 */
export type ReverseGeocoder = (
  latitude: number,
  longitude: number,
) => Promise<{ address: string; placeId?: string | null } | null>;

export function MapPicker({
  latitude,
  longitude,
  address,
  ward,
  onLocationChange,
}: MapPickerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const markerRef = useRef<Marker | null>(null);

  const [addressValue, setAddressValue] = useState(address ?? "");
  const [wardValue, setWardValue] = useState(ward ?? "");
  const [mapReady, setMapReady] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    if (address !== null) {
      setAddressValue(address);
    }
  }, [address]);

  useEffect(() => {
    if (ward !== null) {
      setWardValue(ward);
    }
  }, [ward]);

  const emitLocation = useCallback(
    (next: {
      latitude: number | null;
      longitude: number | null;
      address?: string;
      ward?: string | null;
    }) => {
      onLocationChange({
        latitude: next.latitude,
        longitude: next.longitude,
        address: next.address ?? addressValue,
        googlePlaceId: null,
        ward: next.ward ?? (wardValue.trim() || null),
      });
    },
    [addressValue, onLocationChange, wardValue],
  );

  const setMarkerAt = useCallback(
    (lng: number, lat: number) => {
      const map = mapRef.current;
      if (!map) {
        return;
      }

      if (!markerRef.current) {
        markerRef.current = new maplibregl.Marker({ draggable: true, color: "#2563eb" })
          .setLngLat([lng, lat])
          .addTo(map);

        markerRef.current.on("dragend", () => {
          const position = markerRef.current?.getLngLat();
          if (!position) {
            return;
          }
          emitLocation({
            latitude: position.lat,
            longitude: position.lng,
          });
        });
      } else {
        markerRef.current.setLngLat([lng, lat]);
      }

      emitLocation({ latitude: lat, longitude: lng });
    },
    [emitLocation],
  );

  useEffect(() => {
    if (!containerRef.current || mapRef.current) {
      return;
    }

    try {
      const initialCenter =
        latitude !== null && longitude !== null
          ? ([longitude, latitude] as [number, number])
          : ([DEFAULT_PUNE_CENTER.lng, DEFAULT_PUNE_CENTER.lat] as [number, number]);

      const map = new maplibregl.Map({
        container: containerRef.current,
        style: createBaseMapStyle(),
        center: initialCenter,
        zoom: latitude !== null && longitude !== null ? 16 : DEFAULT_PUNE_ZOOM,
        attributionControl: false,
      });

      map.on("load", () => {
        setMapReady(true);
        if (latitude !== null && longitude !== null) {
          setMarkerAt(longitude, latitude);
        }
      });

      map.on("click", (event) => {
        setMarkerAt(event.lngLat.lng, event.lngLat.lat);
      });

      mapRef.current = map;
    } catch (error) {
      setLoadError(
        error instanceof Error ? error.message : "Failed to initialize map.",
      );
    }

    return () => {
      markerRef.current?.remove();
      markerRef.current = null;
      mapRef.current?.remove();
      mapRef.current = null;
      setMapReady(false);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- single map mount
  }, []);

  useEffect(() => {
    if (!mapReady || latitude === null || longitude === null) {
      return;
    }
    setMarkerAt(longitude, latitude);
  }, [latitude, longitude, mapReady, setMarkerAt]);

  useEffect(() => {
    emitLocation({
      latitude,
      longitude,
      address: addressValue,
      ward: wardValue.trim() || null,
    });
  }, [addressValue, wardValue, latitude, longitude, emitLocation]);

  if (loadError) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        Failed to load map: {loadError}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-neutral-600">
        Tap the map to drop a pin on the issue location, then enter the address below.
      </p>

      <div className="relative h-80 overflow-hidden rounded-lg border border-neutral-200">
        <div ref={containerRef} className="h-full w-full" aria-label="Location picker map" />
        <MapAttribution />
        {!mapReady && (
          <div className="absolute inset-0 flex items-center justify-center bg-neutral-50 text-sm text-neutral-500">
            Loading map…
          </div>
        )}
      </div>

      <label className="block space-y-1 text-sm">
        <span className="font-medium">Area / ward</span>
        <input
          type="text"
          placeholder="e.g. Kothrud, Hadapsar"
          value={wardValue}
          onChange={(event) => setWardValue(event.target.value)}
          className="w-full rounded-lg border border-neutral-300 px-3 py-2"
        />
      </label>

      <label className="block space-y-1 text-sm">
        <span className="font-medium">Address</span>
        <textarea
          placeholder="Street, landmark, or nearby reference"
          value={addressValue}
          onChange={(event) => setAddressValue(event.target.value)}
          rows={3}
          className="w-full rounded-lg border border-neutral-300 px-3 py-2"
        />
      </label>

      {latitude !== null && longitude !== null && (
        <div className="rounded-lg bg-neutral-50 px-4 py-3 text-sm">
          <p className="font-medium">{addressValue || "Address not entered yet"}</p>
          <p className="mt-1 text-xs text-neutral-500">
            {latitude.toFixed(6)}, {longitude.toFixed(6)}
          </p>
        </div>
      )}
    </div>
  );
}
