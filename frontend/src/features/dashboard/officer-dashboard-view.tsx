"use client";

import { useAuth, UserButton } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { ComplaintListItem } from "@/features/complaints/complaint-detail-view";
import { getOfficerQueue } from "@/lib/api";

export function OfficerDashboardView() {
  const { getToken, isLoaded } = useAuth();

  const queueQuery = useQuery({
    queryKey: ["officer-queue"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) {
        throw new Error("Not authenticated");
      }
      return getOfficerQueue(token);
    },
    enabled: isLoaded,
  });

  return (
    <main className="mx-auto min-h-screen max-w-3xl px-6 py-12">
      <div className="flex items-center justify-between">
        <div>
          <Link href="/dashboard" className="text-sm text-neutral-500 hover:text-neutral-700">
            ← Dashboard
          </Link>
          <h1 className="mt-2 text-2xl font-bold">Officer Dashboard</h1>
          <p className="mt-1 text-neutral-600">
            Open complaints needing action in Pune.
          </p>
        </div>
        <UserButton />
      </div>

      {queueQuery.isLoading && (
        <p className="mt-8 text-sm text-neutral-500">Loading queue…</p>
      )}

      {queueQuery.error && (
        <p className="mt-8 text-sm text-red-600">
          Could not load officer queue. Ensure your Clerk role is officer or admin.
        </p>
      )}

      {queueQuery.data && queueQuery.data.length === 0 && (
        <p className="mt-8 text-sm text-neutral-500">No open complaints right now.</p>
      )}

      <ul className="mt-8 space-y-4">
        {queueQuery.data?.map((complaint) => (
          <li key={complaint.id}>
            <ComplaintListItem complaint={complaint} />
          </li>
        ))}
      </ul>
    </main>
  );
}
