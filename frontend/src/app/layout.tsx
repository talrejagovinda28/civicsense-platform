import { ClerkProvider } from "@clerk/nextjs";
import type { Metadata } from "next";

import { Providers } from "@/features/shared/providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "CivicSense — Civic issues for your city",
  description:
    "Browse public civic issues, explore the map, report problems, track accountability, and connect with your municipality.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body>
          <Providers>{children}</Providers>
        </body>
      </html>
    </ClerkProvider>
  );
}
