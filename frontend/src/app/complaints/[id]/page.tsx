import Link from "next/link";

import { ComplaintDetailView } from "@/features/complaints/complaint-detail-view";

type ComplaintDetailPageProps = {
  params: Promise<{ id: string }>;
};

export default async function ComplaintDetailPage({ params }: ComplaintDetailPageProps) {
  const { id } = await params;

  return (
    <main className="mx-auto min-h-screen max-w-3xl px-6 py-12">
      <Link href="/complaints" className="text-sm text-neutral-500 hover:text-neutral-700">
        ← Back to feed
      </Link>
      <div className="mt-6">
        <ComplaintDetailView complaintId={id} />
      </div>
    </main>
  );
}
