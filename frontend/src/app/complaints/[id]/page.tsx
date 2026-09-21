import Link from "next/link";

import { ComplaintDetailView } from "@/features/complaints/complaint-detail-view";
import { AppShell } from "@/features/shell/app-shell";

type ComplaintDetailPageProps = {
  params: Promise<{ id: string }>;
};

export default async function ComplaintDetailPage({ params }: ComplaintDetailPageProps) {
  const { id } = await params;

  return (
    <AppShell contentClassName="max-w-5xl">
      <div>
        <Link href="/" className="text-sm text-[var(--muted)] hover:text-civic-navy">
          ← Back to feed
        </Link>
        <div className="mt-6">
          <ComplaintDetailView complaintId={id} />
        </div>
      </div>
    </AppShell>
  );
}
