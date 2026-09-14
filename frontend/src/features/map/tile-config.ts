/**
 * Base map tile configuration.
 * Swap this module to change tile providers without touching map components.
 */
export const ACTIVE_TILE_PROVIDER_ID = "openstreetmap-raster" as const;

export type MapTileProviderConfig = {
  id: string;
  tiles: readonly string[];
  tileSize: number;
  attribution: string;
  maxZoom: number;
};

export const OPENSTREETMAP_RASTER: MapTileProviderConfig = {
  id: ACTIVE_TILE_PROVIDER_ID,
  tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
  tileSize: 256,
  attribution: "© OpenStreetMap contributors",
  maxZoom: 19,
};

/** Active provider for the MVP — OpenStreetMap raster tiles (no API key). */
export const MAP_TILE_PROVIDER: MapTileProviderConfig = OPENSTREETMAP_RASTER;

export function createBaseMapStyle() {
  return {
    version: 8 as const,
    sources: {
      [MAP_TILE_PROVIDER.id]: {
        type: "raster" as const,
        tiles: [...MAP_TILE_PROVIDER.tiles],
        tileSize: MAP_TILE_PROVIDER.tileSize,
        attribution: MAP_TILE_PROVIDER.attribution,
        maxzoom: MAP_TILE_PROVIDER.maxZoom,
      },
    },
    layers: [
      {
        id: `${MAP_TILE_PROVIDER.id}-layer`,
        type: "raster" as const,
        source: MAP_TILE_PROVIDER.id,
      },
    ],
  };
}

export const DEFAULT_PUNE_CENTER = {
  lng: 73.8567,
  lat: 18.5204,
} as const;

export const DEFAULT_PUNE_ZOOM = 12;
