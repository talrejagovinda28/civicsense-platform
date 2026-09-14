"use client";

import dynamic from "next/dynamic";
import { useCallback } from "react";

import { useComplaintWizard } from "../wizard-context";

const MapPicker = dynamic(
  () => import("../components/map-picker").then((module) => module.MapPicker),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-80 items-center justify-center rounded-lg border border-neutral-200 bg-neutral-50 text-sm text-neutral-500">
        Loading map…
      </div>
    ),
  },
);

export function LocationStep() {
  const { draft, updateDraft } = useComplaintWizard();

  const handleLocationChange = useCallback(
    (location: {
      latitude: number | null;
      longitude: number | null;
      address: string;
      googlePlaceId: string | null;
      ward?: string | null;
    }) => {
      updateDraft({
        latitude: location.latitude,
        longitude: location.longitude,
        address: location.address,
        googlePlaceId: location.googlePlaceId,
        ward: location.ward !== undefined ? location.ward : draft.ward,
      });
    },
    [draft.ward, updateDraft],
  );

  return (
    <div className="space-y-4">
      <aside
        className="rounded-lg border border-civic bg-[var(--surface-muted)] px-4 py-3 text-sm text-[var(--muted)]"
        aria-label="Location privacy notice"
      >
        <p className="font-medium text-civic-navy">How we use your location</p>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li>
            Location helps determine your ward, responsible department, and elected
            representatives.
          </li>
          <li>
            Photos and descriptions document the civic issue only — not hidden metadata.
          </li>
          <li>
            Public complaint pages show approximate coordinates and hide your exact address
            and identity.
          </li>
          <li>
            If you choose official PMC handoff, selected details may be sent to the
            government channel you open.
          </li>
        </ul>
      </aside>

      <MapPicker
      latitude={draft.latitude}
      longitude={draft.longitude}
      address={draft.address}
      ward={draft.ward}
      onLocationChange={handleLocationChange}
    />
    </div>
  );
}
