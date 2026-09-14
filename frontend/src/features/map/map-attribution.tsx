import { MAP_TILE_PROVIDER } from "./tile-config";

type MapAttributionProps = {
  className?: string;
};

export function MapAttribution({ className = "" }: MapAttributionProps) {
  return (
    <div
      className={`pointer-events-none absolute bottom-2 left-2 z-10 rounded bg-white/90 px-2 py-1 text-[10px] leading-tight text-slate-700 shadow-sm ${className}`}
      aria-label="Map attribution"
    >
      {MAP_TILE_PROVIDER.attribution}
    </div>
  );
}
