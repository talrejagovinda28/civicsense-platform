"use client";

import type { Map as MapLibreMap } from "maplibre-gl";
import maplibreglImport from "maplibre-gl";

let workerConfigured = false;

/** Self-hosted CSP worker (see scripts/copy-maplibre-worker.mjs). */
const MAPLIBRE_WORKER_PATH = "/maplibre/maplibre-gl-csp-worker.js";

type MapLibreModule = typeof maplibreglImport & {
  default?: typeof maplibreglImport;
};

/**
 * Resolve the MapLibre namespace from the CSP bundle (webpack alias in next.config.ts).
 */
function resolveMapLibre() {
  const mod = maplibreglImport as MapLibreModule;
  return mod.default ?? mod;
}

/**
 * MapLibre requires a web worker. The CSP main + CSP worker builds must be used as a pair.
 */
export function getMapLibre() {
  const maplibregl = resolveMapLibre();

  if (typeof window !== "undefined" && !workerConfigured) {
    maplibregl.setWorkerUrl(
      new URL(MAPLIBRE_WORKER_PATH, window.location.origin).href,
    );
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

export function resizeMap(map: MapLibreMap) {
  requestAnimationFrame(() => {
    map.resize();
  });
}
