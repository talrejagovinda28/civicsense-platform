"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  ComplaintDetail,
  ExternalSubmissionResponse,
  saveExternalSubmissionToken,
  startExternalSubmission,
} from "@/lib/api";

type OfficialHandoffCardProps = {
  complaint: ComplaintDetail;
};

const PMC_PORTAL_URL = "https://pmc.gov.in/en/online-complaint";

export function OfficialHandoffCard({ complaint }: OfficialHandoffCardProps) {
  const { getToken, userId } = useAuth();
  const queryClient = useQueryClient();
  const [externalToken, setExternalToken] = useState("");
  const [statusUrl, setStatusUrl] = useState("");
  const [error, setError] = useState<string | null>(null);

  const isOwner = complaint.user_id === userId;
  const submission = complaint.external_submission;

  const startMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      if (!token) {
        throw new Error("Sign in to start PMC handoff.");
      }
      return startExternalSubmission(token, complaint.id);
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["complaint", complaint.id], {
        ...complaint,
        external_submission: data,
      });
      setError(null);
      window.open(PMC_PORTAL_URL, "_blank", "noopener,noreferrer");
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Could not start handoff.");
    },
  });

  const tokenMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      if (!token) {
        throw new Error("Sign in to save your PMC token.");
      }
      if (!externalToken.trim()) {
        throw new Error("Enter the PMC complaint reference number.");
      }
      return saveExternalSubmissionToken(token, complaint.id, {
        external_token: externalToken.trim(),
        status_url: statusUrl.trim() || null,
      });
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["complaint", complaint.id], {
        ...complaint,
        external_submission: data,
      });
      setExternalToken("");
      setStatusUrl("");
      setError(null);
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Could not save token.");
    },
  });

  if (!isOwner) {
    return null;
  }

  return (
    <section className="rounded-xl border border-civic bg-[var(--surface-muted)] p-5 shadow-civic-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-[var(--primary)]">
        PMC official handoff
      </p>
      <h3 className="mt-1 font-semibold text-civic-navy">
        Forward to Pune Municipal Corporation
      </h3>
      <p className="mt-2 text-sm text-[var(--muted)]">
        Submit your issue on the official PMC portal, then save the reference number here
        so you can track it in CivicSense.
      </p>

      {submission && (
        <HandoffStatus submission={submission} />
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => startMutation.mutate()}
          disabled={startMutation.isPending}
          className="rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--primary-hover)] disabled:opacity-50"
        >
          {startMutation.isPending ? "Starting…" : "Open PMC portal"}
        </button>
        <a
          href={PMC_PORTAL_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-lg border border-civic px-4 py-2 text-sm font-medium text-civic-navy hover:bg-white"
        >
          PMC link
        </a>
      </div>

      <form
        className="mt-4 space-y-3"
        onSubmit={(event) => {
          event.preventDefault();
          tokenMutation.mutate();
        }}
      >
        <label className="block text-sm font-medium">
          PMC reference number
          <input
            type="text"
            value={externalToken}
            onChange={(event) => setExternalToken(event.target.value)}
            placeholder="e.g. PMC-2025-12345"
            className="mt-1 w-full rounded-lg border border-civic px-3 py-2 text-sm"
          />
        </label>

        <label className="block text-sm font-medium">
          Status URL (optional)
          <input
            type="url"
            value={statusUrl}
            onChange={(event) => setStatusUrl(event.target.value)}
            placeholder="https://…"
            className="mt-1 w-full rounded-lg border border-civic px-3 py-2 text-sm"
          />
        </label>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={tokenMutation.isPending || !externalToken.trim()}
          className="rounded-lg bg-civic-navy px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {tokenMutation.isPending ? "Saving…" : "Save PMC reference"}
        </button>
      </form>
    </section>
  );
}

function HandoffStatus({ submission }: { submission: ExternalSubmissionResponse }) {
  const statusLabels: Record<string, string> = {
    pending: "Not started",
    handoff_started: "Portal opened",
    token_received: "Reference saved",
    forwarded: "Forwarded",
  };

  return (
    <div className="mt-4 rounded-lg border border-civic bg-white px-4 py-3 text-sm">
      <p className="font-medium text-civic-navy">
        Status: {statusLabels[submission.status] ?? submission.status}
      </p>
      {submission.external_token && (
        <p className="mt-1 text-[var(--muted)]">
          Reference: <span className="font-mono">{submission.external_token}</span>
        </p>
      )}
      {submission.status_url && (
        <a
          href={submission.status_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-1 inline-block text-[var(--primary)] hover:underline"
        >
          Track on PMC
        </a>
      )}
    </div>
  );
}
