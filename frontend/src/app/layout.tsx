import { ClerkProvider } from "@clerk/nextjs";
import type { Metadata } from "next";

import { Providers } from "@/features/shared/providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "CivicSense — Civic issues for your city",
  description:
    "Browse public civic issues, explore the map, report problems, track accountability, and connect with your municipality.",
};

const clerkProxyUrl = process.env.NEXT_PUBLIC_CLERK_PROXY_URL?.trim() || undefined;

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
