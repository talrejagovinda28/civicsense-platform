# CivicSense V2 — Completion Report

**Branch:** `feature/civicsense-v2`  
**Date:** 2026-09-14  
**Status:** V2 implementation complete — ready for review, migration, and deploy

---

## Executive summary

CivicSense V2 transforms the MVP into a map-first, multi-city civic accountability platform. Pune is fully functional with electoral ward boundaries, complaint pins, jurisdiction resolution, “Who is responsible?” accountability, and PMC official handoff tracking. Five additional cities appear as preview/coming-soon in the city selector.

All slices (0–15) from `docs/v2/CivicSense_V2_Cursor_Execution_Plan.md` are implemented on branch `feature/civicsense-v2`.

---

## Slice completion

| Slice | Scope | Status |
|-------|-------|--------|
| 0 | Baseline audit | ✅ `docs/V2_BASELINE_AUDIT.md` |
| 1 | Multi-city model + seed | ✅ Migration `005`, cities API |
| 2 | Pune ward GeoJSON package | ✅ 41 features validated |
| 3 | Electoral wards + jurisdiction resolver | ✅ Migration `006`, ward APIs |
| 4 | Ward offices + 2026 representatives | ✅ Migration `007`, 15 offices, 165 reps |
| 5 | Departments, routing, accountability API | ✅ Migration `007`, `/accountability` |
| 6 | V2 design + app shell + city selector | ✅ Tokens, header, city context |
| 7 | Pune ward map + preview cities | ✅ `CivicMap`, preview overlay |
| 8 | Complaint pins + clustering | ✅ `@googlemaps/markerclusterer` |
| 9 | Complaint wizard V2 + server jurisdiction | ✅ Server-side FK resolution |
| 10 | “Who is responsible?” UX | ✅ `AccountabilityCard` in wizard + detail |
| 11 | Official handoff UX | ✅ `OfficialHandoffCard`, external submissions |
| 12 | Complaint detail V2 | ✅ Accountability sidebar, privacy redaction |
| 13 | Officer/Admin upgrades | ✅ City-aware dashboards, V2 styling |
| 14 | QA / privacy / data quality | ✅ Privacy notice, audit scripts |
| 15 | Production readiness | ✅ This report + manual steps below |

---

## Database migrations (004–008)

| Revision | Purpose |
|----------|---------|
| `004` | Nullable complaint lat/lng/google_place_id (manual maps fallback) |
| `005` | `cities` table + Pune active + 5 preview cities |
| `006` | `electoral_wards` + Pune 41 ward seed from GeoJSON |
| `007` | Ward offices, departments, routing channels, 2026 reps, jurisdiction mapping table |
| `008` | Complaint jurisdiction FKs, public coords, `external_submissions` |

**Important:** Migrations 004–008 have **not** been applied to production. Apply them manually after review.

---

## Key backend additions

- **Models:** `WardOffice`, `PublicOfficial`, `OfficialJurisdiction`, `CategoryRoutingRule`, `RoutingChannel`, `WardJurisdictionMapping`, `ExternalSubmission`
- **Services:** `jurisdiction.py`, `accountability.py`, `external_submissions.py`
- **APIs:**
  - `GET /api/v1/cities` — city list with status
  - `GET /api/v1/cities/{slug}/wards/geojson` — ward boundaries
  - `GET /api/v1/cities/{slug}/wards/resolve?lat=&lng=` — point-in-polygon ward lookup
  - `GET /api/v1/cities/{slug}/accountability?lat=&lng=&category_id=` — full accountability payload
  - `GET /api/v1/complaints?city=&status=&category_id=` — filtered public feed with `public_latitude/longitude`
  - `POST/PATCH /api/v1/complaints/{id}/external-submission/*` — PMC handoff tracking

---

## Key frontend additions

- `features/cities/` — city context + selector
- `features/map/` — ward map, complaint markers with clustering, issue panel
- `features/accountability/` — “Who is responsible?” card
- `features/routing/` — PMC official handoff card
- `features/shared/app-header.tsx` — V2 header with city selector
- Map-first home (`home-view.tsx`), V2 globals.css design tokens
- Complaint wizard privacy notice on location step
- Post-submit redirect to complaint detail page

---

## Privacy model

| Data | Public feed / anonymous detail | Owner / officer / admin |
|------|-------------------------------|-------------------------|
| Exact address | Hidden | Visible |
| Exact lat/lng | Hidden | Visible |
| Public lat/lng | Rounded to 3 decimals | Visible |
| Status history notes | Hidden | Visible |
| User ID | Hidden | Visible (owner/officer) |

Validation scripts:
- `backend/scripts/audit_public_api_privacy.py`
- `backend/scripts/validate_city_data.py`
- `backend/scripts/validate_pune_ward_geojson.py`

---

## Known limitations (documented, not blockers)

1. **Electoral → administrative ward office mapping** — `ward_jurisdiction_mappings` table is empty pending verified PMC mapping data. Accountability API shows a warning when ward office cannot be resolved.
2. **Google OAuth** — Requires Clerk Dashboard + Google Cloud Console configuration (not a code change).
3. **npm not available in local agent environment** — Frontend build must be verified locally or on Vercel CI.
4. **Cloudinary EXIF stripping** — Relies on Cloudinary upload settings; no custom image pipeline added.
5. **Automated pytest suite** — Not added; validation scripts cover data/privacy checks.

---

## Environment variables

### Vercel (frontend)

| Variable | Required | Notes |
|----------|----------|-------|
| `NEXT_PUBLIC_API_URL` | Yes | Railway backend URL |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Yes | Clerk |
| `CLERK_SECRET_KEY` | Yes | Clerk |
| `NEXT_PUBLIC_CLERK_PROXY_URL` | Yes | `https://civicsense-platform.vercel.app/__clerk/` |
| `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` | Optional | Map + wizard pin; manual address fallback without it |

### Railway (backend)

| Variable | Required |
|----------|----------|
| `DATABASE_URL` | Yes |
| `CLERK_JWKS_URL` or Clerk issuer config | Yes |
| `CLOUDINARY_*` | Yes (for uploads) |
| `CORS_ORIGINS` | Yes — include Vercel domain |

---

## Manual commands you must run

Run these **after merging** `feature/civicsense-v2` and **before** relying on V2 in production.

### 1. Backend — apply migrations (production Supabase)

```powershell
Set-Location "C:\Users\govindat\Desktop\PROJECTS FOR LEARNING\Pune Civilian App\civicsense_platform\backend"

# Ensure DATABASE_URL points at your Supabase production database
# Review migration files 004–008 before running

py -m alembic upgrade head
```

### 2. Validate civic data (against migrated DB)

```powershell
Set-Location "C:\Users\govindat\Desktop\PROJECTS FOR LEARNING\Pune Civilian App\civicsense_platform\backend"

py scripts/validate_pune_ward_geojson.py
py scripts/audit_public_api_privacy.py
py scripts/validate_city_data.py
```

Expected: 41 wards, 15 ward offices, 165 representatives, 6 active categories routed.

### 3. Frontend — install and build

```powershell
Set-Location "C:\Users\govindat\Desktop\PROJECTS FOR LEARNING\Pune Civilian App\civicsense_platform\frontend"

npm install
npm run build
npm run lint
```

### 4. Deploy

```powershell
# Push branch and open PR, or merge to main
git push -u origin feature/civicsense-v2

# After merge — Vercel auto-deploys frontend; Railway auto-deploys backend
# Verify both services picked up the new commit
```

### 5. Post-deploy smoke test

1. Open `https://civicsense-platform.vercel.app` — Pune map loads (or fallback message if no Maps key)
2. City selector — switch to Mumbai → preview overlay, no reporting
3. Switch back to Pune → ward polygons + complaint pins
4. Sign in → Report Issue → complete wizard → accountability preview on review step
5. Submit → lands on complaint detail with handoff card
6. Anonymous view of same complaint — no exact address/coords
7. Officer dashboard — queue loads for Pune
8. `GET {API}/api/v1/health` — healthy

### 6. Clerk (if not done)

- Enable Google OAuth provider with valid Google Cloud `client_id` / `client_secret`
- Set proxy URL: `https://civicsense-platform.vercel.app/__clerk/`
- Add Vercel domain to allowed origins

---

## Git

Recommended merge path:

```powershell
Set-Location "C:\Users\govindat\Desktop\PROJECTS FOR LEARNING\Pune Civilian App\civicsense_platform"
git checkout feature/civicsense-v2
git pull
# Review diff, then merge to main via PR
```

---

## Files changed (summary)

- **Backend:** 8 migrations, 6 new models, 3 services, accountability router, complaint jurisdiction + handoff endpoints
- **Frontend:** map-first home, city selector, accountability/handoff UI, wizard V2, officer/admin styling
- **Data:** Pune electoral GeoJSON, 2026 election CSV, source manifests
- **Docs:** V2 pack, baseline audit, this completion report

---

*Generated as part of CivicSense V2 Slice 15 — production readiness.*
