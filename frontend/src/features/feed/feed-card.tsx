"use client";

import Link from "next/link";

import { EngagementBar } from "@/features/social/engagement-bar";
import { FeedItem, STATUS_LABELS } from "@/lib/api";

type FeedCardProps = {
  item: FeedItem;
  engagementUnavailable?: boolean;
};

export function FeedCard({ item, engagementUnavailable }: FeedCardProps) {
  const imageUrl = item.image_url ?? item.images?.[0]?.cloudinary_url ?? null;
  const locality = item.locality_label ?? "Locality unavailable";

  return (
    <article className="overflow-hidden rounded-xl border border-civic bg-[var(--surface)] shadow-civic-sm transition hover:border-[var(--border-strong)]">
      <Link href={`/complaints/${item.complaint_id}`} className="block">
        {imageUrl && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={imageUrl}
            alt=""
            className="aspect-[16/10] w-full object-cover"
          />
        )}

        <div className="space-y-2 p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              {item.category_name && (
                <p className="text-xs uppercase tracking-wide text-[var(--muted)]">
                  {item.category_name}
                  {item.kind === "update" ? " · Update" : ""}
                </p>
              )}
              <h2 className="mt-0.5 font-semibold text-civic-navy">{item.title}</h2>
            </div>
            <span className="shrink-0 rounded-full bg-[var(--surface-muted)] px-2.5 py-0.5 text-xs font-medium text-civic-navy">
              {STATUS_LABELS[item.status] ?? item.status}
            </span>
          </div>

          {item.description && (
            <p className="line-clamp-2 text-sm text-[var(--muted)]">{item.description}</p>
          )}

          <p className="text-xs text-[var(--muted)]">{locality}</p>

          <p className="text-xs text-[var(--muted)]">
            {item.responsibility_line ?? "Responsibility being verified"}
          </p>

          <p className="text-xs text-[var(--muted)]">
            {new Date(item.created_at).toLocaleDateString(undefined, {
              day: "numeric",
              month: "short",
              year: "numeric",
            })}
          </p>
        </div>
      </Link>

      <div className="border-t border-civic px-4 py-2">
        <EngagementBar
          complaintId={item.complaint_id}
          initial={{
            like_count: item.like_count,
            affected_count: item.affected_count,
            comment_count: item.comment_count,
            viewer_liked: item.viewer_liked ?? false,
            viewer_affected: item.viewer_affected ?? false,
          }}
          compact
          unavailable={engagementUnavailable}
        />
      </div>
    </article>
  );
}
