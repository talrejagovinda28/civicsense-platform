"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AppShell } from "@/features/shell/app-shell";
import {
  createDirectChat,
  followProfile,
  getPublicProfile,
  getReputation,
  unfollowProfile,
} from "@/lib/api";

type PublicProfileViewProps = {
  handle: string;
};

export function PublicProfileView({ handle }: PublicProfileViewProps) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const queryClient = useQueryClient();
  const router = useRouter();
  const [followError, setFollowError] = useState<string | null>(null);
  const [messageError, setMessageError] = useState<string | null>(null);

  const profileQuery = useQuery({
    queryKey: ["profile", handle],
    queryFn: async () => {
      const token = isSignedIn ? await getToken() : null;
      return getPublicProfile(handle, token);
    },
    enabled: isLoaded,
  });

  const reputationQuery = useQuery({
    queryKey: ["reputation-me"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) {
        return null;
      }
      return getReputation(token);
    },
    enabled: isLoaded && isSignedIn,
  });

  const messageMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      const profile = profileQuery.data;
      const recipientId = profile?.messaging_user_id;
      if (!token || !recipientId) {
        throw new Error("Messaging is not available for this profile.");
      }
      const result = await createDirectChat(token, recipientId);
      if (!result.ok) {
        throw new Error(result.error);
      }
      return result.data!;
    },
    onSuccess: (data) => {
      setMessageError(null);
      if (data.conversation_id) {
        router.push(`/chats/${data.conversation_id}`);
      } else if (data.request_id) {
        setMessageError("Message request sent — waiting for acceptance.");
      }
    },
    onError: (error) => {
      setMessageError(error instanceof Error ? error.message : "Could not start chat.");
    },
  });

  const followMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      const profile = profileQuery.data;
      if (!token || !profile) {
        throw new Error("Sign in to follow.");
      }
      const result = profile.viewer_is_following
        ? await unfollowProfile(token, profile.id)
        : await followProfile(token, profile.id);
      if (!result.ok) {
        throw new Error(result.error);
      }
      return result.data;
    },
    onSuccess: () => {
      setFollowError(null);
      void queryClient.invalidateQueries({ queryKey: ["profile", handle] });
    },
    onError: (error) => {
      setFollowError(error instanceof Error ? error.message : "Follow action failed.");
    },
  });

  const unavailable = profileQuery.data === null && !profileQuery.isLoading;

  return (
    <AppShell>
      <div className="space-y-6">
        <Link href="/" className="text-sm text-[var(--muted)] hover:text-civic-navy">
          ← Back to feed
        </Link>

        {profileQuery.isLoading && (
          <p className="text-sm text-[var(--muted)]">Loading profile…</p>
        )}

        {unavailable && (
          <p className="rounded-lg border border-civic bg-[var(--surface-muted)] px-4 py-3 text-sm text-[var(--muted)]">
            Profile not found or the profiles API is not deployed yet.
          </p>
        )}

        {profileQuery.data && (
          <section className="rounded-xl border border-civic bg-[var(--surface)] p-5 shadow-civic-sm">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="text-2xl font-bold text-civic-navy">
                  {profileQuery.data.display_name}
                </h1>
                <p className="text-sm text-[var(--muted)]">@{profileQuery.data.handle}</p>
                {profileQuery.data.is_private && (
                  <p className="mt-2 text-xs text-[var(--muted)]">Private account</p>
                )}
              </div>
              {isSignedIn && (
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => followMutation.mutate()}
                    disabled={followMutation.isPending}
                    className="rounded-lg border border-civic px-4 py-2 text-sm font-medium text-civic-navy disabled:opacity-40"
                  >
                    {profileQuery.data.viewer_is_following
                      ? "Unfollow"
                      : profileQuery.data.viewer_follow_pending
                        ? "Requested"
                        : "Follow"}
                  </button>
                  {profileQuery.data.messaging_user_id &&
                    reputationQuery.data?.unlocks.can_initiate_dm && (
                      <button
                        type="button"
                        onClick={() => messageMutation.mutate()}
                        disabled={messageMutation.isPending}
                        className="rounded-lg bg-civic-navy px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
                      >
                        {messageMutation.isPending ? "Opening…" : "Message"}
                      </button>
                    )}
                </div>
              )}
            </div>

            {profileQuery.data.bio && (
              <p className="mt-4 text-sm">{profileQuery.data.bio}</p>
            )}

            <dl className="mt-6 flex gap-6 text-sm">
              <div>
                <dt className="text-[var(--muted)]">Followers</dt>
                <dd className="font-semibold text-civic-navy">
                  {profileQuery.data.follower_count}
                </dd>
              </div>
              <div>
                <dt className="text-[var(--muted)]">Following</dt>
                <dd className="font-semibold text-civic-navy">
                  {profileQuery.data.following_count}
                </dd>
              </div>
            </dl>

            {followError && <p className="mt-3 text-sm text-red-600">{followError}</p>}
            {messageError && <p className="mt-3 text-sm text-amber-700">{messageError}</p>}
          </section>
        )}
      </div>
    </AppShell>
  );
}
