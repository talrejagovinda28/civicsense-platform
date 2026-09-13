import Link from "next/link";

import { ComplaintDetailView } from "@/features/complaints/complaint-detail-view";

type ComplaintDetailPageProps = {
  params: Promise<{ id: string }>;
};

export default async function ComplaintDetailPage({ params }: ComplaintDetailPageProps) {
  const { id } = await params;

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-12">
      <Link href="/complaints" className="text-sm text-[var(--muted)] hover:text-civic-navy">
        ← Back to feed
      </Link>
      <div className="mt-6">
        <ComplaintDetailView complaintId={id} />
      </div>
    </main>
  );
}
