/** Shared Clerk FAPI proxy gating for middleware + ClerkProvider. */

export function getConfiguredClerkProxyUrl(): string {
  return process.env.NEXT_PUBLIC_CLERK_PROXY_URL?.trim() || "";
}

/**
 * Preview / non-production Vercel must never use `/__clerk`.
 * Production enables proxy only when NEXT_PUBLIC_CLERK_PROXY_URL is set,
 * and (for absolute URLs) only on the configured hostname.
 */
export function shouldEnableClerkFrontendProxy(requestUrl?: URL): boolean {
  if (process.env.VERCEL_ENV && process.env.VERCEL_ENV !== "production") {
    return false;
  }

  const configured = getConfiguredClerkProxyUrl();
  if (!configured) {
    return false;
  }

  if (/^https?:\/\//i.test(configured)) {
    try {
      const configuredHost = new URL(configured).hostname;
      if (requestUrl) {
        return requestUrl.hostname === configuredHost;
      }
      // SSR/ClerkProvider: only expose proxyUrl on Vercel Production builds.
      return process.env.VERCEL_ENV === "production";
    } catch {
      return false;
    }
  }

  // Relative proxy path — Production Vercel only.
  return process.env.VERCEL_ENV === "production";
}

export function resolveClerkProxyUrlForProvider(): string | undefined {
  if (!shouldEnableClerkFrontendProxy()) {
    return undefined;
  }
  return getConfiguredClerkProxyUrl() || undefined;
}
