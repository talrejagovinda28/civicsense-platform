"use client";

import { useAuth } from "@clerk/nextjs";
import { SignInButton } from "@clerk/nextjs";
import { useState } from "react";

import { EngagementCounts, likeComplaint, unlikeComplaint } from "@/lib/api";

type LikeButtonProps = {
  complaintId: string;
  count: number;
  liked: boolean;
  onUpdate: (next: Partial<EngagementCounts>) => void;
  disabled?: boolean;
  compact?: boolean;
};

export function LikeButton({
  complaintId,
  count,
  liked,
  onUpdate,
  disabled,
  compact,
}: LikeButtonProps) {
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

    onUpdate({
      like_count: liked ? Math.max(0, count - 1) : count + 1,
      viewer_liked: !liked,
    });

    const result = liked
      ? await unlikeComplaint(token, complaintId)
      : await likeComplaint(token, complaintId);

    if (result.ok) {
      onUpdate(result.data);
    }

    setPending(false);
  }

  const label = compact ? `${count}` : `Like (${count})`;

  if (!isSignedIn) {
    return (
      <SignInButton mode="modal">
        <button
          type="button"
          className="text-sm text-[var(--muted)] hover:text-civic-navy"
          aria-label={`Like, ${count} likes`}
        >
          ♡ {label}
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
        liked ? "text-[var(--primary)]" : "text-[var(--muted)] hover:text-civic-navy"
      } disabled:opacity-50`}
      aria-pressed={liked}
      aria-label={`${liked ? "Unlike" : "Like"}, ${count} likes`}
    >
      {liked ? "♥" : "♡"} {label}
    </button>
  );
}
