"use client";

import { useAuth } from "@clerk/nextjs";
import { SignInButton } from "@clerk/nextjs";
import { useState } from "react";

import { EngagementCounts, markAffected, unmarkAffected } from "@/lib/api";

type AffectedButtonProps = {
  complaintId: string;
  count: number;
  affected: boolean;
  onUpdate: (next: Partial<EngagementCounts>) => void;
  disabled?: boolean;
  compact?: boolean;
};

export function AffectedButton({
  complaintId,
  count,
  affected,
  onUpdate,
  disabled,
  compact,
}: AffectedButtonProps) {
  const { getToken, isSignedIn } = useAuth();
  const [pending, setPending] = useState(false);

  async function toggle() {
    if (disabled || pending) {
      return;
    }

    setPending(true);
    const token = await getToken();
    if (!token) {
      setPending(false);
      return;
    }

    const result = affected
      ? await unmarkAffected(token, complaintId)
      : await markAffected(token, complaintId);

    if (result.ok) {
      onUpdate(result.data);
    }

    setPending(false);
  }

  const label = compact ? `${count}` : `Affected (${count})`;

  if (!isSignedIn) {
    return (
      <SignInButton mode="modal">
        <button
          type="button"
          className="text-sm text-[var(--muted)] hover:text-civic-navy"
          aria-label={`Mark as affected, ${count} affected`}
        >
          ◉ {label}
        </button>
      </SignInButton>
    );
  }

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={disabled || pending}
      className={`text-sm transition ${
        affected ? "text-[var(--warning)]" : "text-[var(--muted)] hover:text-civic-navy"
      } disabled:opacity-50`}
      aria-pressed={affected}
      aria-label={`${affected ? "Remove affected mark" : "Mark as affected"}, ${count} affected`}
    >
      {affected ? "●" : "◉"} {label}
    </button>
  );
}
