import { ClerkProvider } from "@clerk/nextjs";
import type { Metadata } from "next";

import { Providers } from "@/features/shared/providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "CivicSense — Civic issues for your city",
  description:
    "Browse public civic issues, explore the map, report problems, track accountability, and connect with your municipality.",
};

/**
 * Production-only Clerk FAPI proxy. Preview must omit proxyUrl so ClerkJS talks
 * to the development Frontend API (*.clerk.accounts.dev), not /__clerk on the
 * preview host (which yields host_invalid).
 */
function resolveClerkProxyUrl(): string | undefined {
  if (process.env.VERCEL_ENV && process.env.VERCEL_ENV !== "production") {
    return undefined;
  }
  const configured = process.env.NEXT_PUBLIC_CLERK_PROXY_URL?.trim();
  return configured || undefined;
}

const clerkProxyUrl = resolveClerkProxyUrl();

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider {...(clerkProxyUrl ? { proxyUrl: clerkProxyUrl } : {})}>
      <html lang="en">
        <body>
          <Providers>{children}</Providers>
        </body>
      </html>
    </ClerkProvider>
  );
}
