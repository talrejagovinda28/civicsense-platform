"use client";

import { useAuth } from "@clerk/nextjs";
import { SignInButton } from "@clerk/nextjs";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { getComments, postComment } from "@/lib/api";

type CommentsSectionProps = {
  complaintId: string;
};

export function CommentsSection({ complaintId }: CommentsSectionProps) {
  const { getToken, isSignedIn, isLoaded } = useAuth();
  const queryClient = useQueryClient();
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);

  const commentsQuery = useQuery({
    queryKey: ["comments", complaintId],
    queryFn: () => getComments(complaintId),
    enabled: isLoaded,
  });

  const postMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      if (!token || !body.trim()) {
        throw new Error("Sign in and enter a comment.");
      }
      const result = await postComment(token, complaintId, body.trim());
      if (!result.ok) {
        throw new Error(result.error);
      }
      return result.data;
    },
    onSuccess: () => {
      setBody("");
      setError(null);
      void queryClient.invalidateQueries({ queryKey: ["comments", complaintId] });
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Could not post comment.");
    },
  });

  const unavailable = commentsQuery.data === null && !commentsQuery.isLoading;

  return (
    <section className="space-y-4">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
        Comments
      </h3>

      {commentsQuery.isLoading && (
        <p className="text-sm text-[var(--muted)]">Loading comments…</p>
      )}

      {unavailable && (
        <p className="rounded-lg border border-civic bg-[var(--surface-muted)] px-4 py-3 text-sm text-[var(--muted)]">
          Comments are not available yet — the API endpoint is not deployed.
        </p>
      )}

      {commentsQuery.data && commentsQuery.data.items.length === 0 && (
        <p className="text-sm text-[var(--muted)]">No comments yet.</p>
      )}

      {commentsQuery.data && commentsQuery.data.items.length > 0 && (
        <ul className="space-y-3">
          {commentsQuery.data.items.map((comment) => (
            <li
              key={comment.id}
              className="rounded-lg border border-civic bg-[var(--surface)] px-4 py-3"
            >
              <div className="flex items-baseline justify-between gap-2">
                <p className="text-sm font-medium text-civic-navy">
                  {comment.author_display_name}
                  {comment.is_official && (
                    <span className="ml-2 text-xs font-normal text-[var(--primary)]">
                      Official
                    </span>
                  )}
                </p>
                <time className="text-xs text-[var(--muted)]">
                  {new Date(comment.created_at).toLocaleString()}
                </time>
              </div>
              <p className="mt-1 text-sm text-[var(--foreground)]">{comment.body}</p>
            </li>
          ))}
        </ul>
      )}

      {isSignedIn ? (
        <form
          className="space-y-2"
          onSubmit={(event) => {
            event.preventDefault();
            postMutation.mutate();
          }}
        >
          <label className="block text-sm font-medium text-civic-navy">
            Add a comment
            <textarea
              value={body}
              onChange={(event) => setBody(event.target.value)}
              rows={3}
              placeholder="Share context about this issue…"
              className="mt-1 w-full rounded-lg border border-civic px-3 py-2 text-sm"
              disabled={unavailable}
            />
          </label>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={!body.trim() || postMutation.isPending || unavailable}
            className="rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
          >
            {postMutation.isPending ? "Posting…" : "Post comment"}
          </button>
        </form>
      ) : (
        <SignInButton mode="modal">
          <button
            type="button"
            className="rounded-lg border border-civic px-4 py-2 text-sm font-medium text-civic-navy"
          >
            Sign in to comment
          </button>
        </SignInButton>
      )}
    </section>
  );
}
