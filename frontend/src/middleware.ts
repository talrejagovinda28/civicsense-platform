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

const clerkProxyUrl = process.env.NEXT_PUBLIC_CLERK_PROXY_URL?.trim() || "";

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

  const publicMetadata = sessionClaims.public_metadata as { role?: string } | undefined;
  if (publicMetadata?.role) {
    return publicMetadata.role;
  }

  const topLevelRole = sessionClaims.role;
  if (typeof topLevelRole === "string" && topLevelRole.trim()) {
    return topLevelRole.trim().toLowerCase();
  }

  return "citizen";
}

/**
 * Enable Clerk frontend API proxy only when an explicit proxy URL is configured
 * (production Vercel). Leaving it enabled without a working proxy causes
 * `host_invalid` on localhost / preview hosts.
 */
const middlewareOptions = clerkProxyUrl
  ? {
      frontendApiProxy: {
        enabled: true as const,
        // Clerk reads NEXT_PUBLIC_CLERK_PROXY_URL; keep proxy enabled only when set.
      },
    }
  : {};

export default clerkMiddleware(async (auth, req) => {
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
}, middlewareOptions);

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
    "/__clerk",
    "/__clerk/(.*)",
  ],
};
