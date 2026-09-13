"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { useCity } from "@/features/cities/city-context";
import { AppHeader } from "@/features/shared/app-header";
import { StatusCard } from "@/features/shared/status-card";
import { getAdminStats, STATUS_LABELS, updateUserRole } from "@/lib/api";

export function AdminDashboardView() {
  const { getToken, isLoaded } = useAuth();
  const { selectedCity } = useCity();
  const queryClient = useQueryClient();
  const [userId, setUserId] = useState("");
  const [role, setRole] = useState<"citizen" | "officer" | "admin">("citizen");
  const [roleError, setRoleError] = useState<string | null>(null);
  const [roleSuccess, setRoleSuccess] = useState<string | null>(null);

  const statsQuery = useQuery({
    queryKey: ["admin-stats"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) {
        throw new Error("Not authenticated");
      }
      return getAdminStats(token);
    },
    enabled: isLoaded,
  });

  const roleMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      if (!token || !userId.trim()) {
        throw new Error("User ID is required.");
      }
      return updateUserRole(token, userId.trim(), { role });
    },
    onSuccess: (data) => {
      setRoleSuccess(`Updated ${data.user_id} to ${data.role}.`);
      setRoleError(null);
      setUserId("");
      queryClient.invalidateQueries({ queryKey: ["admin-stats"] });
    },
    onError: (error) => {
      setRoleSuccess(null);
      setRoleError(error instanceof Error ? error.message : "Role update failed.");
    },
  });

  const statusRows =
    statsQuery.data?.by_status.map((item) => ({
      label: STATUS_LABELS[item.label] ?? item.label,
      value: String(item.count),
    })) ?? [];

  const categoryRows =
    statsQuery.data?.by_category.map((item) => ({
      label: item.label,
      value: String(item.count),
    })) ?? [];

  const statsCity = statsQuery.data?.city ?? selectedCity?.name ?? "Pune";

  return (
    <>
      <AppHeader />
      <main className="mx-auto min-h-screen max-w-4xl px-6 py-12">
        <div>
          <Link href="/dashboard" className="text-sm text-[var(--muted)] hover:text-civic-navy">
            ← Dashboard
          </Link>
          <h1 className="mt-2 text-2xl font-bold text-civic-navy">Admin Dashboard</h1>
          <p className="mt-1 text-[var(--muted)]">
            {statsCity} complaint overview and user role management.
          </p>
        </div>

        {statsQuery.isLoading && (
          <p className="mt-8 text-sm text-[var(--muted)]">Loading stats…</p>
        )}

        {statsQuery.error && (
          <p className="mt-8 text-sm text-red-600">
            Could not load admin stats. Ensure your Clerk role is admin.
          </p>
        )}

        {statsQuery.data && (
          <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <StatusCard
              title="Total Complaints"
              rows={[
                { label: "City", value: statsCity },
                { label: "Total", value: String(statsQuery.data.total) },
              ]}
            />
            <StatusCard title="By Status" rows={statusRows} />
            <StatusCard title="By Category" rows={categoryRows} />
          </section>
        )}

        <section className="mt-10 rounded-xl border border-civic bg-[var(--surface-muted)] p-5">
          <h2 className="font-semibold text-civic-navy">Manage User Roles</h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Set a Clerk user&apos;s <code className="text-xs">public_metadata.role</code>.
            Find user IDs in the Clerk dashboard.
          </p>

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <label className="block text-sm font-medium sm:col-span-2">
              Clerk User ID
              <input
                type="text"
                value={userId}
                onChange={(event) => setUserId(event.target.value)}
                placeholder="user_2abc..."
                className="mt-1 w-full rounded-lg border border-civic px-3 py-2 text-sm"
              />
            </label>

            <label className="block text-sm font-medium">
              Role
              <select
                value={role}
                onChange={(event) =>
                  setRole(event.target.value as "citizen" | "officer" | "admin")
                }
                className="mt-1 w-full rounded-lg border border-civic px-3 py-2 text-sm"
              >
                <option value="citizen">Citizen</option>
                <option value="officer">Officer</option>
                <option value="admin">Admin</option>
              </select>
            </label>

            <div className="flex items-end">
              <button
                type="button"
                disabled={!userId.trim() || roleMutation.isPending}
                onClick={() => roleMutation.mutate()}
                className="rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
              >
                {roleMutation.isPending ? "Saving…" : "Update Role"}
              </button>
            </div>
          </div>

          {roleError && <p className="mt-3 text-sm text-red-600">{roleError}</p>}
          {roleSuccess && <p className="mt-3 text-sm text-green-700">{roleSuccess}</p>}
        </section>

        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/officer"
            className="rounded-lg border border-civic px-4 py-2 text-sm font-medium"
          >
            Officer Queue
          </Link>
          <Link
            href="/complaints"
            className="rounded-lg border border-civic px-4 py-2 text-sm font-medium"
          >
            Public Feed
          </Link>
          <Link
            href="/"
            className="rounded-lg border border-civic px-4 py-2 text-sm font-medium"
          >
            City Map
          </Link>
        </div>
      </main>
    </>
  );
}
