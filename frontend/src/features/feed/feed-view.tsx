"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { useCity } from "@/features/cities/city-context";
import { AppShell } from "@/features/shell/app-shell";
import { FeedItem, getFeed } from "@/lib/api";

import { FeedCard } from "./feed-card";

function FeedContent() {
  const { citySlug, selectedCity } = useCity();
  const { getToken, isLoaded } = useAuth();
  const searchParams = useSearchParams();
  const submitted = searchParams.get("submitted") === "1";
  const [extraItems, setExtraItems] = useState<FeedItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);

  const feedQuery = useQuery({
    queryKey: ["feed", citySlug],
    queryFn: async () => {
      const token = isLoaded ? await getToken() : null;
      setExtraItems([]);
      setNextCursor(null);
      return getFeed(citySlug, token);
    },
    enabled: isLoaded,
  });

  const initialCursor = feedQuery.data?.next_cursor ?? null;
  const effectiveCursor = nextCursor ?? initialCursor;
  const allItems = [...(feedQuery.data?.items ?? []), ...extraItems];
  const canLoadMore =
    !feedQuery.data?.fallback && effectiveCursor !== null && !feedQuery.isLoading;

  async function loadMore() {
    if (!effectiveCursor || loadingMore) {
      return;
    }
    setLoadingMore(true);
    try {
      const token = isLoaded ? await getToken() : null;
      const page = await getFeed(citySlug, token, effectiveCursor);
      setExtraItems((current) => [...current, ...page.items]);
      setNextCursor(page.next_cursor);
    } finally {
      setLoadingMore(false);
    }
  }

  const cityName = selectedCity?.name ?? citySlug;

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-civic-navy">Issue feed</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Public civic issues in {cityName}. Complaints and linked updates only.
          </p>
        </div>

        {submitted && (
          <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
            Your complaint was submitted successfully.
          </div>
        )}

        {feedQuery.isLoading && (
          <p className="text-sm text-[var(--muted)]">Loading feed…</p>
        )}

        {feedQuery.error && (
          <p className="text-sm text-red-600">
            Could not load the feed. Check that the API is running.
          </p>
        )}

        {feedQuery.data?.fallback && (
          <p className="rounded-lg border border-civic bg-[var(--surface-muted)] px-4 py-3 text-sm text-[var(--muted)]">
            Showing complaints list — blended feed API is not available yet.
          </p>
        )}

        {feedQuery.data && allItems.length === 0 && (
          <p className="text-sm text-[var(--muted)]">
            No public issues in {cityName} yet. Be the first to report one.
          </p>
        )}

        <ul className="space-y-4">
          {allItems.map((item) => (
            <li key={`${item.kind}-${item.complaint_id}-${item.id}`}>
              <FeedCard
                item={item}
                engagementUnavailable={feedQuery.data?.fallback}
              />
            </li>
          ))}
        </ul>

        {canLoadMore && (
          <button
            type="button"
            onClick={() => void loadMore()}
            disabled={loadingMore}
            className="w-full rounded-lg border border-civic px-4 py-2 text-sm font-medium text-civic-navy disabled:opacity-50"
          >
            {loadingMore ? "Loading…" : "Load more"}
          </button>
        )}
      </div>
    </AppShell>
  );
}

export function FeedView() {
  return (
    <Suspense
      fallback={
        <AppShell>
          <p className="text-sm text-[var(--muted)]">Loading feed…</p>
        </AppShell>
      }
    >
      <FeedContent />
    </Suspense>
  );
}
