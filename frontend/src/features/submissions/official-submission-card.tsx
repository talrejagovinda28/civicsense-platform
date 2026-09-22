"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { OfficialHandoffCard } from "@/features/routing/official-handoff-card";
import {
  ComplaintDetail,
  ConsentResponse,
  DispatchResponse,
  createSubmissionConsent,
  dispatchSubmission,
  attestSubmissionSent,
  attachSubmissionReference,
  getAccountability,
  getComplaintSubmissionChannels,
  SubmissionChannelSummary,
} from "@/lib/api";

type OfficialSubmissionCardProps = {
  complaint: ComplaintDetail;
};

function generateIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID().replace(/-/g, "");
  }
  return `idem-${Date.now()}-${Math.random().toString(36).slice(2, 12)}`;
}

function buildDisclosure(complaint: ComplaintDetail): Record<string, unknown> {
  return {
    summary: complaint.title,
    description: complaint.description,
    category: complaint.category.name,
    location: complaint.address ?? complaint.ward ?? complaint.city,
  };
}

export function OfficialSubmissionCard({ complaint }: OfficialSubmissionCardProps) {
  const { getToken, userId } = useAuth();
  const [consentAccepted, setConsentAccepted] = useState(false);
  const [selectedChannelId, setSelectedChannelId] = useState<string>("");
  const [consent, setConsent] = useState<ConsentResponse | null>(null);
  const [dispatchResult, setDispatchResult] = useState<DispatchResponse | null>(null);
  const [referenceValue, setReferenceValue] = useState("");
  const [trackingUrl, setTrackingUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [legacyOpen, setLegacyOpen] = useState(false);

  const isOwner =
    complaint.viewer_is_owner ??
    (complaint.user_id !== undefined &&
      complaint.user_id !== null &&
      complaint.user_id === userId);
  const citySlug = complaint.city.toLowerCase().replace(/\s+/g, "-");
  const mapLat = complaint.public_latitude ?? complaint.latitude ?? null;
  const mapLng = complaint.public_longitude ?? complaint.longitude ?? null;

  const channelsQuery = useQuery({
    queryKey: ["submission-channels", complaint.id],
    queryFn: async () => {
      const token = await getToken();
      return getComplaintSubmissionChannels(token, complaint.id);
    },
    enabled: isOwner,
  });

  const accountabilityQuery = useQuery({
    queryKey: ["accountability", citySlug, mapLat, mapLng, complaint.category.id],
    queryFn: () =>
      getAccountability(citySlug, mapLat!, mapLng!, complaint.category.id),
    enabled: isOwner && mapLat !== null && mapLng !== null,
  });

  const availableChannels = useMemo(() => {
    const apiChannels = channelsQuery.data ?? [];
    if (apiChannels.length > 0) {
      return apiChannels.map((channel) => ({
        id: channel.id,
        label: channel.label,
        url: channel.url ?? null,
        enabled: channel.enabled,
        source: "api" as const,
      }));
    }
    const routing = accountabilityQuery.data?.routing_channels ?? [];
    return routing.map((channel) => ({
      id: channel.id,
      label: channel.label,
      url: channel.url,
      enabled: channel.is_official,
      source: "routing" as const,
    }));
  }, [channelsQuery.data, accountabilityQuery.data]);

  const consentMutation = useMutation({
    mutationFn: async (channelId: string) => {
      const token = await getToken();
      if (!token) {
        throw new Error("Sign in to authorize submission.");
      }
      const result = await createSubmissionConsent(token, complaint.id, {
        channel_id: channelId,
        disclosure_json: buildDisclosure(complaint),
      });
      if (!result.ok) {
        throw new Error(result.error);
      }
      return result.data!;
    },
    onSuccess: (data) => {
      setConsent(data);
      setError(null);
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Could not create consent.");
    },
  });

  const dispatchMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      if (!token || !consent) {
        throw new Error("Consent required before dispatch.");
      }
      const result = await dispatchSubmission(token, complaint.id, {
        consent_id: consent.id,
        idempotency_key: generateIdempotencyKey(),
      });
      if (!result.ok) {
        throw new Error(result.error);
      }
      return result.data!;
    },
    onSuccess: (data) => {
      setDispatchResult(data);
      setError(null);
      const metadata = data.metadata ?? {};
      const portalUrl =
        (metadata.portal_url as string | undefined) ??
        (metadata.whatsapp_url as string | undefined);
      if (portalUrl && data.status === "user_action_required") {
        window.open(portalUrl, "_blank", "noopener,noreferrer");
      }
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Dispatch failed.");
    },
  });

  const attestMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      const intentId = dispatchResult?.intent_id;
      if (!token || !intentId) {
        throw new Error("No submission intent to attest.");
      }
      const result = await attestSubmissionSent(token, intentId);
      if (!result.ok) {
        throw new Error(result.error);
      }
      return result.data!;
    },
    onSuccess: () => setError(null),
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Attestation failed.");
    },
  });

  const referenceMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      const intentId = dispatchResult?.intent_id;
      if (!token || !intentId) {
        throw new Error("No submission intent for reference.");
      }
      if (!referenceValue.trim()) {
        throw new Error("Enter a reference value.");
      }
      const result = await attachSubmissionReference(token, intentId, {
        reference_value: referenceValue.trim(),
        tracking_url: trackingUrl.trim() || null,
      });
      if (!result.ok) {
        throw new Error(result.error);
      }
      return result.data!;
    },
    onSuccess: () => {
      setReferenceValue("");
      setTrackingUrl("");
      setError(null);
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Could not attach reference.");
    },
  });

  if (!isOwner) {
    return null;
  }

  const metadata = dispatchResult?.metadata ?? {};
  const actionUrl =
    (metadata.portal_url as string | undefined) ??
    (metadata.whatsapp_url as string | undefined);
  const showUserAction = dispatchResult?.status === "user_action_required";

  return (
    <section className="rounded-xl border border-civic bg-[var(--surface-muted)] p-5 shadow-civic-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-[var(--primary)]">
        Official submission
      </p>
      <h3 className="mt-1 font-semibold text-civic-navy">
        Submit to an official channel
      </h3>
      <p className="mt-2 text-sm text-[var(--muted)]">
        Authorize CivicSense to prepare your complaint for an official routing channel.
        You may need to complete the final step yourself on a portal or messaging app.
      </p>

      {availableChannels.length === 0 && !channelsQuery.isLoading && (
        <p className="mt-4 rounded-lg border border-civic bg-white px-3 py-2 text-sm text-[var(--muted)]">
          No submission channels are listed yet. Channels must be enabled for your city
          before automated handoff is available.
        </p>
      )}

      {availableChannels.length > 0 && (
        <div className="mt-4 space-y-3">
          <label className="block text-sm font-medium">
            Channel
            <select
              value={selectedChannelId}
              onChange={(event) => {
                setSelectedChannelId(event.target.value);
                setConsent(null);
                setDispatchResult(null);
              }}
              className="mt-1 w-full rounded-lg border border-civic px-3 py-2 text-sm"
            >
              <option value="">Select a channel…</option>
              {availableChannels.map((channel) => (
                <option key={channel.id} value={channel.id}>
                  {channel.label}
                  {!channel.enabled ? " (not enabled)" : ""}
                </option>
              ))}
            </select>
          </label>

          {selectedChannelId && (
            <label className="flex items-start gap-3 text-sm">
              <input
                type="checkbox"
                checked={consentAccepted}
                onChange={(event) => setConsentAccepted(event.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-civic"
              />
              <span>
                I authorize CivicSense to disclose the complaint summary above to the
                selected channel for this one-time submission attempt.
              </span>
            </label>
          )}

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={
                !selectedChannelId ||
                !consentAccepted ||
                consentMutation.isPending ||
                !!consent
              }
              onClick={() => consentMutation.mutate(selectedChannelId)}
              className="rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              {consentMutation.isPending ? "Authorizing…" : "Authorize disclosure"}
            </button>

            <button
              type="button"
              disabled={!consent || dispatchMutation.isPending}
              onClick={() => dispatchMutation.mutate()}
              className="rounded-lg bg-civic-navy px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
            >
              {dispatchMutation.isPending ? "Dispatching…" : "Dispatch submission"}
            </button>
          </div>
        </div>
      )}

      {dispatchResult && (
        <div className="mt-4 rounded-lg border border-civic bg-white px-4 py-3 text-sm">
          <p className="font-medium text-civic-navy">
            Status: {dispatchResult.status.replace(/_/g, " ")}
          </p>
          {dispatchResult.message && (
            <p className="mt-1 text-[var(--muted)]">{dispatchResult.message}</p>
          )}
          {showUserAction && (
            <div className="mt-3 space-y-2">
              <p className="font-medium text-amber-800">Action required</p>
              {typeof metadata.instructions === "string" &&
                metadata.instructions.length > 0 && (
                <p className="text-[var(--muted)]">{metadata.instructions}</p>
              )}
              {actionUrl && (
                <a
                  href={actionUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block text-[var(--primary)] hover:underline"
                >
                  Open portal / WhatsApp link
                </a>
              )}
              <button
                type="button"
                disabled={attestMutation.isPending}
                onClick={() => attestMutation.mutate()}
                className="mt-2 rounded-lg border border-civic px-4 py-2 text-sm font-medium text-civic-navy disabled:opacity-50"
              >
                {attestMutation.isPending ? "Saving…" : "I sent it"}
              </button>
            </div>
          )}
        </div>
      )}

      {dispatchResult?.intent_id && (
        <form
          className="mt-4 space-y-3 border-t border-civic pt-4"
          onSubmit={(event) => {
            event.preventDefault();
            referenceMutation.mutate();
          }}
        >
          <p className="text-sm font-medium text-civic-navy">
            Unverified reference (pending review)
          </p>
          <p className="text-xs text-[var(--muted)]">
            If you received a reference number from the channel, you can attach it here.
            CivicSense has not independently verified this reference.
          </p>
          <label className="block text-sm font-medium">
            Reference value
            <input
              type="text"
              value={referenceValue}
              onChange={(event) => setReferenceValue(event.target.value)}
              placeholder="e.g. ticket or complaint ID"
              className="mt-1 w-full rounded-lg border border-civic px-3 py-2 text-sm"
            />
          </label>
          <label className="block text-sm font-medium">
            Tracking URL (optional)
            <input
              type="url"
              value={trackingUrl}
              onChange={(event) => setTrackingUrl(event.target.value)}
              placeholder="https://…"
              className="mt-1 w-full rounded-lg border border-civic px-3 py-2 text-sm"
            />
          </label>
          <button
            type="submit"
            disabled={referenceMutation.isPending || !referenceValue.trim()}
            className="rounded-lg bg-civic-navy px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {referenceMutation.isPending ? "Saving…" : "Attach unverified reference"}
          </button>
        </form>
      )}

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      <div className="mt-6 border-t border-civic pt-4">
        <button
          type="button"
          onClick={() => setLegacyOpen((open) => !open)}
          className="text-sm font-medium text-[var(--muted)] hover:text-civic-navy"
        >
          {legacyOpen ? "Hide" : "Show"} legacy PMC portal handoff
        </button>
        {legacyOpen && (
          <div className="mt-3">
            <OfficialHandoffCard complaint={complaint} />
          </div>
        )}
      </div>
    </section>
  );
}
