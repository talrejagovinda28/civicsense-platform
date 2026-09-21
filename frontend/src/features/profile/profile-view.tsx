"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { AppShell } from "@/features/shell/app-shell";
import { getOwnProfile, getReputation, updateOwnProfile } from "@/lib/api";

export function ProfileView() {
  const { getToken, isLoaded } = useAuth();
  const queryClient = useQueryClient();
  const [saveError, setSaveError] = useState<string | null>(null);

  const profileQuery = useQuery({
    queryKey: ["profile-me"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) {
        return null;
      }
      return getOwnProfile(token);
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
    enabled: isLoaded,
  });

  const privacyMutation = useMutation({
    mutationFn: async (isPrivate: boolean) => {
      const token = await getToken();
      if (!token) {
        throw new Error("Not signed in.");
      }
      const result = await updateOwnProfile(token, { is_private: isPrivate });
      if (!result.ok) {
        throw new Error(result.error);
      }
      return result.data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["profile-me"], data);
      setSaveError(null);
    },
    onError: (error) => {
      setSaveError(error instanceof Error ? error.message : "Could not update profile.");
    },
  });

  const profileUnavailable = profileQuery.data === null && !profileQuery.isLoading;
  const reputation = reputationQuery.data;

  return (
    <AppShell>
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-civic-navy">Your profile</h1>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Manage privacy and view your civic reputation.
          </p>
        </div>

        {profileQuery.isLoading && (
          <p className="text-sm text-[var(--muted)]">Loading profile…</p>
        )}

        {profileUnavailable && (
          <p className="rounded-lg border border-civic bg-[var(--surface-muted)] px-4 py-3 text-sm text-[var(--muted)]">
            Profile API is not available yet. Privacy and reputation settings will appear
            when the backend is deployed.
          </p>
        )}

        {profileQuery.data && (
          <section className="rounded-xl border border-civic bg-[var(--surface)] p-5 shadow-civic-sm">
            <h2 className="font-semibold text-civic-navy">{profileQuery.data.display_name}</h2>
            <p className="text-sm text-[var(--muted)]">@{profileQuery.data.handle}</p>
            {profileQuery.data.bio && (
              <p className="mt-3 text-sm">{profileQuery.data.bio}</p>
            )}

            <label className="mt-6 flex items-center gap-3">
              <input
                type="checkbox"
                checked={profileQuery.data.is_private}
                disabled={privacyMutation.isPending}
                onChange={(event) => privacyMutation.mutate(event.target.checked)}
                className="h-4 w-4 rounded border-civic"
              />
              <span className="text-sm">
                Private account — hide profile from non-followers
              </span>
            </label>
            {saveError && <p className="mt-2 text-sm text-red-600">{saveError}</p>}
          </section>
        )}

        <section className="rounded-xl border border-civic bg-[var(--surface)] p-5 shadow-civic-sm">
          <h2 className="font-semibold text-civic-navy">Reputation</h2>
          {reputationQuery.isLoading && (
            <p className="mt-2 text-sm text-[var(--muted)]">Loading reputation…</p>
          )}
          {!reputationQuery.isLoading && !reputation && (
            <p className="mt-2 text-sm text-[var(--muted)]">
              Reputation data is not available yet.
            </p>
          )}
          {reputation && (
            <div className="mt-4 space-y-4">
              <div className="flex gap-6">
                <div>
                  <p className="text-2xl font-bold text-[var(--primary)]">
                    {reputation.lifetime_xp}
                  </p>
                  <p className="text-xs text-[var(--muted)]">Lifetime XP</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-civic-navy">
                    {reputation.eligible_xp}
                  </p>
                  <p className="text-xs text-[var(--muted)]">Eligible XP</p>
                </div>
              </div>

              {reputation.badges.length > 0 && (
                <ul className="flex flex-wrap gap-2">
                  {reputation.badges.map((badge) => (
                    <li
                      key={badge.code}
                      className="rounded-full bg-[var(--primary-muted)] px-3 py-1 text-xs font-medium text-civic-navy"
                    >
                      {badge.label}
                    </li>
                  ))}
                </ul>
              )}

              <ul className="space-y-1 text-sm text-[var(--muted)]">
                <li>
                  {reputation.unlocks.can_initiate_dm
                    ? "✓ Can initiate direct messages (200+ XP)"
                    : "○ Direct messages unlock at 200 eligible XP"}
                </li>
                <li>
                  {reputation.unlocks.can_create_groups
                    ? "✓ Can create groups (500+ XP)"
                    : "○ Group creation unlocks at 500 eligible XP"}
                </li>
              </ul>
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}
