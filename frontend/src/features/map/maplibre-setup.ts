"use client";

import maplibregl from "maplibre-gl";

let workerConfigured = false;

/** Self-hosted worker shipped in /public/maplibre (see scripts/copy-maplibre-worker.mjs). */
const MAPLIBRE_WORKER_URL = "/maplibre/maplibre-gl-csp-worker.js";

/**
 * MapLibre requires a web worker. Use the app-hosted worker for reliable Vercel production.
 */
export function getMapLibre() {
  if (typeof window !== "undefined" && !workerConfigured) {
    maplibregl.setWorkerUrl(MAPLIBRE_WORKER_URL);
    workerConfigured = true;
  }

  return maplibregl;
}

/**
 * Ignore non-fatal tile/network errors so the map keeps rendering.
 */
export function isFatalMapError(message: string): boolean {
  const normalized = message.toLowerCase();
  if (
    normalized.includes("failed to fetch") ||
    normalized.includes("network") ||
    normalized.includes("could not be decoded") ||
    normalized.includes("aborted")
  ) {
    return false;
  }
  return true;
}

export function resizeMap(map: maplibregl.Map) {
  requestAnimationFrame(() => {
    map.resize();
  });
}
