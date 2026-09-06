"use client";

import { MapPicker } from "../components/map-picker";
import { useComplaintWizard } from "../wizard-context";

export function LocationStep() {
  const { draft, updateDraft } = useComplaintWizard();

  return (
    <MapPicker
      latitude={draft.latitude}
      longitude={draft.longitude}
      address={draft.address}
      onLocationChange={(location) =>
        updateDraft({
          latitude: location.latitude,
          longitude: location.longitude,
          address: location.address,
          googlePlaceId: location.googlePlaceId,
        })
      }
    />
  );
}
