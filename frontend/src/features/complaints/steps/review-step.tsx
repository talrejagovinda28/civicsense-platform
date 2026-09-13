"use client";

import { AccountabilityCard } from "@/features/accountability/accountability-card";
import { useComplaintWizard } from "../wizard-context";

export function ReviewStep() {
  const { draft } = useComplaintWizard();

  return (
    <div className="space-y-6">
      <p className="text-sm text-[var(--muted)]">
        Check everything looks correct before submitting your complaint.
      </p>

      {draft.images.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-[var(--muted)]">
            Photos
          </h3>
          <ul className="mt-2 grid gap-3 sm:grid-cols-3">
            {draft.images.map((image, index) => (
              <li key={image.cloudinaryPublicId}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={image.cloudinaryUrl}
                  alt={`Review photo ${index + 1}`}
                  className="h-28 w-full rounded-lg object-cover"
                />
              </li>
            ))}
          </ul>
        </div>
      )}

      <dl className="space-y-4">
        <ReviewRow label="Location" value={draft.address} />
        <ReviewRow
          label="Coordinates"
          value={
            draft.latitude !== null && draft.longitude !== null
              ? `${draft.latitude.toFixed(6)}, ${draft.longitude.toFixed(6)}`
              : null
          }
        />
        <ReviewRow label="City" value={draft.city} />
        <ReviewRow label="Category" value={draft.categoryName} />
        <ReviewRow label="Description" value={draft.description} />
      </dl>

      <AccountabilityCard
        citySlug={draft.citySlug}
        latitude={draft.latitude}
        longitude={draft.longitude}
        categoryId={draft.categoryId}
        compact
      />
    </div>
  );
}

function ReviewRow({
  label,
  value,
}: {
  label: string;
  value: string | null;
}) {
  return (
    <div className="border-b border-[var(--border)] pb-3">
      <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">{label}</dt>
      <dd className="mt-1 text-sm whitespace-pre-wrap">{value || "—"}</dd>
    </div>
  );
}
