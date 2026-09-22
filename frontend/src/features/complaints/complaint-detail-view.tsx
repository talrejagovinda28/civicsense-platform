"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { AccountabilityCard } from "@/features/accountability/accountability-card";
import { ComplaintTimeline } from "@/features/complaints/complaint-timeline";
import { ResolutionPanel } from "@/features/resolution/resolution-panel";
import { OfficialSubmissionCard } from "@/features/submissions/official-submission-card";
import { CommentsSection } from "@/features/social/comments-section";
import { EngagementBar } from "@/features/social/engagement-bar";
import {
  apiFetch,
  ComplaintDetail,
  ComplaintFeedItem,
  EngagementCounts,
  getComplaint,
  getComplaintEngagement,
  getNextStatusOptions,
  STATUS_LABELS,
  updateComplaintStatus,
  UserResponse,
} from "@/lib/api";

type ComplaintDetailViewProps = {
  complaintId: string;
};

export function ComplaintDetailView({ complaintId }: ComplaintDetailViewProps) {
  const { getToken, isLoaded, userId } = useAuth();
  const queryClient = useQueryClient();
  const [selectedStatus, setSelectedStatus] = useState("");
  const [note, setNote] = useState("");
  const [updateError, setUpdateError] = useState<string | null>(null);

  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const token = await getToken();
      return apiFetch<UserResponse>("/api/v1/me", token);
    },
    enabled: isLoaded,
  });

  const complaintQuery = useQuery({
    queryKey: ["complaint", complaintId],
    queryFn: async () => {
      const token = await getToken();
      return getComplaint(token, complaintId);
    },
    enabled: isLoaded,
  });

  const engagementQuery = useQuery({
    queryKey: ["engagement", complaintId],
    queryFn: async () => {
      const token = await getToken();
      return getComplaintEngagement(token, complaintId);
    },
    enabled: isLoaded,
  });

  const statusMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      if (!token || !selectedStatus) {
        throw new Error("Missing auth or status selection.");
      }
      return updateComplaintStatus(token, complaintId, {
        status: selectedStatus,
        note: note.trim() || null,
      });
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["complaint", complaintId], data);
      setSelectedStatus("");
      setNote("");
      setUpdateError(null);
    },
    onError: (error) => {
      setUpdateError(
        error instanceof Error ? error.message : "Status update failed.",
      );
    },
  });

  if (complaintQuery.isLoading) {
    return <p className="text-sm text-[var(--muted)]">Loading complaint…</p>;
  }

  if (complaintQuery.error || !complaintQuery.data) {
    return (
      <p className="text-sm text-red-600">
        Could not load this complaint. It may not exist or the API is unavailable.
      </p>
    );
  }

  const complaint = complaintQuery.data;
  const role = meQuery.data?.role ?? "citizen";
  const canUpdateStatus = role === "officer" || role === "admin";
  const isOfficer = role === "officer" || role === "admin";
  const isOwner =
    complaint.viewer_is_owner ??
    (complaint.user_id !== undefined &&
      complaint.user_id !== null &&
      (complaint.user_id === userId || complaint.user_id === meQuery.data?.user_id));
  const nextStatuses = getNextStatusOptions(complaint.status, role);

  const mapLat = complaint.public_latitude ?? complaint.latitude ?? null;
  const mapLng = complaint.public_longitude ?? complaint.longitude ?? null;
  const citySlug = complaint.city.toLowerCase().replace(/\s+/g, "-");

  const engagement: EngagementCounts = engagementQuery.data ?? {
    like_count: 0,
    affected_count: 0,
    comment_count: 0,
    viewer_liked: false,
    viewer_affected: false,
  };

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_320px]">
      <ComplaintDetailContent
        complaint={complaint}
        engagement={engagement}
        engagementUnavailable={engagementQuery.data === null && !engagementQuery.isLoading}
        canUpdateStatus={canUpdateStatus}
        isOwner={isOwner}
        isOfficer={isOfficer}
        nextStatuses={nextStatuses}
        selectedStatus={selectedStatus}
        note={note}
        updateError={updateError}
        isUpdating={statusMutation.isPending}
        onStatusChange={setSelectedStatus}
        onNoteChange={setNote}
        onSubmitUpdate={() => statusMutation.mutate()}
      />

      <aside className="space-y-4">
        <AccountabilityCard
          citySlug={citySlug}
          latitude={mapLat}
          longitude={mapLng}
          categoryId={complaint.category.id}
        />
        <OfficialSubmissionCard complaint={complaint} />
      </aside>
    </div>
  );
}

function ComplaintDetailContent({
  complaint,
  engagement,
  engagementUnavailable,
  canUpdateStatus,
  isOwner,
  isOfficer,
  nextStatuses,
  selectedStatus,
  note,
  updateError,
  isUpdating,
  onStatusChange,
  onNoteChange,
  onSubmitUpdate,
}: {
  complaint: ComplaintDetail;
  engagement: EngagementCounts;
  engagementUnavailable: boolean;
  canUpdateStatus: boolean;
  isOwner: boolean;
  isOfficer: boolean;
  nextStatuses: { value: string; label: string }[];
  selectedStatus: string;
  note: string;
  updateError: string | null;
  isUpdating: boolean;
  onStatusChange: (value: string) => void;
  onNoteChange: (value: string) => void;
  onSubmitUpdate: () => void;
}) {
  const locationLabel =
    complaint.approximate_location_label ?? complaint.ward ?? complaint.city;

  return (
    <div className="space-y-8">
      <div>
        <p className="text-xs uppercase tracking-wide text-[var(--muted)]">
          {complaint.category.name} · {STATUS_LABELS[complaint.status] ?? complaint.status}
        </p>
        <h2 className="mt-1 text-2xl font-bold text-civic-navy">{complaint.title}</h2>
        <p className="mt-3 text-[var(--muted)]">{complaint.description}</p>
      </div>

      {complaint.images.length > 0 && (
        <ul className="grid gap-3 sm:grid-cols-3">
          {complaint.images.map((image) => (
            <li key={image.id}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={image.cloudinary_url}
                alt=""
                className="h-32 w-full rounded-lg object-cover"
              />
            </li>
          ))}
        </ul>
      )}

      <dl className="grid gap-4 sm:grid-cols-2">
        <DetailItem label="Area" value={locationLabel ?? "—"} />
        <DetailItem
          label="Reported"
          value={new Date(complaint.created_at).toLocaleString()}
        />
        {complaint.address && <DetailItem label="Address" value={complaint.address} />}
      </dl>

      <EngagementBar
        complaintId={complaint.id}
        initial={engagement}
        unavailable={engagementUnavailable}
      />

      <CommentsSection complaintId={complaint.id} />

      <ComplaintTimeline complaint={complaint} />

      <ResolutionPanel complaint={complaint} isOwner={isOwner} isOfficer={isOfficer} />

      {canUpdateStatus && nextStatuses.length > 0 && (
        <section className="rounded-xl border border-civic bg-[var(--surface-muted)] p-4">
          <h3 className="font-semibold text-civic-navy">Update Status</h3>
          <div className="mt-4 space-y-3">
            <label className="block text-sm font-medium">
              New status
              <select
                value={selectedStatus}
                onChange={(event) => onStatusChange(event.target.value)}
                className="mt-1 w-full rounded-lg border border-civic px-3 py-2 text-sm"
              >
                <option value="">Select status…</option>
                {nextStatuses.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="block text-sm font-medium">
              Note (optional)
              <textarea
                value={note}
                onChange={(event) => onNoteChange(event.target.value)}
                rows={3}
                placeholder="Add a note for the citizen…"
                className="mt-1 w-full rounded-lg border border-civic px-3 py-2 text-sm"
              />
            </label>

            {updateError && <p className="text-sm text-red-600">{updateError}</p>}

            <button
              type="button"
              disabled={!selectedStatus || isUpdating}
              onClick={onSubmitUpdate}
              className="rounded-lg bg-civic-navy px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
            >
              {isUpdating ? "Updating…" : "Save Status Update"}
            </button>
          </div>
        </section>
      )}
    </div>
  );
}

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-[var(--muted)]">{label}</dt>
      <dd className="mt-1 text-sm">{value}</dd>
    </div>
  );
}

export function ComplaintListItem({ complaint }: { complaint: ComplaintFeedItem }) {
  return (
    <Link
      href={`/complaints/${complaint.id}`}
      className="block rounded-xl border border-civic bg-[var(--surface)] p-5 shadow-civic-sm transition hover:border-[var(--border-strong)]"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-wide text-[var(--muted)]">
            {complaint.category.name} · {STATUS_LABELS[complaint.status] ?? complaint.status}
          </p>
          <h2 className="mt-1 font-semibold text-civic-navy">{complaint.title}</h2>
          <p className="mt-2 line-clamp-2 text-sm text-[var(--muted)]">
            {complaint.description}
          </p>
          <p className="mt-2 text-xs text-[var(--muted)]">
            {complaint.ward ?? complaint.city} ·{" "}
            {new Date(complaint.created_at).toLocaleDateString()}
          </p>
        </div>
        {complaint.images[0] && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={complaint.images[0].cloudinary_url}
            alt=""
            className="h-20 w-20 shrink-0 rounded-lg object-cover"
          />
        )}
      </div>
    </Link>
  );
}
