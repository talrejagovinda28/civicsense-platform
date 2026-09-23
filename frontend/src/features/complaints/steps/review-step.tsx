"use client";

import { AccountabilityCard } from "@/features/accountability/accountability-card";
import { useComplaintWizard } from "../wizard-context";

export function ReviewStep() {
  const { draft, updateDraft } = useComplaintWizard();

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

      <section className="rounded-xl border border-civic bg-[var(--surface-muted)] p-4">
        <h3 className="text-sm font-semibold text-civic-navy">Privacy options</h3>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Choose how this report appears to others on CivicSense.
        </p>
        <div className="mt-4 space-y-3">
          <label className="flex items-start gap-3">
            <input
              type="checkbox"
              checked={draft.anonymousToPublic}
              onChange={(event) =>
                updateDraft({ anonymousToPublic: event.target.checked })
              }
              className="mt-0.5 h-4 w-4 rounded border-civic"
            />
            <span className="text-sm">
              <span className="font-medium text-civic-navy">
                Report anonymously on public pages
              </span>
              <span className="mt-0.5 block text-[var(--muted)]">
                Your name will not be shown on the feed, map, or public complaint page.
              </span>
            </span>
          </label>
          <label className="flex items-start gap-3">
            <input
              type="checkbox"
              checked={draft.isSensitive}
              onChange={(event) =>
                updateDraft({ isSensitive: event.target.checked })
              }
              className="mt-0.5 h-4 w-4 rounded border-civic"
            />
            <span className="text-sm">
              <span className="font-medium text-civic-navy">
                Confidential report (not public)
              </span>
              <span className="mt-0.5 block text-[var(--muted)]">
                Hides this report from the public feed and map. Only you and authorized
                officials can see full details.
              </span>
            </span>
          </label>
        </div>
      </section>
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
