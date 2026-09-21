# PR #1 Remediation Report

**Branch:** `feature/civicsense-accountability-social`  
**PR:** https://github.com/talrejagovinda28/civicsense-platform/pull/1  
**Date:** 2026-09-22  
**Scope:** Security hardening, API contract alignment, expanded automated tests  

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

### SEC-2 — Sensitive complaint exposure
**Severity:** Critical  
**Files:** `services/access.py`, `routers/complaints.py`, `routers/social.py`, `services/social.py`, `services/feed.py`  
**Fix:**
- Public listing/feed exclude `is_sensitive`.
- Detail GET returns **404** (not 403) for unauthorized viewers.
- Like/affected/comments gated via `assert_complaint_socially_visible`.
- Owners and officer/admin retain access.

### SEC-3 — Resolution role spoofing
**Severity:** Critical  
**Files:** `services/resolution.py`, `schemas/resolution.py`, `routers/resolution.py`  
**Fix:**
- Removed client `submitter_role`; derive from Clerk JWT role only.
- Independent review requires officer/admin.
- Reporter confirm → `confirmed_by_reporter` (not independently verified).
- Evidence XP only after accepted review; resolution XP to complaint owner once via `resolution_verified:{id}`.

### SEC-4 — Idempotency cross-user leak
**Severity:** High  
**Files:** `submission_engine.py`  
**Fix:** Existing idempotency key is returned only after verifying complaint ownership and consent ownership; otherwise 409 without leaking peer intent details. No blind retry of `UNKNOWN_OUTCOME`.

### API-1 — Feed / engagement / social contracts
**Severity:** High (broken UX)  
**Files:** feed schemas/service, social schemas/router, profiles, messaging, `frontend/src/lib/api.ts`  
**Fix:**
- Feed items include required `complaint_id`, counts, `image_url`, locality, kind `complaint|update`.
- Added `GET /complaints/{id}/engagement`.
- Like/affected PUT/DELETE return `EngagementCounts` (200).
- Comments return paginated `{items,total,skip,limit}` with author display fields.
- Profiles/reputation/chats aligned to frontend TypeScript types.
- `apiFetchOptional` handles HTTP 204 / empty bodies safely.

---

## Tests added

| File | Coverage |
|------|----------|
| `test_no_public_fake_registration.py` | Production blocks fake dispatch; schema rejects `test_scenario` |
| `test_idempotency_authz.py` | Cross-user idempotency key replay denied |
| `test_resolution_role_spoof.py` | Citizen cannot independent-review; body role spoof rejected |
| `test_sensitive_privacy.py` | Anonymous/other citizen blocked; owner allowed |
| `test_feed_contract.py` | `complaint_id` present; sensitive excluded; owner list |
| `test_engagement_contract.py` | Like/unlike/engagement counts shape |

---

## Verification results

| Check | Result |
|-------|--------|
| `py -m pytest tests/ -v` | **21 passed** |
| `npm run lint` | **pass** |
| `npm run build` | **pass** (see build log) |
| Isolated PostgreSQL `008→009` | **UNVERIFIED** — Docker/local Postgres not available on agent host |
| Playwright browser E2E | **UNVERIFIED** — Chromium download previously timed out / not installed |
| Production migration | **NOT RUN** (hard boundary) |
| Live government dispatch | **NOT ENABLED** |

---

## Remaining limitations / release gates

1. Run `alembic upgrade head` on an **isolated** Postgres clone from revision `008` before merge.
2. Confirm Railway does **not** auto-apply Alembic on deploy without reviewed backup.
3. Install Playwright browsers and run full sign-in → report → feed → social journey.
4. Fix Clerk JWKS /session token issues observed historically on Railway (`/me` 401) if still present.
5. Keep `EXTERNAL_DISPATCH_GLOBAL_ENABLED=false` and `CIVICSENSE_ALLOW_FAKE_ADAPTERS=false` in production.
6. Ward jurisdiction mappings and live agency channels remain research/disabled.

---

## Deployment readiness checklist (do NOT merge until)

- [ ] Human review of this PR diff
- [ ] Isolated Postgres migration proof attached
- [ ] Production env flags confirmed false for outbound/fake
- [ ] Clerk production JWT verification smoke
- [ ] Manual smoke: feed, map, report wizard, like/comment, profile privacy
- [ ] Explicit decision: still **no** live government dispatch

**Status:** CODE-READY for continued PR review — security and contract defects above are fixed and unit-tested. Not PRODUCT-LAUNCH-READY for on-behalf filing.
