"use client";

import { useAuth, UserButton } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { StatusCard } from "@/features/shared/status-card";
import { apiFetch, HealthResponse, UserResponse } from "@/lib/api";

export function DashboardView() {
  const { getToken, isLoaded } = useAuth();

  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const token = await getToken();
      return apiFetch<HealthResponse>("/api/v1/health", token);
    },
    enabled: isLoaded,
  });

  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const token = await getToken();
      return apiFetch<UserResponse>("/api/v1/me", token);
    },
    enabled: isLoaded,
  });

  return (
    <main className="mx-auto min-h-screen max-w-3xl px-6 py-12">
      <div className="flex items-center justify-between">
        <div>
          <Link href="/" className="text-sm text-neutral-500 hover:text-neutral-700">
            ← Home
          </Link>
          <h1 className="mt-2 text-2xl font-bold">Dashboard</h1>
          <p className="mt-1 text-neutral-600">
            Protected route — Clerk auth + FastAPI verified.
          </p>
        </div>
        <UserButton />
      </div>

      <div className="mt-8 flex flex-wrap gap-3">
        <Link
          href="/complaints/new"
          className="inline-flex rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white"
        >
          Raise Complaint
        </Link>
        {(meQuery.data?.role === "officer" || meQuery.data?.role === "admin") && (
          <Link
            href="/officer"
            className="inline-flex rounded-lg border border-neutral-300 px-4 py-2 text-sm font-medium"
          >
            Officer Dashboard
          </Link>
        )}
        {meQuery.data?.role === "admin" && (
          <Link
            href="/admin"
            className="inline-flex rounded-lg border border-neutral-300 px-4 py-2 text-sm font-medium"
          >
            Admin Dashboard
          </Link>
        )}
      </div>

      <section className="mt-10 grid gap-4 sm:grid-cols-2">
        <StatusCard
          title="API Health"
          loading={healthQuery.isLoading}
          error={healthQuery.error?.message}
          rows={
            healthQuery.data
              ? [
                  { label: "Status", value: healthQuery.data.status },
                  { label: "Database", value: healthQuery.data.database },
                ]
              : []
          }
        />
        <StatusCard
          title="Current User"
          loading={meQuery.isLoading}
          error={meQuery.error?.message}
          rows={
            meQuery.data
              ? [
                  { label: "User ID", value: meQuery.data.user_id },
                  { label: "Role", value: meQuery.data.role },
                ]
              : []
          }
        />
      </section>
    </main>
  );
}
