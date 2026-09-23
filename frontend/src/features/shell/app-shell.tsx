"use client";

import { AppHeader } from "@/features/shared/app-header";

import { BottomNav } from "./bottom-nav";

type AppShellProps = {
  children: React.ReactNode;
  variant?: "default" | "immersive";
  contentClassName?: string;
};

export function AppShell({
  children,
  variant = "default",
  contentClassName,
}: AppShellProps) {
  if (variant === "immersive") {
    return (
      <div className="flex h-[100dvh] flex-col overflow-hidden">
        <AppHeader />
        <div className="relative min-h-0 flex-1 pb-14 md:pb-0">{children}</div>
        <BottomNav />
      </div>
    );
  }

  return (
    <div className="flex min-h-[100dvh] flex-col">
      <AppHeader />
      <main
        className={`mx-auto w-full flex-1 px-4 py-6 pb-20 sm:px-6 md:pb-8 ${contentClassName ?? "max-w-3xl"}`}
      >
        {children}
      </main>
      <BottomNav />
    </div>
  );
}
