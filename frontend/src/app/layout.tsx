import { ClerkProvider } from "@clerk/nextjs";
import type { Metadata } from "next";

import { Providers } from "@/features/shared/providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "CivicSense — Civic issues map for your city",
  description:
    "Explore public civic issues on an interactive map. Report problems, track accountability, and connect with your municipality.",
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
