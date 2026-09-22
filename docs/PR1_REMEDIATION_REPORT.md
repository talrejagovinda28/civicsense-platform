# PR #1 Remediation Report

**Branch:** `feature/civicsense-accountability-social`  
**PR:** https://github.com/talrejagovinda28/civicsense-platform/pull/1  
**Date:** 2026-09-23  
**Scope:** V3 security + UI integration (confidential reporting, unverified refs, resolution authz, guided channels), verification

---

## Defects identified and fixed

### SEC-1 — Public fake government registration
**Severity:** Critical  
**Files:** `submission_engine.py`, `adapters/registry.py`, `schemas/submission.py`, `routers/submissions.py`, `core/config.py`  
**Fix:**
- Removed `test_scenario` from citizen-facing `DispatchRequest` (`extra="forbid"`).
- Fake adapters only when `ENVIRONMENT in {test,development}` **and** `CIVICSENSE_ALLOW_FAKE_ADAPTERS=true` **and** channel `TEST_ONLY`.
- DISABLED channels never dispatch.
- Fake “official” outcomes map to `simulated_registered` + `reference_type=simulated_test_reference`, never real government registration language.
- Live outbound remains unimplemented / gated by `EXTERNAL_DISPATCH_GLOBAL_ENABLED=false`.

### SEC-2 — Sensitive / confidential complaint exposure
**Severity:** Critical  
**Files:** `services/access.py`, `routers/complaints.py`, `services/feed.py`, `models/complaint_image.py`, create schemas  
**Fix:**
- Create accepts `is_sensitive` and `anonymous_to_public`; sensitive images stored `visibility=private`.
- Public listing/feed/map exclude `is_sensitive`.
- Detail GET returns **404** (not 403) for unauthorized viewers.
- Case access helper for owner / admin / scoped officers.
- Owners and officer/admin retain access.

### SEC-3 — Resolution role spoofing + evidence gate
**Severity:** Critical  
**Files:** `services/resolution.py`, schemas/routers  
**Fix:**
- Removed client `submitter_role`; derive from Clerk JWT role only.
- Independent review requires officer/admin **and** prior resolution evidence.
- Reporter confirm → `confirmed_by_reporter` (not independently verified).
- Evidence XP only after accepted review.

### SEC-4 — Citizen government references unverified
**Severity:** High  
**Files:** `submission_engine.py`, submission UI  
**Fix:**
- Citizen `attach_reference` stores `user_provided_unverified`.
- Admin/officer verify path required before trusted labeling.
- UI labels references as unverified pending review.

### SEC-5 — Guided channel activation
**Severity:** High  
**Files:** `adapters/registry.py`, `submission_engine.py`  
**Fix:**
- Guided channels require `enabled` **and** activation mode `MANUAL` or `LIVE_APPROVED`.
- DISABLED / inactive guided channels cannot dispatch.

### SEC-6 — Idempotency cross-user leak
**Severity:** High  
**Files:** `submission_engine.py`  
**Fix:** Existing idempotency key returned only after ownership/consent checks; otherwise 409. No blind retry of `UNKNOWN_OUTCOME`.

### API-1 — Feed / engagement / social / timeline contracts
**Severity:** High (broken UX)  
**Files:** feed/social/profiles/messaging, `frontend/src/lib/api.ts`, timeline service/router  
**Fix:**
- Feed items include required `complaint_id`, counts, locality, kind.
- Engagement endpoints aligned; comments paginated.
- Complaint timeline GET for owners/officers.
- Frontend: submission consent/dispatch card, resolution panel, confidential wizard flags.

### FE-1 — Hooks / TypeScript build blockers
**Severity:** High  
**Files:** `resolution-panel.tsx`, `official-submission-card.tsx`  
**Fix:**
- All `useMutation` hooks run unconditionally before early return.
- Metadata `instructions` narrowed before render (`unknown` → string check).

---

## Tests added

| File | Coverage |
|------|----------|
| `test_no_public_fake_registration.py` | Production blocks fake dispatch; schema rejects `test_scenario` |
| `test_idempotency_authz.py` | Cross-user idempotency key replay denied |
| `test_resolution_role_spoof.py` | Citizen cannot independent-review; body role spoof rejected |
| `test_sensitive_privacy.py` | Anonymous/other citizen blocked; owner allowed |
| `test_confidential_create_and_privacy.py` | Sensitive create + private images + feed exclusion |
| `test_guided_disabled_channel.py` | Disabled guided channel cannot dispatch |
| `test_resolution_requires_evidence.py` | Officer cannot verify without evidence |
| `test_user_reference_unverified.py` | Citizen refs marked unverified |
| `test_feed_contract.py` | `complaint_id` present; sensitive excluded |
| `test_engagement_contract.py` | Like/unlike/engagement counts shape |
| `frontend/e2e/smoke.spec.ts` | Playwright smoke (home/map/wizard) |

---

## Verification results

| Check | Result |
|-------|--------|
| `py -m pytest -q` | **35 passed** |
| `npm run lint` | **pass** |
| `npm run build` | **pass** |
| Isolated PostgreSQL `008→009` | **VERIFIED** on local disposable DB `civicsense_mig_test` (PostgreSQL 16.15 @ 127.0.0.1) — not Supabase/production |
| Playwright browser E2E | **3/3 smoke passed** earlier (home/map/wizard shell). Signed-in journey **UNVERIFIED**. Clerk proxy now disabled unless `NEXT_PUBLIC_CLERK_PROXY_URL` is set (fixes local `host_invalid`). |
| Production backup | **NOT VERIFIED** — interactive scripts prepared under `Desktop\CivicSense-Private-Backups`; user must run dump + verify before merge |
| Production migration | **NOT RUN** (hard boundary) |
| Live government dispatch | **NOT ENABLED** |

---

## Remaining limitations / release gates

1. Confirm Railway does **not** auto-apply Alembic on deploy without reviewed backup.
2. Playwright smoke needs a running frontend + Chromium; Clerk-authenticated journey remains manual.
3. Fix Clerk JWKS /session token issues on Railway (`/me` 401) if still present.
4. Keep `EXTERNAL_DISPATCH_GLOBAL_ENABLED=false` and `CIVICSENSE_ALLOW_FAKE_ADAPTERS=false` in production.
5. Ward jurisdiction mappings and live agency channels remain research/disabled.
6. Drop disposable local DB `civicsense_mig_test` after review (agent host only).

---

## Deployment readiness checklist (do NOT merge until)

- [ ] Human review of this PR diff
- [x] Isolated Postgres migration proof (`008→009` on disposable local DB)
- [ ] Production env flags confirmed false for outbound/fake
- [ ] Clerk production JWT verification smoke
- [ ] Manual smoke: feed, map, report wizard, like/comment, profile privacy
- [ ] Explicit decision: still **no** live government dispatch

**Status:** CODE-READY for continued PR review — V3 security/UI defects above are fixed and unit-tested. Isolated migration verified. Not PRODUCT-LAUNCH-READY for on-behalf filing.
