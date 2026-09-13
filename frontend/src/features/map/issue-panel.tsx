"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { ComplaintFeedItem, STATUS_LABELS } from "@/lib/api";

type IssuePanelProps = {
  complaints: ComplaintFeedItem[];
  isLoading?: boolean;
  selectedId?: string | null;
  onSelect?: (complaint: ComplaintFeedItem) => void;
};

const STATUS_FILTERS = [
  { value: "", label: "All" },
  { value: "submitted", label: "Submitted" },
  { value: "in_progress", label: "In Progress" },
  { value: "resolved", label: "Resolved" },
  { value: "closed", label: "Closed" },
];

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    submitted: "bg-blue-500",
    in_progress: "bg-amber-500",
    resolved: "bg-green-500",
    closed: "bg-slate-400",
  };

  return (
    <span
      className={`inline-block h-2 w-2 shrink-0 rounded-full ${colors[status] ?? "bg-slate-400"}`}
      aria-hidden
    />
  );
}

function IssueList({
  complaints,
  selectedId,
  onSelect,
}: {
  complaints: ComplaintFeedItem[];
  selectedId?: string | null;
  onSelect?: (complaint: ComplaintFeedItem) => void;
}) {
  if (complaints.length === 0) {
    return (
      <p className="px-4 py-8 text-center text-sm text-[var(--muted)]">
        No issues match your filters.
      </p>
    );
  }

  return (
    <ul className="divide-y divide-[var(--border)]">
      {complaints.map((complaint) => {
        const isSelected = selectedId === complaint.id;

        return (
          <li key={complaint.id}>
            <button
              type="button"
              onClick={() => onSelect?.(complaint)}
              className={`w-full px-4 py-3 text-left transition hover:bg-[var(--surface-muted)] ${
                isSelected ? "bg-[var(--primary-muted)]" : ""
              }`}
            >
              <div className="flex items-start gap-3">
                <StatusDot status={complaint.status} />
                <div className="min-w-0 flex-1">
                  <p className="text-xs text-[var(--muted)]">
                    {complaint.category.name} ·{" "}
                    {STATUS_LABELS[complaint.status] ?? complaint.status}
                  </p>
                  <p className="mt-0.5 truncate font-medium text-civic-navy">
                    {complaint.title}
                  </p>
                  <p className="mt-1 line-clamp-2 text-sm text-[var(--muted)]">
                    {complaint.description}
                  </p>
                  <p className="mt-1 text-xs text-[var(--muted)]">
                    {complaint.ward ?? complaint.city} ·{" "}
                    {new Date(complaint.created_at).toLocaleDateString()}
                  </p>
                </div>
                {complaint.images[0] && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={complaint.images[0].cloudinary_url}
                    alt=""
                    className="h-12 w-12 shrink-0 rounded-lg object-cover"
                  />
                )}
              </div>
            </button>
          </li>
        );
      })}
    </ul>
  );
}

export function IssuePanel({
  complaints,
  isLoading,
  selectedId,
  onSelect,
}: IssuePanelProps) {
  const [statusFilter, setStatusFilter] = useState("");
  const [mobileOpen, setMobileOpen] = useState(false);

  const filtered = useMemo(() => {
    if (!statusFilter) {
      return complaints;
    }
    return complaints.filter((c) => c.status === statusFilter);
  }, [complaints, statusFilter]);

  const panelContent = (
    <>
      <div className="border-b border-civic px-4 py-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-civic-navy">Public Issues</h2>
          <span className="text-xs text-[var(--muted)]">{filtered.length} shown</span>
        </div>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {STATUS_FILTERS.map((filter) => (
            <button
              key={filter.value}
              type="button"
              onClick={() => setStatusFilter(filter.value)}
              className={`rounded-full px-2.5 py-1 text-xs font-medium transition ${
                statusFilter === filter.value
                  ? "bg-[var(--primary)] text-white"
                  : "bg-[var(--surface-muted)] text-[var(--muted)] hover:text-civic-navy"
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      <div className="max-h-[calc(100vh-12rem)] overflow-y-auto md:max-h-[calc(100vh-8rem)]">
        {isLoading ? (
          <p className="px-4 py-8 text-center text-sm text-[var(--muted)]">Loading…</p>
        ) : (
          <IssueList
            complaints={filtered}
            selectedId={selectedId}
            onSelect={onSelect}
          />
        )}
      </div>

      {selectedId && (
        <div className="border-t border-civic px-4 py-3">
          <Link
            href={`/complaints/${selectedId}`}
            className="block w-full rounded-lg bg-[var(--primary)] px-4 py-2 text-center text-sm font-medium text-white hover:bg-[var(--primary-hover)]"
          >
            View full details
          </Link>
        </div>
      )}
    </>
  );

  return (
    <>
      {/* Desktop side panel */}
      <aside className="hidden h-full w-96 shrink-0 flex-col border-l border-civic bg-[var(--surface)] shadow-civic-md md:flex">
        {panelContent}
      </aside>

      {/* Mobile bottom sheet */}
      <div className="fixed inset-x-0 bottom-0 z-40 md:hidden">
        <button
          type="button"
          onClick={() => setMobileOpen((open) => !open)}
          className="flex w-full items-center justify-between rounded-t-xl border border-b-0 border-civic bg-[var(--surface)] px-4 py-3 shadow-civic-lg"
          aria-expanded={mobileOpen}
        >
          <span className="font-semibold text-civic-navy">
            Public Issues ({filtered.length})
          </span>
          <span className="text-sm text-[var(--muted)]">{mobileOpen ? "Hide" : "Show"}</span>
        </button>

        {mobileOpen && (
          <div className="max-h-[60vh] overflow-hidden border border-civic bg-[var(--surface)] shadow-civic-lg">
            {panelContent}
          </div>
        )}
      </div>
    </>
  );
}
