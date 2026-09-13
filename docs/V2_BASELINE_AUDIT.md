# CivicSense V2 — Baseline Repository Audit (Slice 0)

**Date:** 14 September 2026  
**Branch:** `feature/civicsense-v2`  
**Purpose:** Document the pre-V2 state before implementation.

---

## Repository layout

Monorepo at `civicsense_platform/` with `frontend/` (Next.js 15) and `backend/` (FastAPI).

V2 specification pack lives in `docs/v2/` (copied from repo `v2/` pack).

---

## Stack versions (current)

| Layer | Version |
|-------|---------|
| Next.js | ^15.3.0 |
| React | ^19.0.0 |
| @clerk/nextjs | ^7.6.0 |
| @react-google-maps/api | ^2.20.6 |
| TanStack Query | ^5.67.0 |
| Tailwind CSS | ^4.0.0 |
| FastAPI | >=0.115.0 |
| SQLAlchemy | >=2.0.36 |
| Alembic | 001–004 applied |
| Python | 3.12 |

**Not yet present:** shadcn/ui, React Hook Form, Zod (blueprint mentions them for V2).

---

## Frontend routes

| Route | Purpose |
|-------|---------|
| `/` | Landing / home |
| `/sign-in`, `/sign-up` | Clerk auth |
| `/dashboard` | User dashboard |
| `/complaints` | Public feed |
| `/complaints/[id]` | Complaint detail |
| `/complaints/new/*` | 5-step wizard |
| `/officer` | Officer queue |
| `/admin` | Admin stats + roles |

---

## Backend API (`/api/v1`)

| Method | Path | Notes |
|--------|------|-------|
| GET | `/health` | DB connectivity |
| GET | `/users/me` | Current user + role |
| GET | `/categories` | 7 Pune categories |
| GET/POST | `/complaints/*` | CRUD + officer queue + status |
| POST | `/uploads/cloudinary-signature` | Signed uploads |
| GET/PATCH | `/admin/*` | Stats + role updates |

---

## Database tables

- `categories`, `complaints`, `complaint_images`, `complaint_status_history`, `user_profiles`
- Migration 004 made `latitude`, `longitude`, `google_place_id` nullable (manual address fallback)

---

## Maps & auth

- **Maps:** `@react-google-maps/api` in `map-picker.tsx`; manual address fallback when API key missing
- **Auth:** Clerk middleware with role gates; `frontendApiProxy` enabled for Vercel
- **Images:** Cloudinary signed uploads via backend

---

## Deployment

- Frontend: Vercel (`output: standalone`)
- Backend: Railway (Dockerfile.backend)
- DB: Supabase PostgreSQL
- No `vercel.json`; env vars documented in `.env.example`

---

## Blueprint conflicts / gaps

| Gap | V2 requirement | Current state |
|-----|----------------|---------------|
| Multi-city | City config model + selector | Hardcoded `city: "Pune"` string on complaints |
| Ward map | 41 electoral ward polygons | No ward geometry or resolver |
| Accountability | Departments, officials, routing | Not implemented |
| Map-first home | Ward map + complaint pins | Form-centric landing page |
| shadcn/ui | Design system | Plain Tailwind only |
| Governance model | Separate electoral/admin/department/routing | Single `ward` text field on complaint |
| Privacy | Public approximate location | Role-based detail hiding exists; no ward-level public coords policy |

---

## V2 attachment points

| Slice | Primary files |
|-------|----------------|
| 1 Cities | `backend/app/models/city.py`, `routers/cities.py`, migration 005 |
| 2–3 Wards | `backend/app/data/cities/pune/`, `services/jurisdiction.py` |
| 4–5 Accountability | New models + `services/accountability.py` |
| 6+ Frontend | `features/cities/`, `features/map/`, redesign `home-view.tsx` |

---

## Baseline checks

Run before V2 changes (adapt if npm/py unavailable locally):

```powershell
Set-Location frontend; npm install; npm run lint; npm run build
Set-Location ../backend; py -m compileall app; py -m alembic current
```

---

## Risks

1. Clerk 7.x Core 3 removed `SignedIn`/`SignedOut` — already migrated to `Show`.
2. Production migration 004 must run on Supabase before manual-address complaints persist.
3. Pune ward GeoJSON requires external download (OpenCity) — do not fabricate.
4. No automated test suite — add focused pytest for jurisdiction/accountability in slices 3–5.
