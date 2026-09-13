"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { ComplaintListItem } from "@/features/complaints/complaint-detail-view";
import { useCity } from "@/features/cities/city-context";
import { AppHeader } from "@/features/shared/app-header";
import { getOfficerQueue } from "@/lib/api";

export function OfficerDashboardView() {
  const { getToken, isLoaded } = useAuth();
  const { selectedCity, citySlug } = useCity();

  const queueQuery = useQuery({
    queryKey: ["officer-queue", citySlug],
    queryFn: async () => {
      const token = await getToken();
      if (!token) {
        throw new Error("Not authenticated");
      }
      return getOfficerQueue(token, selectedCity?.name ?? "Pune");
    },
    enabled: isLoaded,
  });

  return (
    <>
      <AppHeader />
      <main className="mx-auto min-h-screen max-w-3xl px-6 py-12">
        <div>
          <Link href="/dashboard" className="text-sm text-[var(--muted)] hover:text-civic-navy">
            ← Dashboard
          </Link>
          <h1 className="mt-2 text-2xl font-bold text-civic-navy">Officer Dashboard</h1>
          <p className="mt-1 text-[var(--muted)]">
            Open complaints needing action in {selectedCity?.name ?? "Pune"}.
          </p>
        </div>

        {queueQuery.isLoading && (
          <p className="mt-8 text-sm text-[var(--muted)]">Loading queue…</p>
        )}

        {queueQuery.error && (
          <p className="mt-8 text-sm text-red-600">
            Could not load officer queue. Ensure your Clerk role is officer or admin.
          </p>
        )}

        {queueQuery.data && queueQuery.data.length === 0 && (
          <p className="mt-8 text-sm text-[var(--muted)]">No open complaints right now.</p>
        )}

        <ul className="mt-8 space-y-4">
          {queueQuery.data?.map((complaint) => (
            <li key={complaint.id}>
              <ComplaintListItem complaint={complaint} />
            </li>
          ))}
        </ul>
      </main>
    </>
  );
}
