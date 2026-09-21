"use client";

import { useState } from "react";

import { EngagementCounts } from "@/lib/api";

import { AffectedButton } from "./affected-button";
import { LikeButton } from "./like-button";

type EngagementBarProps = {
  complaintId: string;
  initial: EngagementCounts;
  compact?: boolean;
  unavailable?: boolean;
};

export function EngagementBar({
  complaintId,
  initial,
  compact,
  unavailable,
}: EngagementBarProps) {
  const [engagement, setEngagement] = useState(initial);

  function handleUpdate(partial: Partial<EngagementCounts>) {
    setEngagement((current) => ({ ...current, ...partial }));
  }

  return (
    <div className="flex flex-wrap items-center gap-4">
      <LikeButton
        complaintId={complaintId}
        count={engagement.like_count}
        liked={engagement.viewer_liked}
        onUpdate={handleUpdate}
        disabled={unavailable}
        compact={compact}
      />
      <AffectedButton
        complaintId={complaintId}
        count={engagement.affected_count}
        affected={engagement.viewer_affected}
        onUpdate={handleUpdate}
        disabled={unavailable}
        compact={compact}
      />
      <span className="text-sm text-[var(--muted)]" aria-label={`${engagement.comment_count} comments`}>
        💬 {compact ? engagement.comment_count : `Comments (${engagement.comment_count})`}
      </span>
      {unavailable && (
        <span className="text-xs text-[var(--muted)]">Social actions pending API</span>
      )}
    </div>
  );
}
