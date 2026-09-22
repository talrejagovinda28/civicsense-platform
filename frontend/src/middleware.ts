import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const isProtectedRoute = createRouteMatcher([
  "/dashboard(.*)",
  "/complaints/new(.*)",
  "/officer(.*)",
  "/admin(.*)",
  "/chats(.*)",
  "/profile",
]);

const isOfficerRoute = createRouteMatcher(["/officer(.*)"]);
const isAdminRoute = createRouteMatcher(["/admin(.*)"]);

const configuredProxyUrl = process.env.NEXT_PUBLIC_CLERK_PROXY_URL?.trim() || "";

/**
 * Clerk @7 auto-enables Frontend API proxy on `*.vercel.app` when it thinks
 * production keys / proxy are in play. Preview hosts must never use `/__clerk`
 * — they should call the development Frontend API directly.
 *
 * Enable proxy only on Vercel Production, and only for the host named in
 * NEXT_PUBLIC_CLERK_PROXY_URL (preserves the working Production setup).
 */
function shouldEnableClerkFrontendProxy(requestUrl: URL): boolean {
  // Preview / staging / development deployments: never proxy.
  if (process.env.VERCEL_ENV && process.env.VERCEL_ENV !== "production") {
    return false;
  }
  if (!configuredProxyUrl) {
    return false;
  }
  if (/^https?:\/\//i.test(configuredProxyUrl)) {
    try {
      return requestUrl.hostname === new URL(configuredProxyUrl).hostname;
    } catch {
      return false;
    }
  }
  // Relative proxy path (e.g. /__clerk) — Production Vercel only.
  return process.env.VERCEL_ENV === "production";
}

function getRoleFromClaims(
  sessionClaims: Record<string, unknown> | null | undefined,
): string {
  if (!sessionClaims) {
    return "citizen";
  }

  const metadata = sessionClaims.metadata as { role?: string } | undefined;
  if (metadata?.role) {
    return metadata.role;
  }

  const publicMetadata = sessionClaims.public_metadata as
    | { role?: string }
    | undefined;
  if (publicMetadata?.role) {
    return publicMetadata.role;
  }

  const topLevelRole = sessionClaims.role;
  if (typeof topLevelRole === "string" && topLevelRole.trim()) {
    return topLevelRole.trim().toLowerCase();
  }

  return "citizen";
}

export default clerkMiddleware(
  async (auth, req) => {
    if (isProtectedRoute(req)) {
      await auth.protect();

      if (isOfficerRoute(req)) {
        const { sessionClaims } = await auth();
        const role = getRoleFromClaims(sessionClaims as Record<string, unknown>);

        if (role !== "officer" && role !== "admin") {
          return NextResponse.redirect(new URL("/dashboard", req.url));
        }
      }

      if (isAdminRoute(req)) {
        const { sessionClaims } = await auth();
        const role = getRoleFromClaims(sessionClaims as Record<string, unknown>);

        if (role !== "admin") {
          return NextResponse.redirect(new URL("/dashboard", req.url));
        }
      }
    }
  },
  {
    // Always pass an explicit enabled function so Clerk does not auto-enable
    // `/__clerk` on Preview `*.vercel.app` hosts.
    frontendApiProxy: {
      enabled: (url) => shouldEnableClerkFrontendProxy(url),
    },
  },
);

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
    // Keep matcher entries so Production proxy requests reach middleware when enabled.
    "/__clerk",
    "/__clerk/(.*)",
  ],
};
