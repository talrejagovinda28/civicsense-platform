"use client";

import { useQuery } from "@tanstack/react-query";

import { AccountabilityResponse, getAccountability } from "@/lib/api";

type AccountabilityCardProps = {
  citySlug: string;
  latitude: number | null;
  longitude: number | null;
  categoryId: string | null;
  compact?: boolean;
};

function AccountabilityContent({
  data,
  compact,
}: {
  data: AccountabilityResponse;
  compact?: boolean;
}) {
  return (
    <div className="space-y-4">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-[var(--primary)]">
          Who is responsible
        </p>
        <p className="mt-1 text-sm text-[var(--muted)]">{data.municipality_name}</p>
      </div>

      {!data.inside_supported_area && (
        <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
          This location is outside the supported accountability area for this city.
        </p>
      )}

      {data.electoral_ward && (
        <div>
          <h4 className="text-xs uppercase tracking-wide text-[var(--muted)]">Ward</h4>
          <p className="mt-1 text-sm font-medium text-civic-navy">
            Ward {data.electoral_ward.ward_no} — {data.electoral_ward.name}
          </p>
        </div>
      )}

      {data.ward_office && (
        <div>
          <h4 className="text-xs uppercase tracking-wide text-[var(--muted)]">
            Ward office
          </h4>
          <p className="mt-1 text-sm font-medium text-civic-navy">{data.ward_office.name}</p>
        </div>
      )}

      {data.department && (
        <div>
          <h4 className="text-xs uppercase tracking-wide text-[var(--muted)]">
            Department
          </h4>
          <p className="mt-1 text-sm font-medium text-civic-navy">{data.department.name}</p>
        </div>
      )}

      {data.elected_representatives.length > 0 && (
        <div>
          <h4 className="text-xs uppercase tracking-wide text-[var(--muted)]">
            Elected representatives
          </h4>
          <ul className="mt-2 space-y-2">
            {data.elected_representatives.map((official) => (
              <li
                key={`${official.full_name}-${official.seat_label}`}
                className="rounded-lg bg-[var(--surface-muted)] px-3 py-2 text-sm"
              >
                <p className="font-medium text-civic-navy">{official.full_name}</p>
                <p className="text-[var(--muted)]">{official.seat_label}</p>
                {official.party && (
                  <p className="text-xs text-[var(--muted)]">{official.party}</p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!compact && data.routing_channels.length > 0 && (
        <div>
          <h4 className="text-xs uppercase tracking-wide text-[var(--muted)]">
            Official channels
          </h4>
          <ul className="mt-2 space-y-2">
            {data.routing_channels.map((channel) => (
              <li
                key={channel.id}
                className="rounded-lg border border-civic px-3 py-2 text-sm"
              >
                <p className="font-medium text-civic-navy">{channel.label}</p>
                {channel.url ? (
                  <a
                    href={channel.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[var(--primary)] hover:underline"
                  >
                    {channel.value}
                  </a>
                ) : (
                  <p className="text-[var(--muted)]">{channel.value}</p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {data.warnings.length > 0 && (
        <ul className="space-y-1">
          {data.warnings.map((warning) => (
            <li key={warning} className="text-xs text-amber-700">
              {warning}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function AccountabilityCard({
  citySlug,
  latitude,
  longitude,
  categoryId,
  compact = false,
}: AccountabilityCardProps) {
  const canFetch =
    latitude !== null && longitude !== null && categoryId !== null && categoryId !== "";

  const accountabilityQuery = useQuery({
    queryKey: ["accountability", citySlug, latitude, longitude, categoryId],
    queryFn: () =>
      getAccountability(citySlug, latitude!, longitude!, categoryId!),
    enabled: canFetch,
  });

  if (!canFetch) {
    return (
      <section className="rounded-xl border border-civic bg-[var(--surface)] p-4 shadow-civic-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-[var(--primary)]">
          Who is responsible
        </p>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Set a location and category to see who handles this issue.
        </p>
      </section>
    );
  }

  if (accountabilityQuery.isLoading) {
    return (
      <section className="rounded-xl border border-civic bg-[var(--surface)] p-4 shadow-civic-sm">
        <p className="text-sm text-[var(--muted)]">Loading accountability info…</p>
      </section>
    );
  }

  if (accountabilityQuery.error || !accountabilityQuery.data) {
    return (
      <section className="rounded-xl border border-civic bg-[var(--surface)] p-4 shadow-civic-sm">
        <p className="text-sm text-[var(--muted)]">
          Accountability data is not available for this location.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-xl border border-civic bg-[var(--surface)] p-4 shadow-civic-sm">
      <AccountabilityContent data={accountabilityQuery.data} compact={compact} />
    </section>
  );
}
