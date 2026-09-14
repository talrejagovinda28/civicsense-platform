"use client";

import type { Map as MapLibreMap, Marker } from "maplibre-gl";
import { useCallback, useEffect, useRef, useState } from "react";

import { MapAttribution } from "@/features/map/map-attribution";
import { getMapLibre } from "@/features/map/maplibre-setup";
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
  const onLocationChangeRef = useRef(onLocationChange);

  const [addressValue, setAddressValue] = useState(address ?? "");
  const [wardValue, setWardValue] = useState(ward ?? "");
  const [mapReady, setMapReady] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    onLocationChangeRef.current = onLocationChange;
  }, [onLocationChange]);

  useEffect(() => {
    if (address !== null && address !== addressValue) {
      setAddressValue(address);
    }
  }, [address, addressValue]);

  useEffect(() => {
    if (ward !== null && ward !== wardValue) {
      setWardValue(ward);
    }
  }, [ward, wardValue]);

  const publishLocation = useCallback(
    (next: {
      latitude: number | null;
      longitude: number | null;
      address: string;
      ward: string | null;
    }) => {
      onLocationChangeRef.current({
        latitude: next.latitude,
        longitude: next.longitude,
        address: next.address,
        googlePlaceId: null,
        ward: next.ward,
      });
    },
    [],
  );

  const setMarkerAt = useCallback(
    (lng: number, lat: number, nextAddress = addressValue, nextWard = wardValue) => {
      const map = mapRef.current;
      if (!map) {
        return;
      }

      const maplibregl = getMapLibre();

      if (!markerRef.current) {
        markerRef.current = new maplibregl.Marker({ draggable: true, color: "#2563eb" })
          .setLngLat([lng, lat])
          .addTo(map);

        markerRef.current.on("dragend", () => {
          const position = markerRef.current?.getLngLat();
          if (!position) {
            return;
          }
          publishLocation({
            latitude: position.lat,
            longitude: position.lng,
            address: addressValue,
            ward: wardValue.trim() || null,
          });
        });
      } else {
        markerRef.current.setLngLat([lng, lat]);
      }

      publishLocation({
        latitude: lat,
        longitude: lng,
        address: nextAddress,
        ward: nextWard.trim() || null,
      });
    },
    [addressValue, publishLocation, wardValue],
  );

  useEffect(() => {
    if (!containerRef.current || mapRef.current) {
      return;
    }

    try {
      const maplibregl = getMapLibre();
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
          onChange={(event) => {
            const value = event.target.value;
            setWardValue(value);
            publishLocation({
              latitude,
              longitude,
              address: addressValue,
              ward: value.trim() || null,
            });
          }}
          className="w-full rounded-lg border border-neutral-300 px-3 py-2"
        />
      </label>

      <label className="block space-y-1 text-sm">
        <span className="font-medium">Address</span>
        <textarea
          placeholder="Street, landmark, or nearby reference"
          value={addressValue}
          onChange={(event) => {
            const value = event.target.value;
            setAddressValue(value);
            publishLocation({
              latitude,
              longitude,
              address: value,
              ward: wardValue.trim() || null,
            });
          }}
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
