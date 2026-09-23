import { notFound } from "next/navigation";

import { ReviewDemo } from "@/features/review/review-demo";

// This page is exclusively for illustrative, in-memory preview fixtures.
// It must never be accessible on the production deployment.
export const dynamic = "force-dynamic";

export default function ReviewPage() {
  if (process.env.VERCEL_ENV !== "preview") {
    notFound();
  }

  return <ReviewDemo />;
}
