import { test, expect, type Page, type Request, type Response } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const PREVIEW_URL =
  process.env.PLAYWRIGHT_BASE_URL ??
  "https://civicsense-platform-one4rme16-govi4.vercel.app";

const OUT_DIR =
  process.env.PLAYWRIGHT_ARTIFACT_DIR ??
  path.join(
    process.env.USERPROFILE ?? ".",
    "Desktop",
    "CivicSense-Private-Backups",
    "preview-verify",
  );

type NetHit = { url: string; status: number; bodySnippet?: string };

async function collectPageSignals(page: Page, routePath: string) {
  const clerkProxyHits: string[] = [];
  const hostInvalid: NetHit[] = [];
  const http5xx: NetHit[] = [];

  const onRequest = (req: Request) => {
    const u = req.url();
    if (u.includes("/__clerk")) {
      clerkProxyHits.push(u);
    }
  };

  const onResponse = async (res: Response) => {
    const u = res.url();
    const status = res.status();
    if (status >= 500) {
      http5xx.push({ url: u, status });
    }
    if (u.includes("/__clerk") || u.includes("clerk")) {
      try {
        const text = await res.text();
        if (text.includes("host_invalid") || text.includes("Invalid host")) {
          hostInvalid.push({
            url: u,
            status,
            bodySnippet: text.slice(0, 200),
          });
        }
      } catch {
        // ignore binary / unavailable bodies
      }
    }
  };

  page.on("request", onRequest);
  page.on("response", onResponse);

  const response = await page.goto(`${PREVIEW_URL}${routePath}`, {
    waitUntil: "domcontentloaded",
    timeout: 60_000,
  });
  await page.waitForTimeout(4000);

  const bodyText = await page.locator("body").innerText().catch(() => "");
  const html = await page.content();

  page.off("request", onRequest);
  page.off("response", onResponse);

  return {
    finalUrl: page.url(),
    navStatus: response?.status() ?? 0,
    blockedByVercelSso:
      page.url().includes("vercel.com/login") ||
      bodyText.includes("Log in to Vercel"),
    bodyHasHostInvalid:
      bodyText.includes("host_invalid") ||
      bodyText.includes("Invalid host") ||
      html.includes("host_invalid"),
    bodyHasMiddlewareFail: html.includes("MIDDLEWARE_INVOCATION_FAILED"),
    clerkProxyHits,
    hostInvalid,
    http5xx,
    bodyPreview: bodyText.slice(0, 400),
  };
}

test.describe("Vercel Preview verification", () => {
  test.beforeAll(() => {
    fs.mkdirSync(OUT_DIR, { recursive: true });
  });

  test("homepage: no 500, no host_invalid, no /__clerk", async ({ page }) => {
    const signals = await collectPageSignals(page, "/");
    await page.screenshot({
      path: path.join(OUT_DIR, "home.png"),
      fullPage: true,
    });
    fs.writeFileSync(
      path.join(OUT_DIR, "home-signals.json"),
      JSON.stringify(signals, null, 2),
    );

    expect(signals.navStatus, "homepage HTTP status").toBeLessThan(500);
    expect(signals.navStatus).not.toBe(500);
    expect(
      signals.blockedByVercelSso,
      "Preview is behind Vercel Deployment Protection (SSO). Provide VERCEL_AUTOMATION_BYPASS_SECRET or disable Preview SSO temporarily.",
    ).toBeFalsy();
    expect(signals.bodyHasHostInvalid, "homepage host_invalid").toBeFalsy();
    expect(signals.bodyHasMiddlewareFail, "middleware failure").toBeFalsy();
    expect(
      signals.clerkProxyHits,
      `unexpected /__clerk requests: ${signals.clerkProxyHits.join("\n")}`,
    ).toEqual([]);
    expect(signals.hostInvalid, "Clerk host_invalid responses").toEqual([]);
    expect(
      signals.http5xx.filter((h) => !h.url.includes("analytics")),
      `5xx responses: ${JSON.stringify(signals.http5xx)}`,
    ).toEqual([]);
  });

  test("dashboard route shell loads without proxy errors", async ({ page }) => {
    const signals = await collectPageSignals(page, "/dashboard");
    await page.screenshot({
      path: path.join(OUT_DIR, "dashboard.png"),
      fullPage: true,
    });
    fs.writeFileSync(
      path.join(OUT_DIR, "dashboard-signals.json"),
      JSON.stringify(signals, null, 2),
    );

    expect(signals.navStatus).toBeLessThan(500);
    expect(signals.bodyHasHostInvalid).toBeFalsy();
    expect(signals.clerkProxyHits).toEqual([]);
    expect(signals.hostInvalid).toEqual([]);
  });

  test("complaints/new route shell loads without proxy errors", async ({
    page,
  }) => {
    const signals = await collectPageSignals(page, "/complaints/new");
    await page.screenshot({
      path: path.join(OUT_DIR, "complaints-new.png"),
      fullPage: true,
    });
    fs.writeFileSync(
      path.join(OUT_DIR, "complaints-new-signals.json"),
      JSON.stringify(signals, null, 2),
    );

    expect(signals.navStatus).toBeLessThan(500);
    expect(signals.bodyHasHostInvalid).toBeFalsy();
    expect(signals.clerkProxyHits).toEqual([]);
    expect(signals.hostInvalid).toEqual([]);
  });

  test("signed-in dashboard + report wizard when E2E creds present", async ({
    page,
  }) => {
    const user = process.env.E2E_CLERK_USER?.trim();
    const password = process.env.E2E_CLERK_PASSWORD?.trim();
    test.skip(
      !user || !password,
      "E2E_CLERK_USER / E2E_CLERK_PASSWORD not set — signed-in journey UNVERIFIED",
    );

    await page.goto(`${PREVIEW_URL}/sign-in`, {
      waitUntil: "domcontentloaded",
      timeout: 60_000,
    });
    await page.waitForTimeout(2000);

    // Clerk hosted components vary; try common identifiers.
    const email = page
      .locator('input[name="identifier"], input[type="email"], input[name="emailAddress"]')
      .first();
    await email.waitFor({ timeout: 30_000 });
    await email.fill(user!);

    const continueBtn = page.getByRole("button", {
      name: /continue|sign in|next/i,
    });
    if (await continueBtn.count()) {
      await continueBtn.first().click();
    }

    const passwordInput = page.locator('input[type="password"]').first();
    await passwordInput.waitFor({ timeout: 30_000 });
    await passwordInput.fill(password!);
    await page.getByRole("button", { name: /continue|sign in/i }).first().click();

    await page.waitForURL(/dashboard|complaints|map|\//, { timeout: 60_000 });
    await page.screenshot({
      path: path.join(OUT_DIR, "signed-in-home.png"),
      fullPage: true,
    });

    await page.goto(`${PREVIEW_URL}/dashboard`, {
      waitUntil: "domcontentloaded",
    });
    await page.waitForTimeout(3000);
    await page.screenshot({
      path: path.join(OUT_DIR, "signed-in-dashboard.png"),
      fullPage: true,
    });
    await expect(page.locator("body")).toBeVisible();
    const dashHtml = await page.content();
    expect(dashHtml.includes("host_invalid")).toBeFalsy();

    await page.goto(`${PREVIEW_URL}/complaints/new`, {
      waitUntil: "domcontentloaded",
    });
    await page.waitForTimeout(3000);
    await page.screenshot({
      path: path.join(OUT_DIR, "signed-in-complaints-new.png"),
      fullPage: true,
    });
    const wizardHtml = await page.content();
    expect(wizardHtml.includes("host_invalid")).toBeFalsy();
    expect(wizardHtml.includes("MIDDLEWARE_INVOCATION_FAILED")).toBeFalsy();
  });
});
