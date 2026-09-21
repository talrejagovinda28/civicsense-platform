"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Show, SignInButton, UserButton } from "@clerk/nextjs";

import { CitySelector } from "@/features/cities/city-selector";
import { useCity } from "@/features/cities/city-context";

type AppHeaderProps = {
  showCitySelector?: boolean;
};

type NavLinkConfig = {
  href: string;
  label: string;
  match: (path: string) => boolean;
  requiresAuth?: boolean;
  requiresReporting?: boolean;
  primary?: boolean;
};

const NAV_LINKS: NavLinkConfig[] = [
  {
    href: "/",
    label: "Feed",
    match: (path) => path === "/",
  },
  {
    href: "/map",
    label: "Map",
    match: (path) => path === "/map",
  },
  {
    href: "/complaints/new/location",
    label: "Report",
    match: (path) => path.startsWith("/complaints/new"),
    requiresAuth: true,
    requiresReporting: true,
    primary: true,
  },
  {
    href: "/chats",
    label: "Chats",
    match: (path) => path.startsWith("/chats"),
    requiresAuth: true,
  },
  {
    href: "/profile",
    label: "Profile",
    match: (path) => path === "/profile",
    requiresAuth: true,
  },
];

function HeaderNavLink({ link, active }: { link: NavLinkConfig; active: boolean }) {
  if (link.primary) {
    return (
      <Link
        href={link.href}
        className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
          active
            ? "bg-[var(--primary-hover)] text-white"
            : "bg-[var(--primary)] text-white hover:bg-[var(--primary-hover)]"
        }`}
        aria-current={active ? "page" : undefined}
      >
        {link.label}
      </Link>
    );
  }

  return (
    <Link
      href={link.href}
      className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${
        active
          ? "bg-[var(--primary-muted)] text-civic-navy"
          : "text-[var(--muted)] hover:bg-[var(--surface-muted)] hover:text-civic-navy"
      }`}
      aria-current={active ? "page" : undefined}
    >
      {link.label}
    </Link>
  );
}

export function AppHeader({ showCitySelector = true }: AppHeaderProps) {
  const pathname = usePathname();
  const { isReportingEnabled } = useCity();

  const visibleLinks = NAV_LINKS.filter((link) => {
    if (link.requiresReporting && !isReportingEnabled) {
      return false;
    }
    return true;
  });

  return (
    <header className="relative z-50 border-b border-civic bg-[var(--surface)] shadow-civic-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <div className="flex min-w-0 items-center gap-4">
          <Link href="/" className="shrink-0">
            <span className="text-lg font-bold tracking-tight text-civic-navy">
              CivicSense
            </span>
          </Link>
          {showCitySelector && <CitySelector />}
        </div>

        <nav className="hidden items-center gap-1 sm:flex md:gap-2" aria-label="Primary">
          {visibleLinks.map((link) => {
            const active = link.match(pathname);

            if (link.requiresAuth) {
              return (
                <Show key={link.href} when="signed-in">
                  <HeaderNavLink link={link} active={active} />
                </Show>
              );
            }

            return <HeaderNavLink key={link.href} link={link} active={active} />;
          })}

          <Show when="signed-in">
            <Link
              href="/dashboard"
              className="rounded-lg px-3 py-1.5 text-sm font-medium text-[var(--muted)] hover:bg-[var(--surface-muted)] hover:text-civic-navy"
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

        <div className="flex items-center gap-2 sm:hidden">
          <Show when="signed-in">
            <UserButton />
          </Show>
          <Show when="signed-out">
            <SignInButton mode="modal">
              <button className="rounded-lg bg-civic-navy px-3 py-1.5 text-sm font-medium text-white">
                Sign in
              </button>
            </SignInButton>
          </Show>
        </div>
      </div>
    </header>
  );
}
