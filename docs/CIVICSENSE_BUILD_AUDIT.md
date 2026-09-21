# CivicSense India — Build Audit (Phase 00)

**Date:** 2026-09-22  
**Branch:** `feature/civicsense-accountability-social`  
**Pack:** `CivicSense_India_E2E_Cursor_Pack_2026-09-22`  
**Secrets:** Not inspected or reported — only variable **names** from `.env.example`.

## Repository factual state

| Item | Finding |
|------|---------|
| Git | Was on `main` @ `dd9d463`; branched to `feature/civicsense-accountability-social` |
| Alembic head | Single linear head `008` (001→008). No `009` yet. |
| Backend | FastAPI modular monolith; 14 migrated tables; `UserProfile` model exists **without** migration |
| Frontend | Next.js 15 App Router; MapLibre CSP wired; **map-first home** at `/` |
| Auth | Clerk JWT (`CLERK_JWKS_URL`, `CLERK_SECRET_KEY`, `NEXT_PUBLIC_CLERK_*`) |
| Media | Cloudinary signed uploads (`CLOUDINARY_*`) |
| Hosting | Vercel frontend + Railway backend; `railway.toml` starts uvicorn **only** — **no auto alembic** |
| Tests | No pytest suite; smoke scripts only |
| Maps | MapLibre + OSM raster; Google Maps removed |

## Env variable NAMES (from `.env.example`)

`DATABASE_URL`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, `CLERK_JWKS_URL`, `NEXT_PUBLIC_CLERK_PROXY_URL`, `NEXT_PUBLIC_CLERK_SIGN_IN_URL`, `NEXT_PUBLIC_CLERK_SIGN_UP_URL`, `NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL`, `NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL`, `NEXT_PUBLIC_API_URL`, `CORS_ORIGINS`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `CLOUDINARY_FOLDER`

## Compatibility map (existing → India pack)

| Pack capability | Existing | Action |
|-----------------|----------|--------|
| Complaints + status FSM | Yes | Extend columns; keep enum |
| Cities / wards / accountability | Yes (Pune) | Keep; research CSV as RESEARCH_ONLY |
| External handoff | `external_submissions` 3-state | Add intents/attempts/adapters; keep legacy table |
| MapLibre map | Yes | Move home→feed; map becomes `/map` tab |
| Social / DM / karma / groups | **Absent** | Additive migrations + APIs + UI |
| Resolution evidence | Status notes only | New tables + workflow |
| Moderation | Absent | New tables + admin queue |
| Live government channels | Disabled / guided only | Fake adapters + disabled-by-default registry |

## Deploy / migration warning

Railway start command does **not** run `alembic upgrade`. A previous or future pre-deploy hook that auto-applies Alembic against production must be reviewed by a human before merge. This build will **not** apply production migrations. Migration `009+` must be dry-run on an isolated DB first.

## Superseded V2 decisions (per pack)

Map-first homepage, Google Maps, and “no social” are superseded. Preserve working V2 accountability/map/wizard; extend additively.

## Phase 00 gate

`IMPLEMENTED AND TESTED` — audit complete; no secrets committed.
