"use client";

import { useComplaintWizard } from "../wizard-context";

export function ReviewStep() {
  const { draft } = useComplaintWizard();

  return (
    <div className="space-y-6">
      <p className="text-sm text-neutral-600">
        Check everything looks correct before submitting your complaint.
      </p>

      {draft.images.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-neutral-500">
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
    <div className="border-b border-neutral-100 pb-3">
      <dt className="text-xs uppercase tracking-wide text-neutral-500">{label}</dt>
      <dd className="mt-1 text-sm whitespace-pre-wrap">{value || "—"}</dd>
    </div>
  );
}
