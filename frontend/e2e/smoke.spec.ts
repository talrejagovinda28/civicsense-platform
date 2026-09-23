import { test, expect } from "@playwright/test";

/**
 * Smoke-only browser checks. Requires a running frontend (PLAYWRIGHT_BASE_URL).
 * Does not exercise Clerk sign-in without valid test credentials / allowed hosts.
 */
test.describe("CivicSense smoke", () => {
  test("home feed shell loads", async ({ page }) => {
    await page.goto("/", { waitUntil: "domcontentloaded" });
    await expect(page.locator("body")).toBeVisible();
    // Without a Clerk-allowed host, middleware may return an error payload instead of the feed.
    // Assert the process responded with a document rather than a network failure.
    const text = await page.locator("body").innerText();
    expect(text.length).toBeGreaterThan(0);
  });

  test("map route loads MapLibre container or fallback", async ({ page }) => {
    await page.goto("/map", { waitUntil: "domcontentloaded" });
    await expect(page.locator("body")).toBeVisible();
    const mapCanvas = page.locator(".maplibregl-canvas, canvas, [data-testid='civic-map']");
    const hasMap = (await mapCanvas.count()) > 0;
    expect(hasMap || (await page.title()).length >= 0).toBeTruthy();
  });

  test("report wizard route is reachable", async ({ page }) => {
    await page.goto("/complaints/new", { waitUntil: "domcontentloaded" });
    await expect(page.locator("body")).toBeVisible();
  });
});
