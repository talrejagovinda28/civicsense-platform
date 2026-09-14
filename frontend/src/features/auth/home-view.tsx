"use client";

import dynamic from "next/dynamic";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { AppHeader } from "@/features/shared/app-header";
import { useCity } from "@/features/cities/city-context";
import { MapErrorBoundary } from "@/features/map/map-error-boundary";
import { IssuePanel } from "@/features/map/issue-panel";
import { ComplaintFeedItem, getComplaints } from "@/lib/api";

import type { SelectedWard } from "@/features/map/civic-map";

const CivicMap = dynamic(
  () => import("@/features/map/civic-map").then((module) => module.CivicMap),
  {
    ssr: false,
    loading: () => (
      <div className="absolute inset-0 flex items-center justify-center bg-[var(--surface-muted)]">
        <p className="text-sm text-[var(--muted)]">Loading map…</p>
      </div>
    ),
  },
);

export function HomeView() {
  const { citySlug } = useCity();
  const [selectedComplaint, setSelectedComplaint] = useState<ComplaintFeedItem | null>(
    null,
  );
  const [selectedWard, setSelectedWard] = useState<SelectedWard | null>(null);

  const complaintsQuery = useQuery({
    queryKey: ["complaints", citySlug, selectedWard?.id ?? "all"],
    queryFn: () =>
      getComplaints({
        city: citySlug,
        electoral_ward_id: selectedWard?.id,
        limit: 100,
      }),
  });

  const complaints = complaintsQuery.data?.items ?? [];

  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <AppHeader />

      <div className="relative flex flex-1 overflow-hidden">
        <div className="relative isolate min-h-0 flex-1 pb-16 md:pb-0">
          <MapErrorBoundary>
            <CivicMap
              complaints={complaints}
              selectedComplaintId={selectedComplaint?.id}
              onSelectComplaint={setSelectedComplaint}
              selectedWard={selectedWard}
              onSelectWard={(ward) => {
                setSelectedWard(ward);
                if (ward) {
                  setSelectedComplaint(null);
                }
              }}
              className="absolute inset-0 min-h-[320px]"
            />
          </MapErrorBoundary>
        </div>

        <IssuePanel
          complaints={complaints}
          isLoading={complaintsQuery.isLoading}
          selectedId={selectedComplaint?.id}
          onSelect={setSelectedComplaint}
          selectedWard={selectedWard}
          onClearWard={() => setSelectedWard(null)}
        />
      </div>
    </div>
  );
}
