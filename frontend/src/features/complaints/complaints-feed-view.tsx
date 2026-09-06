"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import { ComplaintListItem } from "@/features/complaints/complaint-detail-view";
import { apiFetch, PaginatedComplaints } from "@/lib/api";

export function ComplaintsFeedView() {
  const searchParams = useSearchParams();
  const submitted = searchParams.get("submitted") === "1";

  const feedQuery = useQuery({
    queryKey: ["complaints-feed"],
    queryFn: () => apiFetch<PaginatedComplaints>("/api/v1/complaints", null),
  });

  return (
    <main className="mx-auto min-h-screen max-w-3xl px-6 py-12">
      <div className="flex items-center justify-between">
        <div>
          <Link href="/" className="text-sm text-neutral-500 hover:text-neutral-700">
            ← Home
          </Link>
          <h1 className="mt-2 text-2xl font-bold">Pune Complaints</h1>
          <p className="mt-1 text-neutral-600">Public feed of reported civic issues.</p>
        </div>
        <Link
          href="/complaints/new"
          className="rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white"
        >
          Raise Complaint
        </Link>
      </div>

      {submitted && (
        <div className="mt-6 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
          Your complaint was submitted successfully.
        </div>
      )}

      {feedQuery.isLoading && (
        <p className="mt-8 text-sm text-neutral-500">Loading complaints…</p>
      )}

      {feedQuery.error && (
        <p className="mt-8 text-sm text-red-600">
          Could not load complaints. Check that the API and database are running.
        </p>
      )}

      {feedQuery.data && feedQuery.data.items.length === 0 && (
        <p className="mt-8 text-sm text-neutral-500">
          No complaints yet. Be the first to report an issue in Pune.
        </p>
      )}

      <ul className="mt-8 space-y-4">
        {feedQuery.data?.items.map((complaint) => (
          <li key={complaint.id}>
            <ComplaintListItem complaint={complaint} />
          </li>
        ))}
      </ul>
    </main>
  );
}
