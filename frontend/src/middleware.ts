import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const isProtectedRoute = createRouteMatcher([
  "/dashboard(.*)",
  "/complaints/new(.*)",
  "/officer(.*)",
  "/admin(.*)",
]);

const isOfficerRoute = createRouteMatcher(["/officer(.*)"]);
const isAdminRoute = createRouteMatcher(["/admin(.*)"]);

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

  return "citizen";
}

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
});

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
