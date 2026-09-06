import { Suspense } from "react";

import { ComplaintsFeedView } from "@/features/complaints/complaints-feed-view";

export default function ComplaintsPage() {
  return (
    <Suspense
      fallback={
        <main className="mx-auto min-h-screen max-w-3xl px-6 py-12">
          <p className="text-sm text-neutral-500">Loading complaints…</p>
        </main>
      }
    >
      <ComplaintsFeedView />
    </Suspense>
  );
}
