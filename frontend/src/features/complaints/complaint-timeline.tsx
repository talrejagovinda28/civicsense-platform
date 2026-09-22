"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";

import {
  ComplaintDetail,
  STATUS_LABELS,
  TimelineEvent,
  getComplaintTimeline,
} from "@/lib/api";

type ComplaintTimelineProps = {
  complaint: ComplaintDetail;
};

const EVENT_LABELS: Record<string, string> = {
  submission_consent_created: "Submission authorized",
  submission_attempt: "Submission attempt",
  attestation_sent: "Reporter attested sent",
  reference_attached: "Reference attached",
  status_change: "Status updated",
};

function formatEventLabel(event: TimelineEvent): string {
  return EVENT_LABELS[event.event_type] ?? event.event_type.replace(/_/g, " ");
}

function formatEventDetail(event: TimelineEvent): string | null {
  const payload = event.public_payload;
  if (!payload) {
    return null;
  }
  if (typeof payload.outcome === "string") {
    return `Outcome: ${payload.outcome.replace(/_/g, " ")}`;
  }
  if (typeof payload.reference_value === "string") {
    return `Reference: ${payload.reference_value}`;
  }
  if (typeof payload.status === "string") {
    return STATUS_LABELS[payload.status] ?? payload.status;
  }
  return null;
}

export function ComplaintTimeline({ complaint }: ComplaintTimelineProps) {
  const { getToken, isLoaded } = useAuth();

  const timelineQuery = useQuery({
    queryKey: ["complaint-timeline", complaint.id],
    queryFn: async () => {
      const token = await getToken();
      return getComplaintTimeline(token, complaint.id);
    },
    enabled: isLoaded,
  });

  const events = timelineQuery.data?.items ?? [];
  const statusHistory = complaint.status_history ?? [];
  const useFallback = events.length === 0 && statusHistory.length > 0;

  return (
    <section>
      <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
        Timeline
      </h3>

      {timelineQuery.isLoading && (
        <p className="mt-4 text-sm text-[var(--muted)]">Loading timeline…</p>
      )}

      {!timelineQuery.isLoading && !useFallback && events.length === 0 && (
        <p className="mt-4 text-sm text-[var(--muted)]">No timeline events yet.</p>
      )}

      {!useFallback && events.length > 0 && (
        <ol className="mt-4 space-y-4 border-l border-civic pl-4">
          {events.map((event) => {
            const detail = formatEventDetail(event);
            return (
              <li key={event.id} className="relative">
                <span className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-[var(--primary)]" />
                <p className="text-sm font-medium">{formatEventLabel(event)}</p>
                {detail && (
                  <p className="mt-1 text-sm text-[var(--muted)]">{detail}</p>
                )}
                <p className="mt-1 text-xs text-[var(--muted)]">
                  {new Date(event.created_at).toLocaleString()}
                </p>
              </li>
            );
          })}
        </ol>
      )}

      {useFallback && (
        <>
          <p className="mt-2 text-xs text-[var(--muted)]">
            Showing status history — full timeline API not available yet.
          </p>
          <ol className="mt-4 space-y-4 border-l border-civic pl-4">
            {statusHistory.map((entry) => (
              <li key={entry.id} className="relative">
                <span className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-[var(--primary)]" />
                <p className="text-sm font-medium">
                  {STATUS_LABELS[entry.status] ?? entry.status}
                </p>
                {entry.note && (
                  <p className="mt-1 text-sm text-[var(--muted)]">{entry.note}</p>
                )}
                <p className="mt-1 text-xs text-[var(--muted)]">
                  {new Date(entry.created_at).toLocaleString()}
                </p>
              </li>
            ))}
          </ol>
        </>
      )}
    </section>
  );
}
