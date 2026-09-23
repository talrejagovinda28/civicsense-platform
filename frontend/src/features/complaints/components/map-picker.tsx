"use client";

import type { Map as MapLibreMap, Marker } from "maplibre-gl";
import { useCallback, useEffect, useRef, useState } from "react";

import { MapAttribution } from "@/features/map/map-attribution";
import { getMapLibre, isFatalMapError, resizeMap } from "@/features/map/maplibre-setup";
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

function isFiniteCoord(value: number | null | undefined): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

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
  const addressRef = useRef(address ?? "");
  const wardRef = useRef(ward ?? "");
  const aliveRef = useRef(true);

  const [addressValue, setAddressValue] = useState(address ?? "");
  const [wardValue, setWardValue] = useState(ward ?? "");
  const [mapReady, setMapReady] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    onLocationChangeRef.current = onLocationChange;
  }, [onLocationChange]);

  useEffect(() => {
    addressRef.current = addressValue;
  }, [addressValue]);

  useEffect(() => {
    wardRef.current = wardValue;
  }, [wardValue]);

  useEffect(() => {
    if (address !== null && address !== addressValue) {
      setAddressValue(address);
    }
    // Sync from parent only when parent value changes — omit addressValue to avoid loops.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional
  }, [address]);

  useEffect(() => {
    if (ward !== null && ward !== wardValue) {
      setWardValue(ward);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional
  }, [ward]);

  const publishLocation = useCallback(
    (next: {
      latitude: number | null;
      longitude: number | null;
      address: string;
      ward: string | null;
    }) => {
      if (!aliveRef.current) {
        return;
      }
      try {
        onLocationChangeRef.current({
          latitude: isFiniteCoord(next.latitude) ? next.latitude : null,
          longitude: isFiniteCoord(next.longitude) ? next.longitude : null,
          address: next.address,
          googlePlaceId: null,
          ward: next.ward,
        });
      } catch (error) {
        console.error("Failed to publish map location:", error);
      }
    },
    [],
  );

  const setMarkerAt = useCallback(
    (lng: number, lat: number) => {
      const map = mapRef.current;
      if (!aliveRef.current || !map || !isFiniteCoord(lng) || !isFiniteCoord(lat)) {
        return;
      }

      try {
        const maplibregl = getMapLibre();
        const nextAddress = addressRef.current;
        const nextWard = wardRef.current.trim() || null;

        if (!markerRef.current) {
          markerRef.current = new maplibregl.Marker({
            draggable: true,
            color: "#2563eb",
          })
            .setLngLat([lng, lat])
            .addTo(map);

          markerRef.current.on("dragend", () => {
            if (!aliveRef.current) {
              return;
            }
            try {
              const position = markerRef.current?.getLngLat();
              if (!position) {
                return;
              }
              publishLocation({
                latitude: position.lat,
                longitude: position.lng,
                address: addressRef.current,
                ward: wardRef.current.trim() || null,
              });
            } catch (error) {
              console.error("Map marker drag failed:", error);
            }
          });
        } else {
          markerRef.current.setLngLat([lng, lat]);
        }

        publishLocation({
          latitude: lat,
          longitude: lng,
          address: nextAddress,
          ward: nextWard,
        });
      } catch (error) {
        console.error("Failed to place map marker:", error);
        setLoadError(
          error instanceof Error ? error.message : "Failed to place map marker.",
        );
      }
    },
    [publishLocation],
  );

  const setMarkerAtRef = useRef(setMarkerAt);
  useEffect(() => {
    setMarkerAtRef.current = setMarkerAt;
  }, [setMarkerAt]);

  useEffect(() => {
    aliveRef.current = true;
    if (!containerRef.current || mapRef.current) {
      return;
    }

    try {
      const maplibregl = getMapLibre();
      const initialCenter =
        isFiniteCoord(latitude) && isFiniteCoord(longitude)
          ? ([longitude, latitude] as [number, number])
          : ([DEFAULT_PUNE_CENTER.lng, DEFAULT_PUNE_CENTER.lat] as [number, number]);

      const map = new maplibregl.Map({
        container: containerRef.current,
        style: createBaseMapStyle(),
        center: initialCenter,
        zoom:
          isFiniteCoord(latitude) && isFiniteCoord(longitude)
            ? 16
            : DEFAULT_PUNE_ZOOM,
        attributionControl: false,
      });

      map.on("error", (event) => {
        const message =
          event.error instanceof Error
            ? event.error.message
            : String(event.error ?? "Map error");
        if (isFatalMapError(message)) {
          console.error("MapLibre fatal error:", message);
          setLoadError(message);
        }
      });

      map.on("load", () => {
        if (!aliveRef.current) {
          return;
        }
        resizeMap(map);
        setMapReady(true);
        if (isFiniteCoord(latitude) && isFiniteCoord(longitude)) {
          setMarkerAtRef.current(longitude, latitude);
        }
      });

      map.on("click", (event) => {
        if (!aliveRef.current) {
          return;
        }
        setMarkerAtRef.current(event.lngLat.lng, event.lngLat.lat);
      });

      mapRef.current = map;
    } catch (error) {
      setLoadError(
        error instanceof Error ? error.message : "Failed to initialize map.",
      );
    }

    return () => {
      aliveRef.current = false;
      try {
        markerRef.current?.remove();
      } catch {
        // ignore cleanup races
      }
      markerRef.current = null;
      try {
        mapRef.current?.remove();
      } catch {
        // ignore cleanup races
      }
      mapRef.current = null;
      setMapReady(false);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- single map mount
  }, []);

  if (loadError) {
    return (
      <div className="space-y-4">
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          Map unavailable: {loadError}. You can still enter address and ward below.
        </div>
        <ManualLocationFields
          addressValue={addressValue}
          wardValue={wardValue}
          latitude={latitude}
          longitude={longitude}
          onAddressChange={(value) => {
            setAddressValue(value);
            publishLocation({
              latitude,
              longitude,
              address: value,
              ward: wardValue.trim() || null,
            });
          }}
          onWardChange={(value) => {
            setWardValue(value);
            publishLocation({
              latitude,
              longitude,
              address: addressValue,
              ward: value.trim() || null,
            });
          }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-neutral-600">
        Tap the map to drop a pin on the issue location, then enter the address below.
      </p>

      <div className="relative h-80 overflow-hidden rounded-lg border border-neutral-200">
        <div
          ref={containerRef}
          className="h-full w-full"
          aria-label="Location picker map"
        />
        <MapAttribution />
        {!mapReady && (
          <div className="absolute inset-0 flex items-center justify-center bg-neutral-50 text-sm text-neutral-500">
            Loading map…
          </div>
        )}
      </div>

      <ManualLocationFields
        addressValue={addressValue}
        wardValue={wardValue}
        latitude={latitude}
        longitude={longitude}
        onAddressChange={(value) => {
          setAddressValue(value);
          publishLocation({
            latitude,
            longitude,
            address: value,
            ward: wardValue.trim() || null,
          });
        }}
        onWardChange={(value) => {
          setWardValue(value);
          publishLocation({
            latitude,
            longitude,
            address: addressValue,
            ward: value.trim() || null,
          });
        }}
      />
    </div>
  );
}

function ManualLocationFields({
  addressValue,
  wardValue,
  latitude,
  longitude,
  onAddressChange,
  onWardChange,
}: {
  addressValue: string;
  wardValue: string;
  latitude: number | null;
  longitude: number | null;
  onAddressChange: (value: string) => void;
  onWardChange: (value: string) => void;
}) {
  return (
    <>
      <label className="block space-y-1 text-sm">
        <span className="font-medium">Area / ward</span>
        <input
          type="text"
          placeholder="e.g. Kothrud, Hadapsar"
          value={wardValue}
          onChange={(event) => onWardChange(event.target.value)}
          className="w-full rounded-lg border border-neutral-300 px-3 py-2"
        />
      </label>

      <label className="block space-y-1 text-sm">
        <span className="font-medium">Address</span>
        <textarea
          placeholder="Street, landmark, or nearby reference"
          value={addressValue}
          onChange={(event) => onAddressChange(event.target.value)}
          rows={3}
          className="w-full rounded-lg border border-neutral-300 px-3 py-2"
        />
      </label>

      {isFiniteCoord(latitude) && isFiniteCoord(longitude) && (
        <div className="rounded-lg bg-neutral-50 px-4 py-3 text-sm">
          <p className="font-medium">{addressValue || "Address not entered yet"}</p>
          <p className="mt-1 text-xs text-neutral-500">
            {latitude.toFixed(6)}, {longitude.toFixed(6)}
          </p>
        </div>
      )}
    </>
  );
}
