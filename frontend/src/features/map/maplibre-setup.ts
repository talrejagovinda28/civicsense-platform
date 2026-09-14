"use client";

import maplibregl from "maplibre-gl";

/** Keep in sync with maplibre-gl version in package.json */
const MAPLIBRE_GL_VERSION = "4.7.1";

let workerConfigured = false;

/**
 * MapLibre requires a web worker. Next.js production bundles need an explicit worker URL.
 */
export function getMapLibre() {
  if (typeof window !== "undefined" && !workerConfigured) {
    maplibregl.setWorkerUrl(
      `https://unpkg.com/maplibre-gl@${MAPLIBRE_GL_VERSION}/dist/maplibre-gl-csp-worker.js`,
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
