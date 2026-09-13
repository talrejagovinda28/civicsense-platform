"use client";

import { MapPicker } from "../components/map-picker";
import { useComplaintWizard } from "../wizard-context";

export function LocationStep() {
  const { draft, updateDraft } = useComplaintWizard();

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
      onLocationChange={(location) =>
        updateDraft({
          latitude: location.latitude,
          longitude: location.longitude,
          address: location.address,
          googlePlaceId: location.googlePlaceId,
          ward: location.ward !== undefined ? location.ward : draft.ward,
        })
      }
    />
    </div>
  );
}
