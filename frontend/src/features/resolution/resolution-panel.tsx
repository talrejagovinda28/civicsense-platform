"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  ComplaintDetail,
  VERIFICATION_STATE_LABELS,
  confirmResolution,
  reviewResolution,
  submitResolutionEvidence,
} from "@/lib/api";

type ResolutionPanelProps = {
  complaint: ComplaintDetail;
  isOwner: boolean;
  isOfficer: boolean;
};

export function ResolutionPanel({
  complaint,
  isOwner,
  isOfficer,
}: ResolutionPanelProps) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const [assertion, setAssertion] = useState("");
  const [mediaUrl, setMediaUrl] = useState("");
  const [disputeReason, setDisputeReason] = useState("");
  const [reviewDecision, setReviewDecision] = useState("verified_resolved");
  const [reviewReason, setReviewReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const showPanel =
    complaint.status === "resolved" ||
    complaint.status === "in_progress" ||
    complaint.status === "closed";

  const verificationLabel =
    VERIFICATION_STATE_LABELS[complaint.verification_state ?? "none"] ??
    complaint.verification_state ??
    "Not verified";

  const evidenceMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      if (!token) {
        throw new Error("Sign in to submit evidence.");
      }
      if (!assertion.trim()) {
        throw new Error("Describe what was fixed.");
      }
      const result = await submitResolutionEvidence(token, complaint.id, {
        assertion: assertion.trim(),
        media_url: mediaUrl.trim() || null,
      });
      if (!result.ok) {
        throw new Error(result.error);
      }
      return result.data!;
    },
    onSuccess: () => {
      setAssertion("");
      setMediaUrl("");
      setError(null);
      setSuccess("Evidence submitted.");
      void queryClient.invalidateQueries({ queryKey: ["complaint", complaint.id] });
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Could not submit evidence.");
    },
  });

  const confirmMutation = useMutation({
    mutationFn: async (confirmed: boolean) => {
      const token = await getToken();
      if (!token) {
        throw new Error("Sign in to respond.");
      }
      const result = await confirmResolution(token, complaint.id, {
        confirmed,
        reason: confirmed ? null : disputeReason.trim() || null,
      });
      if (!result.ok) {
        throw new Error(result.error);
      }
      return result.data!;
    },
    onSuccess: (data) => {
      setDisputeReason("");
      setError(null);
      setSuccess(
        data?.verification_state === "disputed"
          ? "Resolution disputed."
          : "Resolution confirmed.",
      );
      void queryClient.invalidateQueries({ queryKey: ["complaint", complaint.id] });
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Could not save response.");
    },
  });

  const reviewMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      if (!token) {
        throw new Error("Sign in to review.");
      }
      const result = await reviewResolution(token, complaint.id, {
        decision: reviewDecision,
        reason: reviewReason.trim() || null,
      });
      if (!result.ok) {
        throw new Error(result.error);
      }
      return result.data!;
    },
    onSuccess: () => {
      setReviewReason("");
      setError(null);
      setSuccess("Review recorded.");
      void queryClient.invalidateQueries({ queryKey: ["complaint", complaint.id] });
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Review failed.");
    },
  });

  if (!showPanel) {
    return null;
  }

  return (
    <section className="rounded-xl border border-civic bg-[var(--surface-muted)] p-5">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
        Resolution verification
      </h3>
      <p className="mt-2 text-sm">
        Verification state:{" "}
        <span className="font-medium text-civic-navy">{verificationLabel}</span>
      </p>

      {(isOwner || isOfficer) && complaint.status !== "closed" && (
        <form
          className="mt-4 space-y-3 border-t border-civic pt-4"
          onSubmit={(event) => {
            event.preventDefault();
            evidenceMutation.mutate();
          }}
        >
          <p className="text-sm font-medium text-civic-navy">Submit resolution evidence</p>
          <label className="block text-sm font-medium">
            What was fixed?
            <textarea
              value={assertion}
              onChange={(event) => setAssertion(event.target.value)}
              rows={3}
              className="mt-1 w-full rounded-lg border border-civic px-3 py-2 text-sm"
              placeholder="Describe the fix or remaining issue…"
            />
          </label>
          <label className="block text-sm font-medium">
            Evidence URL (optional)
            <input
              type="url"
              value={mediaUrl}
              onChange={(event) => setMediaUrl(event.target.value)}
              placeholder="https://…"
              className="mt-1 w-full rounded-lg border border-civic px-3 py-2 text-sm"
            />
          </label>
          <button
            type="submit"
            disabled={evidenceMutation.isPending || !assertion.trim()}
            className="rounded-lg bg-civic-navy px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {evidenceMutation.isPending ? "Submitting…" : "Submit evidence"}
          </button>
        </form>
      )}

      {isOwner && complaint.status === "resolved" && (
        <div className="mt-4 space-y-3 border-t border-civic pt-4">
          <p className="text-sm font-medium text-civic-navy">Reporter confirmation</p>
          <p className="text-sm text-[var(--muted)]">
            Was this issue actually resolved to your satisfaction?
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={confirmMutation.isPending}
              onClick={() => confirmMutation.mutate(true)}
              className="rounded-lg bg-green-700 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              Yes, resolved
            </button>
            <button
              type="button"
              disabled={confirmMutation.isPending}
              onClick={() => confirmMutation.mutate(false)}
              className="rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-700 disabled:opacity-50"
            >
              No, still an issue
            </button>
          </div>
          <label className="block text-sm font-medium">
            Reason if disputing (optional)
            <input
              type="text"
              value={disputeReason}
              onChange={(event) => setDisputeReason(event.target.value)}
              className="mt-1 w-full rounded-lg border border-civic px-3 py-2 text-sm"
            />
          </label>
        </div>
      )}

      {isOfficer && (
        <form
          className="mt-4 space-y-3 border-t border-civic pt-4"
          onSubmit={(event) => {
            event.preventDefault();
            reviewMutation.mutate();
          }}
        >
          <p className="text-sm font-medium text-civic-navy">Officer review</p>
          <p className="text-xs text-[var(--muted)]">
            Verified resolved requires resolution evidence submitted by someone other
            than the reviewing officer. CivicSense never marks government filing as
            official without authentic confirmation.
          </p>
          <label className="block text-sm font-medium">
            Decision
            <select
              value={reviewDecision}
              onChange={(event) => setReviewDecision(event.target.value)}
              className="mt-1 w-full rounded-lg border border-civic px-3 py-2 text-sm"
            >
              <option value="verified_resolved">Verified resolved</option>
              <option value="accepted">Accept evidence</option>
              <option value="rejected">Reject / dispute</option>
            </select>
          </label>
          <label className="block text-sm font-medium">
            Reason (optional)
            <textarea
              value={reviewReason}
              onChange={(event) => setReviewReason(event.target.value)}
              rows={2}
              className="mt-1 w-full rounded-lg border border-civic px-3 py-2 text-sm"
            />
          </label>
          <button
            type="submit"
            disabled={reviewMutation.isPending}
            className="rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {reviewMutation.isPending ? "Saving…" : "Submit review"}
          </button>
        </form>
      )}

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      {success && <p className="mt-3 text-sm text-green-700">{success}</p>}
    </section>
  );
}
