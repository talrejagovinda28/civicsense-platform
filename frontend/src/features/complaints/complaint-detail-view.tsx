"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import {
  apiFetch,
  ComplaintDetail,
  ComplaintFeedItem,
  getComplaint,
  getNextStatusOptions,
  STATUS_LABELS,
  updateComplaintStatus,
  UserResponse,
} from "@/lib/api";

type ComplaintDetailViewProps = {
  complaintId: string;
};

export function ComplaintDetailView({ complaintId }: ComplaintDetailViewProps) {
  const { getToken, isLoaded } = useAuth();
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
    return <p className="text-sm text-neutral-500">Loading complaint…</p>;
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
  const nextStatuses = getNextStatusOptions(complaint.status, role);

  return (
    <ComplaintDetailContent
      complaint={complaint}
      canUpdateStatus={canUpdateStatus}
      nextStatuses={nextStatuses}
      selectedStatus={selectedStatus}
      note={note}
      updateError={updateError}
      isUpdating={statusMutation.isPending}
      onStatusChange={setSelectedStatus}
      onNoteChange={setNote}
      onSubmitUpdate={() => statusMutation.mutate()}
    />
  );
}

function ComplaintDetailContent({
  complaint,
  canUpdateStatus,
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
  canUpdateStatus: boolean;
  nextStatuses: { value: string; label: string }[];
  selectedStatus: string;
  note: string;
  updateError: string | null;
  isUpdating: boolean;
  onStatusChange: (value: string) => void;
  onNoteChange: (value: string) => void;
  onSubmitUpdate: () => void;
}) {
  return (
    <div className="space-y-8">
      <div>
        <p className="text-xs uppercase tracking-wide text-neutral-500">
          {complaint.category.name} · {STATUS_LABELS[complaint.status] ?? complaint.status}
        </p>
        <h2 className="mt-1 text-2xl font-bold">{complaint.title}</h2>
        <p className="mt-3 text-neutral-600">{complaint.description}</p>
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
        <DetailItem label="Area" value={complaint.ward ?? complaint.city} />
        <DetailItem
          label="Reported"
          value={new Date(complaint.created_at).toLocaleString()}
        />
        {complaint.address && <DetailItem label="Address" value={complaint.address} />}
      </dl>

      <section>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-neutral-500">
          Status Timeline
        </h3>
        <ol className="mt-4 space-y-4 border-l border-neutral-200 pl-4">
          {(complaint.status_history ?? []).map((entry) => (
            <li key={entry.id} className="relative">
              <span className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-neutral-900" />
              <p className="text-sm font-medium">
                {STATUS_LABELS[entry.status] ?? entry.status}
              </p>
              {entry.note && (
                <p className="mt-1 text-sm text-neutral-600">{entry.note}</p>
              )}
              <p className="mt-1 text-xs text-neutral-500">
                {new Date(entry.created_at).toLocaleString()}
              </p>
            </li>
          ))}
        </ol>
      </section>

      {canUpdateStatus && nextStatuses.length > 0 && (
        <section className="rounded-xl border border-neutral-200 bg-neutral-50 p-4">
          <h3 className="font-semibold">Update Status</h3>
          <div className="mt-4 space-y-3">
            <label className="block text-sm font-medium">
              New status
              <select
                value={selectedStatus}
                onChange={(event) => onStatusChange(event.target.value)}
                className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm"
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
                className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm"
              />
            </label>

            {updateError && <p className="text-sm text-red-600">{updateError}</p>}

            <button
              type="button"
              disabled={!selectedStatus || isUpdating}
              onClick={onSubmitUpdate}
              className="rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
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
      <dt className="text-xs uppercase tracking-wide text-neutral-500">{label}</dt>
      <dd className="mt-1 text-sm">{value}</dd>
    </div>
  );
}

export function ComplaintListItem({ complaint }: { complaint: ComplaintFeedItem }) {
  return (
    <Link
      href={`/complaints/${complaint.id}`}
      className="block rounded-xl border border-neutral-200 bg-white p-5 shadow-sm transition hover:border-neutral-400"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-wide text-neutral-500">
            {complaint.category.name} · {STATUS_LABELS[complaint.status] ?? complaint.status}
          </p>
          <h2 className="mt-1 font-semibold">{complaint.title}</h2>
          <p className="mt-2 line-clamp-2 text-sm text-neutral-600">{complaint.description}</p>
          <p className="mt-2 text-xs text-neutral-500">
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
