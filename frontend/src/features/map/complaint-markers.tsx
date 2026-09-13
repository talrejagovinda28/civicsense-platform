"use client";

import { MarkerClusterer } from "@googlemaps/markerclusterer";
import { useEffect, useRef } from "react";

import { ComplaintFeedItem, STATUS_COLORS } from "@/lib/api";

type ComplaintMarkersProps = {
  map: google.maps.Map | null;
  complaints: ComplaintFeedItem[];
  onSelect?: (complaint: ComplaintFeedItem) => void;
  selectedId?: string | null;
};

function createMarkerIcon(color: string): google.maps.Symbol {
  return {
    path: google.maps.SymbolPath.CIRCLE,
    fillColor: color,
    fillOpacity: 0.95,
    strokeColor: "#ffffff",
    strokeWeight: 2,
    scale: 8,
  };
}

export function ComplaintMarkers({
  map,
  complaints,
  onSelect,
  selectedId,
}: ComplaintMarkersProps) {
  const clustererRef = useRef<MarkerClusterer | null>(null);
  const markersRef = useRef<google.maps.Marker[]>([]);

  useEffect(() => {
    if (!map) {
      return;
    }

    markersRef.current.forEach((marker) => marker.setMap(null));
    markersRef.current = [];
    clustererRef.current?.clearMarkers();
    clustererRef.current = null;

    const markers = complaints
      .filter(
        (complaint) =>
          complaint.public_latitude !== null && complaint.public_longitude !== null,
      )
      .map((complaint) => {
        const color = STATUS_COLORS[complaint.status] ?? "#64748b";
        const marker = new google.maps.Marker({
          position: {
            lat: complaint.public_latitude!,
            lng: complaint.public_longitude!,
          },
          map,
          icon: createMarkerIcon(color),
          title: complaint.title,
          zIndex: selectedId === complaint.id ? 1000 : 1,
        });

        marker.addListener("click", () => onSelect?.(complaint));
        return marker;
      });

    markersRef.current = markers;

    if (markers.length > 0) {
      clustererRef.current = new MarkerClusterer({ map, markers });
    }

    return () => {
      markersRef.current.forEach((marker) => marker.setMap(null));
      clustererRef.current?.clearMarkers();
    };
  }, [map, complaints, onSelect, selectedId]);

  return null;
}
