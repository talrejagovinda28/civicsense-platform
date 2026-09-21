"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Show, SignInButton } from "@clerk/nextjs";

import { useCity } from "@/features/cities/city-context";

type NavItem = {
  href: string;
  label: string;
  match: (path: string) => boolean;
  requiresAuth?: boolean;
  requiresReporting?: boolean;
};

const NAV_ITEMS: NavItem[] = [
  {
    href: "/",
    label: "Feed",
    match: (path) => path === "/" || path.startsWith("/complaints/"),
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
    match: (path) => path === "/profile" || path.startsWith("/profile/"),
    requiresAuth: true,
  },
];

function NavLink({ item, active }: { item: NavItem; active: boolean }) {
  return (
    <Link
      href={item.href}
      className={`flex flex-1 flex-col items-center gap-0.5 px-1 py-2 text-xs font-medium transition ${
        active
          ? "text-[var(--primary)]"
          : "text-[var(--muted)] hover:text-civic-navy"
      }`}
      aria-current={active ? "page" : undefined}
    >
      <span className="text-base leading-none" aria-hidden>
        {item.label.charAt(0)}
      </span>
      <span>{item.label}</span>
    </Link>
  );
}

function SignInNavButton({ label }: { label: string }) {
  return (
    <SignInButton mode="modal">
      <button
        type="button"
        className="flex flex-1 flex-col items-center gap-0.5 px-1 py-2 text-xs font-medium text-[var(--muted)]"
      >
        <span className="text-base leading-none" aria-hidden>
          {label.charAt(0)}
        </span>
        <span>{label}</span>
      </button>
    </SignInButton>
  );
}

export function BottomNav() {
  const pathname = usePathname();
  const { isReportingEnabled } = useCity();

  const visibleItems = NAV_ITEMS.filter((item) => {
    if (item.requiresReporting && !isReportingEnabled) {
      return false;
    }
    return true;
  });

  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-50 border-t border-civic bg-[var(--surface)] shadow-civic-md md:hidden"
      aria-label="Primary"
    >
      <div className="mx-auto flex max-w-lg items-stretch justify-around">
        {visibleItems.map((item) => {
          const active = item.match(pathname);

          if (!item.requiresAuth) {
            return <NavLink key={item.href} item={item} active={active} />;
          }

          return (
            <span key={item.href} className="contents">
              <Show when="signed-in">
                <NavLink item={item} active={active} />
              </Show>
              <Show when="signed-out">
                <SignInNavButton label={item.label} />
              </Show>
            </span>
          );
        })}
      </div>
    </nav>
  );
}
