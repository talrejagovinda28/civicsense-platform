"use client";

import Link from "next/link";
import { Show, SignInButton, UserButton } from "@clerk/nextjs";

import { CitySelector } from "@/features/cities/city-selector";
import { useCity } from "@/features/cities/city-context";

type AppHeaderProps = {
  showCitySelector?: boolean;
};

export function AppHeader({ showCitySelector = true }: AppHeaderProps) {
  const { isReportingEnabled } = useCity();

  return (
    <header className="border-b border-civic bg-[var(--surface)] shadow-civic-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <div className="flex min-w-0 items-center gap-4">
          <Link href="/" className="shrink-0">
            <span className="text-lg font-bold tracking-tight text-civic-navy">
              CivicSense
            </span>
          </Link>
          {showCitySelector && <CitySelector />}
        </div>

        <nav className="flex items-center gap-2 sm:gap-3">
          <Link
            href="/complaints"
            className="hidden rounded-lg px-3 py-1.5 text-sm font-medium text-[var(--muted)] hover:bg-[var(--surface-muted)] hover:text-civic-navy sm:inline-block"
          >
            Feed
          </Link>

          <Show when="signed-in">
            {isReportingEnabled && (
              <Link
                href="/complaints/new/location"
                className="rounded-lg bg-[var(--primary)] px-3 py-1.5 text-sm font-medium text-white hover:bg-[var(--primary-hover)]"
              >
                Report Issue
              </Link>
            )}
            <Link
              href="/dashboard"
              className="hidden rounded-lg px-3 py-1.5 text-sm font-medium text-[var(--muted)] hover:bg-[var(--surface-muted)] hover:text-civic-navy sm:inline-block"
            >
              Dashboard
            </Link>
            <UserButton />
          </Show>

          <Show when="signed-out">
            <SignInButton mode="modal">
              <button className="rounded-lg bg-civic-navy px-3 py-1.5 text-sm font-medium text-white hover:bg-[var(--civic-navy-light)]">
                Sign in
              </button>
            </SignInButton>
          </Show>
        </nav>
      </div>
    </header>
  );
}
