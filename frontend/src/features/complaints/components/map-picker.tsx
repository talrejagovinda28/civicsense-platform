"use client";

import { Autocomplete, GoogleMap, Marker, useJsApiLoader } from "@react-google-maps/api";
import { useCallback, useEffect, useRef, useState } from "react";

const PUNE_CENTER = { lat: 18.5204, lng: 73.8567 };
const MAP_LIBRARIES: ("places")[] = ["places"];

export type MapLocation = {
  latitude: number;
  longitude: number;
  address: string;
  googlePlaceId: string;
};

type MapPickerProps = {
  latitude: number | null;
  longitude: number | null;
  address: string | null;
  onLocationChange: (location: MapLocation) => void;
};

export function MapPicker({
  latitude,
  longitude,
  address,
  onLocationChange,
}: MapPickerProps) {
  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ?? "";
  const autocompleteRef = useRef<google.maps.places.Autocomplete | null>(null);
  const [searchValue, setSearchValue] = useState(address ?? "");
  const [geocoding, setGeocoding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (address) {
      setSearchValue(address);
    }
  }, [address]);

  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: apiKey,
    libraries: MAP_LIBRARIES,
  });

  const reverseGeocode = useCallback(
    (lat: number, lng: number) => {
      if (!window.google) {
        return;
      }

      setGeocoding(true);
      setError(null);

      const geocoder = new google.maps.Geocoder();
      geocoder.geocode({ location: { lat, lng } }, (results, status) => {
        setGeocoding(false);

        if (status !== "OK" || !results?.[0]?.place_id) {
          setError("Could not resolve this location. Try searching for an address.");
          return;
        }

        onLocationChange({
          latitude: lat,
          longitude: lng,
          address: results[0].formatted_address,
          googlePlaceId: results[0].place_id,
        });
      });
    },
    [onLocationChange],
  );

  const handlePlaceChanged = () => {
    const place = autocompleteRef.current?.getPlace();
    const location = place?.geometry?.location;

    if (!location || !place?.place_id || !place.formatted_address) {
      setError("Select a place from the suggestions list.");
      return;
    }

    setError(null);
    onLocationChange({
      latitude: location.lat(),
      longitude: location.lng(),
      address: place.formatted_address,
      googlePlaceId: place.place_id,
    });
  };

  const handleMapClick = (event: google.maps.MapMouseEvent) => {
    if (!event.latLng) {
      return;
    }
    reverseGeocode(event.latLng.lat(), event.latLng.lng());
  };

  const handleMarkerDragEnd = (event: google.maps.MapMouseEvent) => {
    if (!event.latLng) {
      return;
    }
    reverseGeocode(event.latLng.lat(), event.latLng.lng());
  };

  if (!apiKey) {
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
        Add <code className="font-mono">NEXT_PUBLIC_GOOGLE_MAPS_API_KEY</code> to your{" "}
        <code className="font-mono">.env</code> file to enable the map picker.
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        Failed to load Google Maps. Check your API key and enabled APIs (Maps
        JavaScript API, Places API).
      </div>
    );
  }

  if (!isLoaded) {
    return (
      <div className="flex h-80 items-center justify-center rounded-lg border border-neutral-200 bg-neutral-50 text-sm text-neutral-500">
        Loading map…
      </div>
    );
  }

  const markerPosition =
    latitude !== null && longitude !== null
      ? { lat: latitude, lng: longitude }
      : null;

  return (
    <div className="space-y-4">
      <p className="text-sm text-neutral-600">
        Search for a place or tap the map to drop a pin on the issue location.
      </p>

      <Autocomplete
        onLoad={(autocomplete) => {
          autocompleteRef.current = autocomplete;
        }}
        onPlaceChanged={handlePlaceChanged}
        options={{
          componentRestrictions: { country: "in" },
          fields: ["place_id", "formatted_address", "geometry"],
        }}
      >
        <input
          type="text"
          placeholder="Search address in Pune…"
          value={searchValue}
          onChange={(event) => setSearchValue(event.target.value)}
          className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm"
        />
      </Autocomplete>

      <GoogleMap
        mapContainerClassName="h-80 w-full rounded-lg border border-neutral-200"
        center={markerPosition ?? PUNE_CENTER}
        zoom={markerPosition ? 16 : 12}
        onClick={handleMapClick}
        options={{
          streetViewControl: false,
          mapTypeControl: false,
          fullscreenControl: false,
        }}
      >
        {markerPosition && (
          <Marker
            position={markerPosition}
            draggable
            onDragEnd={handleMarkerDragEnd}
          />
        )}
      </GoogleMap>

      {geocoding && (
        <p className="text-sm text-neutral-500">Resolving address…</p>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      {address && latitude !== null && longitude !== null && (
        <div className="rounded-lg bg-neutral-50 px-4 py-3 text-sm">
          <p className="font-medium">{address}</p>
          <p className="mt-1 text-xs text-neutral-500">
            {latitude.toFixed(6)}, {longitude.toFixed(6)}
          </p>
        </div>
      )}
    </div>
  );
}
