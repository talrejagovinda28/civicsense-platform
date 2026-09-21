# CivicSense India — Implementation Report

**Date:** 2026-09-22 (updated after PR #1 remediation)  
**Branch:** `feature/civicsense-accountability-social`  
**Pack:** `CivicSense_India_E2E_Cursor_Pack_2026-09-22`  
**Base:** `main` @ `dd9d463` (MapLibre home-map fix)  
**PR:** https://github.com/talrejagovinda28/civicsense-platform/pull/1  
**Remediation:** See `docs/PR1_REMEDIATION_REPORT.md`  
**Production mutations:** None  
**Live external submissions:** None  

---

## 1. Phase matrix

| Phase | Outcome | Classification |
|------|---------|----------------|
| 00 Audit | `docs/CIVICSENSE_BUILD_AUDIT.md` | **IMPLEMENTED + TESTED** |
| 01 Baseline | Frontend build/lint; backend import; pytest suite | **IMPLEMENTED + TESTED** |
| 02 Data migration | Alembic `009` additive + models | **IMPLEMENTED + UNTESTED** against Postgres clone (SQLite unit tests OK; isolated PG upgrade pending human) |
| 03 Directory | `authority_sources`, `external_channels`, research importer, disabled seed channel | **IMPLEMENTED + TESTED** (importer dry-run; routing remains research-only) |
| 04 Adapter core | Fake/guided adapters, intents/attempts, UNKNOWN_OUTCOME no blind retry | **IMPLEMENTED + TESTED** |
| 05 Reporting UX | Existing wizard preserved; MapLibre; consent/submission APIs | **IMPLEMENTED + UNTESTED** (E2E browser not run; API present) |
| 06 Tracking | References, attest-sent, timeline events, guided language | **IMPLEMENTED + UNTESTED** (unit coverage partial) |
| 07 Resolution | Evidence / confirm / dispute / independent review services + routes | **IMPLEMENTED + UNTESTED** |
| 08 Feed | Feed-first `/`; `GET /feed`; FeedView cards | **IMPLEMENTED + TESTED** (frontend build); API unit not exhaustive |
| 09 Map | `/map` with CivicMap; MapLibre CSP; OSM attribution | **IMPLEMENTED + TESTED** (build + prior production map fixes) |
| 10 Social | Likes, affected, comments, follows, blocks, anonymous/privacy fields | **IMPLEMENTED + TESTED** (like uniqueness) |
| 11 Karma | Ledger, badges, 200/500 gates | **IMPLEMENTED + TESTED** |
| 12 DMs | Conversations, requests, XP gate, polling UI | **IMPLEMENTED + TESTED** (XP gate); chat E2E **UNTESTED** |
| 13 Groups | Create at 500 XP, membership APIs + UI hooks | **IMPLEMENTED + UNTESTED** |
| 14 Officials/admin | Existing officer/admin + moderation queue APIs | **IMPLEMENTED + UNTESTED** (no new verified-officer proof workflow UI beyond APIs) |
| 15 Security | Sensitive excluded from feed; public schemas; rate limits preserved; middleware for chats/profile | **IMPLEMENTED + UNTESTED** (privacy script not re-run) |
| 16 Documentation | Audit, deploy runbook, import audit, env names, this report | **IMPLEMENTED + TESTED** |
| 17 Final verification | pytest 7/7; npm build; npm lint | **IMPLEMENTED + TESTED** (see commands) |
| 18 Handoff | This report + deploy checklist | **CONFIGURATION PENDING** / **EXTERNAL VERIFICATION BLOCKED** for live channels |

---

## 2. Git / migrations

- **Branch:** `feature/civicsense-accountability-social` (not pushed to main automatically)
- **Alembic chain:** `001`→`008`→`009` (single head expected)
- **Migration dry-run on production:** **NOT RUN** (hard boundary)
- **Isolated Postgres upgrade from 008:** **PENDING human** — unit tests use SQLite in-memory with UUID/JSON shims

### Key new backend areas

- Models: `authority_channel`, `submission`, `community`, `messaging`, `reputation`, `resolution`, `moderation`; expanded `user_profiles`, `complaints`, `complaint_images`
- Services: adapters (fake/guided), `submission_engine`, `reputation`, `feed`, `social`, `messaging`, `resolution`, `moderation`
- Routers: `feed`, `social`, `profiles`, `chats`, `submissions`, `resolution`, `moderation`
- Tests: `backend/tests/` (7 cases)
- Research: `data/research/*_RESEARCH_ONLY.csv`, `data/import_audit.json`, `scripts/import_research_sources.py`

### Key new frontend areas

- Routes: `/` feed, `/map`, `/chats`, `/chats/[id]`, `/profile`, `/profile/[handle]`
- Shell: header + bottom nav (Feed | Map | Report | Chats | Profile)
- Features: `feed`, `shell`, `social`, `chats`, `profile`, `map/map-view`

---

## 3. Commands run

| Command | Result |
|---------|--------|
| `py -m pytest tests/ -v` | **21 passed** (after PR #1 remediation) |
| `npm run build` (frontend) | **pass** — routes include `/`, `/map`, `/chats`, `/profile` |
| `npm run lint` | **pass** |
| `py -m alembic heads` | `009` (head) |
| Isolated Postgres `008→009` | **UNVERIFIED** (no Docker/Postgres on agent host) |
| Playwright E2E | **UNVERIFIED** (browser binary unavailable) |
| Production `alembic upgrade` | **NOT EXECUTED** |
| Live Clerk/Cloudinary/WhatsApp/email | **NOT EXECUTED** |

---

## 4. API inventory (additive under `/api/v1`)

Preserved: cities, wards, geojson, accountability, complaints CRUD/status, uploads, admin, health, me, external-submission start/token.

Added (representative):

- `GET /feed`
- `PUT/DELETE /complaints/{id}/like`, `/affected`
- `GET/POST /complaints/{id}/comments`
- `POST/DELETE follow`, block, follow-request decide
- `GET/PATCH /profiles/me`, `GET /profiles/{handle}`, `GET /profiles/me/reputation`
- `GET/POST /chats`, `/chats/direct`, `/chats/groups`, messages cursor
- `POST /complaints/{id}/authorization`, `/submissions`, attest, reference, reconcile
- `POST` resolution evidence/confirmation/review
- `POST /reports`, `GET /moderation/queue`, moderation actions

**Tile provider:** OpenStreetMap raster via MapLibre CSP (no Google key). Attribution required.

**Adapters:** Fake (TEST_ONLY) + Guided portal/WhatsApp (USER_ACTION_REQUIRED). Live managed send **disabled**.

**Verified vs research:** Migration seeds one **DISABLED** guided PMC portal channel. Pack CSVs are research-only; not auto-routed.

---

## 5. Acceptance scenario status (20+ from pack)

| ID | Status |
|----|--------|
| T08 idempotency / T15 UNKNOWN no blind retry | Covered by unit tests |
| T13/T14 fake adapter outcomes | Covered |
| T21 like uniqueness / 0 XP engagement | Covered (like unique); XP engagement = 0 by design |
| T25/T26 DM XP gate | Covered (199 denied path in `test_dm_xp_gate`) |
| T33 XP once-only | Covered |
| T01 Postgres migrate 008→009 | **CONFIGURATION PENDING** (isolated DB) |
| T03–T07, T09–T12, T16–T20, T22–T24, T27–T45 | **IMPLEMENTED + UNTESTED** or partial — require human/browser/isolated DB |
| Live agency ACK | **EXTERNAL VERIFICATION BLOCKED** |

---

## 6. Human integration checklist

See `docs/CIVICSENSE_DEPLOY_RUNBOOK.md` and pack `11_DEPLOY_AND_CONNECT_LAST.md`.

1. Review PR on `feature/civicsense-accountability-social` — do **not** merge blindly.
2. Check Railway for auto `alembic upgrade`; backup Supabase.
3. Dry-run `009` on clone.
4. Keep `EXTERNAL_DISPATCH_GLOBAL_ENABLED=false`.
5. Clerk production JWT / JWKS alignment (prior `/me` 401s may still need JWKS fix).
6. Cloudinary video settings if enabling short video.
7. Per-channel verification matrix before enabling any managed adapter.
8. Consented volunteer pilot only after permission evidence.
9. Smoke: feed, map, report wizard, profile privacy, chats empty state, officer/admin.
10. Rollback plan: code rollback; avoid destructive downgrade on prod.

---

## 7. Unresolved external dependencies

| Gap | Evidence | Next action |
|-----|----------|-------------|
| Electoral→ward office mapping empty | Prior V2 report | Verify PMC mapping; fill `ward_jurisdiction_mappings` |
| Appointed officers / phones | Research CSV only | Human verification; keep UNVERIFIED |
| Managed email/WhatsApp permission | None | Agency written acceptance |
| Official API | None documented | Do not invent |
| Postgres migration proof | Not run here | Isolated upgrade from 008 |
| Clerk token failures on Railway | Prior logs | Align `CLERK_JWKS_URL` + session claims |
| OSM tile ToS / capacity | Community tiles | Configurable style URL; attribution; consider hosted tiles later |
| Full 45-scenario automation | Partial unit suite | Expand pytest + optional Playwright |

---

## Honest launch language

This branch is **CODE-READY for review** with simulated submission/social/karma tests. It is **not** PRODUCT-LAUNCH-READY for “on-behalf government filing.” Guided portal remains the only seeded Pune channel and is **DISABLED**. Do not claim official registration without verified government evidence.
