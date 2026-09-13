"use client";

import { useCity } from "./city-context";

function CityBadge({ status }: { status: string }) {
  if (status === "active") {
    return (
      <span className="rounded-full bg-green-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-green-700">
        Active
      </span>
    );
  }

  return (
    <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-700">
      Coming soon
    </span>
  );
}

export function CitySelector() {
  const { citySlug, setCitySlug, cities, isLoading, selectedCity } = useCity();

  if (isLoading && cities.length === 0) {
    return (
      <div className="h-9 w-40 animate-pulse rounded-lg bg-slate-200" aria-hidden />
    );
  }

  return (
    <label className="flex items-center gap-2 text-sm">
      <span className="sr-only">Select city</span>
      <select
        value={citySlug}
        onChange={(event) => setCitySlug(event.target.value)}
        className="rounded-lg border border-civic bg-white px-3 py-1.5 text-sm font-medium text-civic-navy shadow-civic-sm focus:border-[var(--primary)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-muted)]"
        aria-label="Select city"
      >
        {(cities.length > 0 ? cities : [{ slug: citySlug, name: selectedCity?.name ?? "Pune", state_name: selectedCity?.state_name ?? "Maharashtra", status: selectedCity?.status ?? "active" }]).map((city) => (
          <option key={city.slug} value={city.slug}>
            {city.name}, {city.state_name}
          </option>
        ))}
      </select>
      {selectedCity && <CityBadge status={selectedCity.status} />}
    </label>
  );
}
