# CivicSense V2 — Cursor Execution Plan

**Purpose:** Step-by-step implementation plan for Cursor.  
**Companion specification:** `CivicSense_V2_Product_Data_Technical_Blueprint.md`  
**Rule:** Implement one slice, verify it, commit it, then move to the next slice.

---

# 0. How Cursor must work on this project

## 0.1 Operating rules

Cursor must follow these rules on every slice:

1. **Inspect before editing.** Read the relevant existing files and current migration history first.
2. **Preserve the deployed stack.** No provider migrations.
3. **Do not rewrite working features just to match a preferred architecture.** Refactor only when required by the slice.
4. **Use mature libraries where they genuinely reduce code.**
5. **No speculative abstractions.** Build for Pune + clean city configuration, not “millions of cities.”
6. **No microservices.**
7. **No mock government facts in production code.** Placeholder UI must be labelled preview/coming soon.
8. **Source all government/public data.** Data files and seed rows need provenance.
9. **Do not make direct undocumented PMC API calls in production.**
10. **Do not do the next slice early.** Stop after acceptance criteria are satisfied.
11. Run the repo's existing formatter/linter/build commands after every slice.
12. For DB changes, create a proper Alembic migration; do not manually mutate production DB.
13. Show the user:
   - files changed;
   - commands run;
   - verification results;
   - any unresolved risk;
   - suggested commit message.

## 0.2 “Do not overengineer” test

Before adding a dependency/file/layer, Cursor should ask internally:

> Can the current framework/library already do this cleanly?

If yes, use what exists.

## 0.3 Branch strategy

Create one feature branch for the redesign:

```powershell
# from repository root
git checkout -b feature/civicsense-v2
```

If the branch already exists, use it rather than creating variants.

Commit after every completed slice.

---

# 1. End-state slice map

| Slice | Outcome | User-visible? |
|---|---|---|
| 0 | Baseline audit + branch + no code churn | No |
| 1 | City model/config + Pune active + preview cities | Small |
| 2 | Pune 41-ward GeoJSON data package + validation | No |
| 3 | Ward GeoJSON API + backend jurisdiction resolver | No |
| 4 | 2026 elected representatives + 15 ward offices + provenance | No |
| 5 | Departments + routing rules + accountability API | No |
| 6 | V2 design tokens + app shell + city selector | **Yes** |
| 7 | Pune ward map + polygons + preview-city map behavior | **Yes** |
| 8 | Complaint pins + marker clustering + map/feed synchronization | **Yes** |
| 9 | Complaint wizard visual redesign + server jurisdiction | **Yes** |
| 10 | “Who is responsible?” UI | **Yes** |
| 11 | Official PMC handoff + external token capture | **Yes** |
| 12 | Complaint detail/timeline redesign | **Yes** |
| 13 | Officer/admin compatibility + light V2 visual alignment | Yes |
| 14 | Privacy/accessibility/performance QA | Yes |
| 15 | Production migration + deploy + smoke test | **Live** |

Do not collapse all slices into one PR.

---

# Slice 0 — Baseline repository audit

## Goal

Understand exactly what is deployed today and create a safe implementation baseline. No feature changes.

## Cursor tasks

1. Inspect root repository tree.
2. Inspect:
   - frontend `package.json`;
   - frontend app/routes/features/components;
   - current Google Maps integration;
   - current Clerk middleware/config;
   - API client;
   - complaint wizard;
   - complaint feed/detail;
   - backend requirements;
   - backend routers/models/schemas/services;
   - Alembic migrations;
   - deployment Dockerfiles/config;
   - `docs/BACKLOG.md` and complaint docs.
3. Identify current versions of:
   - Next.js;
   - Clerk packages;
   - Google Maps loader/wrapper;
   - SQLAlchemy/Alembic;
   - FastAPI/Pydantic.
4. Confirm current production env-variable names **without printing secret values**.
5. Run current baseline checks.

Suggested commands; adapt to actual repo:

```powershell
# frontend
Set-Location frontend
npm install
npm run lint
npm run build

# backend
Set-Location ../backend
py -m compileall app
py -m alembic current
```

If tests already exist, run them. Do not add a new testing framework in this slice.

## Deliverable

Create/update:

`docs/V2_BASELINE_AUDIT.md`

Include:
- actual repo structure;
- current routes/endpoints;
- models/tables;
- deployment entrypoints;
- current maps/auth implementation;
- any discrepancy with the V2 blueprint.

## Acceptance criteria

- No functional behavior changed.
- Current frontend still builds.
- Backend imports/starts or existing health check remains sound.
- Cursor can state exactly where V2 code should attach.

## Ready-to-paste Cursor prompt

```text
We are starting CivicSense V2. Read docs/CivicSense_V2_Product_Data_Technical_Blueprint.md and docs/CivicSense_V2_Cursor_Execution_Plan.md fully first.

Do Slice 0 only: baseline repository audit.

Inspect the actual repository, current migrations, frontend routes/features, current Google Maps implementation, Clerk middleware/config, complaint flow, API client, backend routers/models/schemas/services, Docker/deployment files, and env variable names. Do not print secrets.

Create docs/V2_BASELINE_AUDIT.md summarizing the real current state and any conflicts with the blueprint.

Run the existing frontend lint/build and available backend checks/tests. Do not add features and do not refactor unrelated code.

Stop after Slice 0 and show:
1. files changed,
2. commands/results,
3. architecture conflicts/risks,
4. proposed commit message.
```

## Suggested commit

`docs: audit current app before CivicSense V2`

---

# Slice 1 — Multi-city data model and seed configuration

## Goal

Introduce city as a first-class concept without changing the existing complaint UI yet.

Pune becomes `active`; other initial cities become `preview`.

## Database changes

Add a `cities` model/table using current UUID/timestamp conventions.

Recommended fields:

- `id`
- `slug` unique
- `name`
- `state_name`
- `state_code` nullable
- `country_code` default `IN`
- `status` (`active`, `preview`, `disabled`)
- `municipality_name` nullable
- `center_lat`
- `center_lng`
- `default_zoom`
- `supports_reporting`
- `supports_ward_map`
- `supports_accountability`
- `map_data_version` nullable
- timestamps

Seed:

### Pune
- `slug=pune`
- active
- Pune Municipal Corporation
- reporting true
- ward map true
- accountability true

### Preview
- Mumbai
- Bengaluru
- Hyderabad
- Delhi
- Chennai

All preview cities:
- reporting false
- ward/accountability false initially

## API

Add public:

- `GET /api/v1/cities`
- `GET /api/v1/cities/{slug}`

Do not build frontend selector yet beyond minimal types/client support if required.

## Existing complaint impact

Do **not** make `city_id` non-null yet.

If you choose to add `city_id` to complaint in this slice, it must be nullable and default/backfill strategy must be explicit. It is acceptable to defer complaint FK to Slice 3/5.

## Acceptance criteria

- Alembic upgrade works on local/dev DB.
- `GET /cities` returns Pune + preview cities.
- Pune capability flags are correct.
- No existing complaint endpoint breaks.
- No city logic is hard-coded in frontend conditionals yet.

## Ready-to-paste Cursor prompt

```text
Implement Slice 1 from the CivicSense V2 execution plan only.

Goal: make City a first-class backend configuration entity while preserving all existing app behavior.

Requirements:
- Add a City SQLAlchemy model using existing UUID/timestamp conventions.
- Fields/capabilities must match the V2 blueprint.
- Add a safe Alembic migration.
- Seed Pune as active/full support.
- Seed Mumbai, Bengaluru, Hyderabad, Delhi, Chennai as preview cities with reporting/ward/accountability disabled.
- Add public GET /api/v1/cities and GET /api/v1/cities/{slug} endpoints with Pydantic schemas.
- Reuse existing patterns; no repository-pattern/CQRS abstractions.
- Do not redesign the UI yet.
- Do not modify providers/deployment.
- Do not implement future slices.

Run migrations/checks and stop after acceptance criteria pass. Show exact files changed and proposed commit message.
```

## Suggested commit

`feat: add multi-city configuration foundation`

---

# Slice 2 — Pune 2025 electoral ward data package

## Goal

Create a reproducible, source-backed spatial dataset for the **41 current Pune electoral wards**.

This slice is data preparation, not map UI.

## Source

Primary:

- OpenCity Pune Wards Info: `https://data.opencity.in/dataset/pune-wards-info`
- 2025 resource: `https://data.opencity.in/dataset/pune-wards-info/resource/2badcc86-489c-4b7e-b7dd-a273ef01b798`

Metadata says:
- KML
- 41 wards
- updated Nov 2025
- Public Domain
- credit/source: Parisar; parent dataset cites PMC

## Rules

1. Download/source the actual KML; do not invent coordinates.
2. Convert to GeoJSON once during development.
3. Normalize to WGS84.
4. Preserve ward identifiers/names from source.
5. Validate exactly 41 usable ward features.
6. Commit the normalized file and source manifest.
7. Do not fetch OpenCity at app runtime.

## Suggested file structure

Adapt to actual repo, but target something like:

```text
backend/app/data/cities/pune/
  electoral_wards_2025.geojson
  source_manifest.json
```

Source manifest example:

```json
{
  "city": "pune",
  "dataset": "PMC Electoral Wards 2025",
  "source_page": "https://data.opencity.in/dataset/pune-wards-info/resource/2badcc86-489c-4b7e-b7dd-a273ef01b798",
  "source_parent": "https://data.opencity.in/dataset/pune-wards-info",
  "source_tier": "B",
  "license": "Public Domain",
  "credit": "Parisar",
  "source_data_date": "2025-11-25",
  "normalized_format": "GeoJSON",
  "crs": "EPSG:4326",
  "feature_count_expected": 41,
  "notes": "Normalized for CivicSense; do not silently replace without revalidation."
}
```

## Conversion tool

Prefer a one-time mature parser/tool. Do not write a complex custom KML parser.

If a temporary conversion dependency is required, keep it out of app runtime when practical.

## Validation script

Add a small script, e.g.:

`backend/scripts/validate_pune_ward_geojson.py`

Validate:

- FeatureCollection
- feature count = 41
- each feature has Polygon/MultiPolygon
- geometry valid (Shapely)
- no empty geometry
- ward identifier/name present
- coordinates plausibly in Pune/India

Do not require perfect non-overlap if source geometry has small topology artifacts, but report invalid geometry explicitly.

## Important handling if Cursor cannot download source

If automated download is blocked:

- do not fabricate a GeoJSON;
- create the manifest + validation/conversion script;
- stop and tell the user exactly which KML to download and where to place it.

## Acceptance criteria

- canonical GeoJSON exists from source, or Cursor explicitly stops awaiting the real KML;
- if GeoJSON exists, validator confirms 41 features;
- source manifest is committed;
- no frontend behavior changes.

## Ready-to-paste Cursor prompt

```text
Implement Slice 2 only: Pune current electoral ward spatial data package.

Use the source and provenance rules in the V2 blueprint. The primary source is OpenCity PMC Electoral Wards 2025 (41 wards):
https://data.opencity.in/dataset/pune-wards-info/resource/2badcc86-489c-4b7e-b7dd-a273ef01b798

Do not invent geometry. Download/convert the real KML to normalized WGS84 GeoJSON using a mature one-time tool/parser. Commit a canonical electoral_wards_2025.geojson plus source_manifest.json. Add a small validation script using Shapely or the simplest mature library available to verify FeatureCollection, 41 features, nonempty valid polygon/multipolygon geometry, identifiers/names, and plausible coordinates.

Do not fetch OpenCity at app runtime. Do not build the map UI yet.

If the source cannot be downloaded in your environment, stop rather than fabricate data; create the conversion/validation scaffolding and tell me exactly what KML I need to place where.

Run validation and stop after Slice 2.
```

## Suggested commit

`data: add versioned Pune electoral ward geometry`

---

# Slice 3 — Electoral ward model, GeoJSON API and jurisdiction resolver

## Goal

Make the backend able to:

- serve current Pune ward polygons;
- map a latitude/longitude to one electoral ward.

## Dependencies

Add **Shapely** only if not already present.

Do not add PostGIS in this phase.

## DB

Add `electoral_wards` table.

Recommended fields from blueprint:
- UUID
- city_id
- external_code nullable
- ward_no
- name
- geometry_feature_id
- valid dates nullable
- source URL/license
- verified_at

Seed/import the 41 records from canonical GeoJSON/source data.

Do not store the entire geometry redundantly in every DB row unless current architecture makes it clearly simpler. Canonical geometry file + feature ID is sufficient for V2.

## Service

Create a small `JurisdictionResolver` or equivalent service consistent with current code style.

Responsibilities:
- load/cached GeoJSON per active city/version;
- create Shapely polygons once;
- resolve `Point(lng, lat)`;
- return ward or outside-area result.

### Coordinate warning

Shapely uses x/y = longitude/latitude. Do not reverse them.

## API

Add:

### `GET /api/v1/cities/pune/wards`

Returns ward metadata without geometry.

### `GET /api/v1/cities/pune/wards/geojson`

Returns the FeatureCollection.

Add cache headers if easy within current stack.

### Internal/test resolver

Do not necessarily expose a raw debug endpoint in production. Resolver will be used by accountability API later.

## Tests

This is a case where a small backend test is justified.

If pytest already exists, add tests.

If no backend test dependency exists, Cursor may add pytest as a dev/test dependency if minimal. Avoid a complex coverage stack.

Tests should include:
- at least two known points inside different Pune wards, obtained/verified against the source map;
- one point outside PMC boundary;
- invalid coordinates.

Do not make up expected ward names for random coordinates. Use source-backed test fixtures.

## Acceptance criteria

- 41 ward metadata records seeded.
- GeoJSON endpoint returns 41 features.
- resolver returns exactly one ward for validated fixtures.
- outside point returns no ward/structured outside result.
- existing APIs unaffected.

## Ready-to-paste Cursor prompt

```text
Implement Slice 3 only.

Goal: backend serving/resolution for Pune's 41 current electoral wards.

Requirements:
- Add electoral_wards model + Alembic migration using existing conventions.
- Seed/import ward metadata from the canonical Slice 2 data; no invented names/codes.
- Add GET /api/v1/cities/{slug}/wards and GET /api/v1/cities/{slug}/wards/geojson.
- Add a small backend jurisdiction resolver using Shapely point-in-polygon with cached parsed geometry.
- Keep canonical geometry in the versioned data file; don't introduce PostGIS.
- The server is authoritative; note longitude/latitude axis order correctly.
- Add minimal tests/fixtures using source-verified points. Do not invent expected ward mappings.
- Do not build frontend map yet.

Run migration, tests/checks, verify the GeoJSON endpoint returns 41 features, then stop.
```

## Suggested commit

`feat: resolve Pune locations to electoral wards`

---

# Slice 4 — Pune ward offices + 2026 elected representatives

## Goal

Seed the two main accountability datasets:

1. current 15 PMC administrative ward offices;
2. current elected corporators from 2026 election results.

No “Who is responsible?” UI yet.

## 4.1 Ward offices

Create `ward_offices` model/table.

Seed 15 names from current source-backed list.

Do not seed current Assistant Commissioner names from old web pages unless verified for 2026. Office names are less volatile; individual officers are more volatile.

### Provenance

Use current PMC/environment report + supporting official/corroborating sources in manifest/seed metadata.

## 4.2 Electoral→administrative mapping

Create `ward_jurisdiction_mappings` table now, but do not force all 41 mappings to exist.

If a mapping has not been verified from an acceptable current source:

- leave it absent;
- do not infer solely from similar names;
- do not silently use 2017 boundaries as 2026 fact.

Historical DataMeet administrative geometry may be loaded later with `legacy` confidence if the product explicitly labels it, but do not convert uncertain mapping into “verified.”

## 4.3 Elected representatives

Create:
- `public_officials`
- `official_jurisdictions` (or simplest equivalent consistent with project)

Import corporators from:

OpenCity PMC Election Results 2026 CSV resource:
`https://data.opencity.in/dataset/pmc-election-results-2026/resource/ac74e3a3-0fce-4ce5-bcdf-b3b6271ae722`

Expected 165 elected seats/rows overall.

Fields available:
- ward no
- ward name
- seat
- reservation
- elected candidate
- party

Store enough source metadata to audit import.

Do not invent contact details.

## Data validator

Extend/create validation script to check:

- 15 ward offices
- 41 electoral wards
- 165 imported elected representatives if source CSV contains expected complete set
- every representative maps to an existing ward
- no duplicate seat within ward

If source uses ward number/name format different from GeoJSON, add a small explicit alias/mapping table checked into source data; do not use fuzzy matching silently in production seed.

## Acceptance criteria

- 15 ward offices seeded.
- 2026 corporator data imported or ingestion script ready awaiting source file.
- expected 165 rows validated when source available.
- no fake phone/email.
- no unverified electoral→ward-office mappings labelled verified.

## Ready-to-paste Cursor prompt

```text
Implement Slice 4 only: Pune accountability reference data.

Add ward_offices plus public_officials/official_jurisdictions (or the minimal equivalent consistent with existing architecture), and a versioned ward_jurisdiction_mappings table.

Seed the 15 current PMC ward-office names from the research blueprint. Do not seed individual officer names unless current 2026 source verification exists.

Import the 2026 elected corporators from the OpenCity public-domain PMC Election Results 2026 CSV resource:
https://data.opencity.in/dataset/pmc-election-results-2026/resource/ac74e3a3-0fce-4ce5-bcdf-b3b6271ae722
Expected current structure: 41 electoral wards, 165 elected seats.

Preserve source URL/date/license/verified metadata. Do not invent contact details. If ward numbering/name normalization is needed between the CSV and GeoJSON, use an explicit checked-in mapping/alias file and validate it; do not silently fuzzy-match.

Create the electoral→administrative mapping table but only insert mappings that can be verified. Missing mapping is preferable to a false one.

Add validation checks and stop after Slice 4.
```

## Suggested commit

`data: add Pune ward offices and 2026 representatives`

---

# Slice 5 — Departments, routing rules and accountability API

## Goal

Turn raw city/ward/official data into one useful backend response: **Who is responsible?**

## DB

Add:
- `departments`
- `category_routing_rules`
- `routing_channels`

### Department seed strategy

Do not try to reproduce all ~43 PMC departments immediately unless sourced cleanly.

Seed only departments needed for current CivicSense categories, e.g. where applicable:
- Road
- Water Supply
- Drainage
- Solid Waste Management
- Electrical
- Health
- Encroachment
- Building Permission
- Environment

Use names that can be sourced from PMC/public reporting.

### Category routing

Map existing CivicSense categories to departments.

Example only — Cursor must inspect current category seeds:

- pothole/road → Road Department
- garbage → Solid Waste Management
- water leakage/supply → Water Supply
- sewage/drainage → Drainage
- streetlight → Electrical

Do not change user-facing category IDs/names if existing complaints rely on them.

## Routing channels

Seed current, source-backed PMC channels as data records.

Examples:

- official PMC CARE portal/app
- PMC helpline `1800-103-0222`
- main contact `020-25501000`
- official-booklet WhatsApp/SMS `9689900002`, but mark source/date and make easy to deactivate if re-verification changes it
- general email `info@punecorporation.org` labelled general contact rather than guaranteed grievance intake

No raw values in frontend code.

## Service

Add `AccountabilityService`.

Input:
- city slug
- lat
- lng
- category ID

Resolve:
1. city
2. electoral ward
3. verified ward office if available
4. department
5. current elected representatives
6. active routing channels
7. warnings/provenance

## API

Add:

`GET /api/v1/cities/{slug}/accountability?lat=&lng=&category_id=`

Validation:
- valid coordinates
- active city capability
- existing category
- outside boundary handled intentionally

## Acceptance criteria

For a validated Pune point/category:
- response returns Pune/PMC;
- electoral ward;
- mapped department;
- 4 or 5 representatives depending ward data;
- ward office only if verified;
- routing channels;
- source/verification fields/warnings.

No UI yet.

## Ready-to-paste Cursor prompt

```text
Implement Slice 5 only: departments, routing configuration and the Pune accountability API.

Read the current CivicSense category model/seeds first. Preserve existing category IDs/names.

Add minimal Department, CategoryRoutingRule and RoutingChannel models + migration. Seed only PMC departments needed by current categories, using sourced names. Add source/verified metadata.

Seed official Pune routing channels as data/config records, not JSX/Python constants. Use the blueprint's source-backed PMC CARE/helpline/contact values and clearly distinguish general contact from confirmed grievance channel. Do not integrate the undocumented PMC CARE API.

Implement AccountabilityService:
city + lat/lng + category → electoral ward → verified ward office if available → department → current elected reps → active routing channels + provenance/warnings.

Add GET /api/v1/cities/{slug}/accountability?lat=&lng=&category_id=.
If ward-office mapping is not verified, return null + a clear warning instead of guessing.

Add focused backend tests and stop after Slice 5.
```

## Suggested commit

`feat: add source-backed Pune accountability routing`

---

# Slice 6 — V2 visual foundation + app shell + city selector

## Goal

This is the first major visual change. Make CivicSense immediately look like a deliberate product before map features are added.

## Do first

Inspect existing Tailwind/shadcn theme and avoid duplicate theme systems.

## Design system

Implement CivicSense tokens from blueprint through the existing Tailwind/CSS variable approach.

Desired:
- neutral light background
- white surfaces
- civic navy
- restrained blue primary
- green/amber status colors
- stronger typography
- 12–16px radius
- subtle border/shadow

No neon/gradients by default.

## Shared shell

Create/refactor reusable:

- `AppHeader`
- `CitySelector`
- page container/layout
- status badges
- loading skeletons

Use current component conventions.

## City selector behavior

Fetch from `/api/v1/cities` via existing API/TanStack Query patterns.

Display:
- India context
- Pune — Active
- Mumbai — Coming soon
- Bengaluru — Coming soon
- Hyderabad — Coming soon
- Delhi — Coming soon
- Chennai — Coming soon

Persist selected city in a lightweight way:
- URL query or localStorage/context if current patterns support it.

Recommendation: keep `city` in URL/query for shareability if it does not cause route churn; otherwise a small context + localStorage is acceptable. Do not add Redux/Zustand solely for this.

## Preview city state

Selecting preview city updates hero/location context and shows:

> Coming soon — verified ward, reporting and government-routing data for this city is not active yet.

Do not pretend feature data exists.

## Acceptance criteria

- UI looks visibly redesigned even before map polygons.
- city selector works.
- Pune active; others preview.
- no auth/provider changes.
- mobile header clean.
- existing complaint/report routes still reachable.

## Ready-to-paste Cursor prompt

```text
Implement Slice 6 only: CivicSense V2 visual foundation and multi-city app shell.

Do not touch infrastructure/auth providers. Inspect current Tailwind/shadcn theme first and reuse it rather than creating a parallel styling system.

Implement the blueprint's calm civic design tokens, stronger typography/spacing, AppHeader, CitySelector, status badges/skeleton basics, and the new map-first home shell structure (map can still be placeholder in this slice).

CitySelector must consume GET /api/v1/cities. Pune is Active. Mumbai, Bengaluru, Hyderabad, Delhi and Chennai display Coming soon/Preview and must not expose fake ward/accountability/reporting data.

Keep state simple; no Redux/Zustand addition unless already present.

Preserve existing complaint/auth/officer/admin flows. Run lint/build and stop after Slice 6. Include screenshots or a concise description of the resulting desktop/mobile layout if your environment supports it.
```

## Suggested commit

`feat: introduce CivicSense V2 city shell and design system`

---

# Slice 7 — Pune ward map + preview city maps

## Goal

Make the home experience genuinely map-first.

## Google Maps rule

Use existing Google Maps integration. Do not replace it with Leaflet/Mapbox.

## Pune

Load:

`GET /api/v1/cities/pune/wards/geojson`

Render via Google Maps JavaScript **Data Layer**.

Use:
- `addGeoJson()` after fetching through existing API client, or `loadGeoJson()` only if CORS/path is clean;
- dynamic `setStyle`;
- click/hover listeners;
- `overrideStyle/revertStyle` if useful.

## Map states

### Default ward
- neutral low-opacity fill
- slate border

### Hover
- stronger boundary
- tooltip/card with ward number/name

### Selected
- blue stroke
- pale blue fill

Clicking ward updates selected ward state and right/bottom panel heading.

## Preview cities

On Mumbai/Bengaluru/Hyderabad/Delhi/Chennai:

- center map to city;
- same visual shell;
- show Preview/Coming soon overlay;
- no complaint pins/accountability;
- no requirement to ingest their ward geometry yet.

If Cursor can add a city boundary from a clearly sourced lightweight dataset without scope explosion, it can be proposed but not required.

## Map key handling

Production should not show developer `.env` instructions to end users.

If `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` missing:
- development: helpful config message;
- production: polished “Map temporarily unavailable” state + log error.

## Accessibility

- ward selection must have a corresponding list/panel representation;
- custom controls are native buttons;
- tooltips not the sole source of data.

## Acceptance criteria

- 41 Pune polygons render.
- hover/click works.
- selected ward state is visible.
- preview cities recenter and show correct coming-soon state.
- mobile map works without horizontal overflow.

## Ready-to-paste Cursor prompt

```text
Implement Slice 7 only: Pune ward map and preview-city map shell.

Keep Google Maps; do not add Leaflet/Mapbox. Reuse the project's current map loader/integration.

For Pune, fetch GET /api/v1/cities/pune/wards/geojson and render all 41 electoral wards through the official Google Maps JavaScript Data Layer. Add restrained default/hover/selected styles and ward click selection. Selected ward must update the side/bottom panel state.

For preview cities, recenter the same map shell and show a clear Coming soon overlay; no fake ward/accountability data and no reporting.

Handle missing map key professionally: dev can show setup guidance, prod should show polished unavailable state.

Use native accessible controls. Run lint/build and stop after Slice 7.
```

## Suggested commit

`feat: add interactive Pune electoral ward map`

---

# Slice 8 — Complaint pins, clustering and map/feed synchronization

## Goal

Put real CivicSense complaints on the map and make map + issue list feel like one product.

## API/read model

Inspect current complaint feed endpoint before creating anything new.

Prefer extending current public feed with filters:

- `city`
- `electoral_ward_id`
- `status`
- `category_id`
- pagination

Add a lightweight map mode/read schema only if current response is too heavy.

Public marker payload must not include private exact address/user info beyond what policy allows.

## Marker clustering

Use:

`@googlemaps/markerclusterer`

Only add it if not already installed.

## Marker visuals

- submitted/open: blue
- in progress: amber
- resolved: green
- closed: slate

Pins should be modest, not giant branded bubbles.

## Interaction

### Map → list
- click ward: filter issue list to ward
- click marker: highlight/open compact issue preview

### List → map
- click/hover card: focus relevant marker if safe
- avoid constant pan/zoom on minor hover if jarring

### Filters
At minimum:
- status
- selected ward

Category filter can be added if current UI remains clean.

## Privacy handling for markers

If public exact lat/lng is currently hidden, do **not** accidentally expose it merely to render pins.

Choose one policy:

A. public coordinates are rounded/obfuscated server-side; or
B. map marker endpoint returns safe approximate coordinates distinct from private exact location.

Document which is used.

Do not send exact private coordinates to unauthenticated public clients if existing policy says they are private.

## Acceptance criteria

- real complaints appear on Pune map.
- cluster at lower zoom.
- selected ward filters list.
- status filter updates map/list.
- public network response does not leak exact address/reporter PII.

## Ready-to-paste Cursor prompt

```text
Implement Slice 8 only: complaint pins + clustering + map/feed synchronization.

Inspect the existing public complaint feed endpoint first; extend it rather than creating redundant APIs where possible. Add city/ward/status filtering and a lightweight map representation only if needed.

Use @googlemaps/markerclusterer for real complaint markers. Status semantics: submitted/open blue, in_progress amber, resolved green, closed slate.

Map and issue list must stay synchronized: ward click filters feed, marker click opens/highlights issue preview, issue card can focus marker without jarring constant movement.

Critical privacy requirement: do not expose reporter PII, exact address or private exact lat/lng in a public endpoint. If public pins need coordinates, return rounded/obfuscated public coordinates explicitly and document the policy.

Run lint/build/backend checks and stop after Slice 8.
```

## Suggested commit

`feat: connect public complaint feed to city map`

---

# Slice 9 — Complaint wizard V2 + server-derived jurisdiction

## Goal

Make reporting visually polished and ensure city/ward routing is real.

## Preserve existing flow logic

Do not rebuild form state from scratch unless unavoidable.

Maintain existing steps:
- Location
- Photo
- Category
- Description
- Review
- Submit

## Visual redesign

- compact progress indicator
- clearer section titles and helper copy
- large map/location card
- polished photo dropzone/preview
- category cards/select
- review summary
- responsive layout

## City behavior

Pune:
- enabled

Preview city:
- Report Issue button disabled or routes to clear “not yet supported” state.

## Jurisdiction resolution

After user sets Pune location + category:

call:

`GET /api/v1/cities/pune/accountability?...`

Show electoral ward and department as a preview.

### On submit

Backend must recompute/validate jurisdiction. Do not trust client ward IDs.

## Complaint DB migration

Add nullable FKs to existing complaints if not already done:

- `city_id`
- `electoral_ward_id`
- `ward_office_id`
- `department_id`

For new Pune complaints, fill them server-side.

Backfill old complaints separately/safely; do not block new functionality on complete historical backfill.

## Outside boundary

If location is outside current PMC area:

> This location is outside the currently supported Pune Municipal Corporation area.

Do not allow a Pune report with a random ward.

## Acceptance criteria

- full wizard looks V2 quality.
- current auth/upload works.
- category/photo validation still works.
- Pune location resolves ward.
- server saves derived city/ward/department.
- preview cities cannot submit fake reports.

## Ready-to-paste Cursor prompt

```text
Implement Slice 9 only: V2 complaint wizard and authoritative jurisdiction persistence.

Preserve the existing wizard/form/upload logic where possible; this is a visual/product refinement plus server routing, not a rewrite.

For Pune, after location/category selection call the accountability endpoint and show a small jurisdiction preview. On POST complaint, backend must recompute/validate city/electoral ward/ward office/department from lat/lng + category rather than trusting client IDs.

Add nullable city_id/electoral_ward_id/ward_office_id/department_id FKs to existing Complaint with a safe Alembic migration if not already present. New Pune complaints should be populated server-side.

Preview cities cannot submit; show a clean Coming soon state.

Outside PMC boundary must return/display a clear supported-area error; never guess a ward.

Redesign the existing 5-step UI to match the V2 blueprint. Do not change Cloudinary/Clerk/Google Maps providers. Run all checks and stop after Slice 9.
```

## Suggested commit

`feat: route new Pune complaints by verified jurisdiction`

---

# Slice 10 — “Who is responsible?” component and accountability UX

## Goal

Make accountability a signature visible feature.

## Component

Create a reusable component, e.g.:

`AccountabilityCard`

Use existing component naming/folder conventions.

## Display order

1. **Municipal body**
2. **Operational department**
3. **Local ward office** (only if verified)
4. **Electoral ward**
5. **Elected representatives**
6. **Official route**
7. source / last verified

## Language

Use exact semantics:

- “Operational department”
- “Local ward office”
- “Elected representatives for this ward”

Do not say a corporator is “assigned” or “responsible for fixing” the issue.

## Uncertain mapping state

If no verified local ward office:

> Local ward office mapping is being verified.

The card still shows department/ward/reps.

## Where to show it

Minimum:
- complaint Review step
- complaint Detail page
- selected Ward side panel (compact variant)

## Source transparency

The card should have a discreet:

`Data source / last verified`

popover/details link rather than overwhelming the main UI.

## Acceptance criteria

- card works with complete and partial data.
- no fabricated contact/authority labels.
- mobile layout clean.
- representatives are current sourced data.

## Ready-to-paste Cursor prompt

```text
Implement Slice 10 only: the reusable Who is responsible? / AccountabilityCard UI.

Use the accountability API. Show municipal body, operational department, verified local ward office if available, electoral ward, current elected representatives, official route, and discreet source/last-verified metadata.

Language must distinguish operational authority from elected representatives. Never label a corporator as assigned officer/resolver. If local ward-office mapping is missing, display “Local ward office mapping is being verified” instead of guessing.

Add full card to complaint Review and Detail, and a compact variant to the selected-ward panel. Keep the visual style calm and consistent with V2.

Do not build official submission yet. Run lint/build and stop.
```

## Suggested commit

`feat: surface ward and authority accountability`

---

# Slice 11 — Official PMC handoff + external token capture

## Goal

Connect a CivicSense complaint to real official action without pretending to have an approved server-to-server PMC API.

## DB

Add `external_submissions` table.

Fields from blueprint, minimally:
- id UUID
- complaint_id
- routing_channel_id nullable
- provider `pmc_care`
- status
- external_token nullable
- status_url nullable
- forwarded_at nullable
- token_received_at nullable
- timestamps

Do not store government OTP/session/token credentials.

## UI module

Create `OfficialHandoffCard` or equivalent.

### State 1 — not forwarded

Show:

**Send this to the official system**

Primary action:
- Open PMC CARE

Secondary actions if active in routing config:
- WhatsApp
- Call helpline
- Copy complaint summary

Explain:

> CivicSense tracks your report independently. PMC will provide its own complaint/token reference after official registration.

### State 2 — handoff started/forwarded

Show:
- handoff timestamp
- channel
- “Add PMC token”

### State 3 — token received

Show:
- official token prominently
- external status if manually known
- CivicSense status separately

## WhatsApp

User initiated only.

Generate a deterministic prefilled message from safe fields.

Do not send server-side WhatsApp in this slice.

Before constructing a WhatsApp URL, make sure active channel record is configured and verified.

## API

Minimal:

- create/update external submission record
- owner/officer authorization according to current RBAC

A public viewer cannot attach or modify someone else's token.

## Acceptance criteria

- internal complaint can be forwarded via official user-controlled actions.
- click does not falsely set “PMC registered.”
- user can attach token.
- token appears on detail.
- no undocumented PMC API call.

## Ready-to-paste Cursor prompt

```text
Implement Slice 11 only: official PMC handoff + external token capture.

Add a minimal ExternalSubmission model/migration linked to Complaint and optional RoutingChannel. Never store PMC OTP/session credentials.

Build an OfficialHandoffCard on the owner complaint detail/success flow:
- Open official PMC CARE
- user-initiated WhatsApp if active routing config provides an official channel
- call helpline
- copy deterministic complaint summary
- then allow owner/authorized officer to add the PMC token received later.

A click/handoff must NOT be represented as “PMC complaint registered.” Keep CivicSense status and external PMC status visibly separate.

Do not call the reverse-engineered api.pmccare.in endpoints. No server-side WhatsApp integration.

Add authorization checks and focused backend tests. Stop after Slice 11.
```

## Suggested commit

`feat: add user-controlled PMC complaint handoff`

---

# Slice 12 — Complaint detail page and timeline V2

## Goal

Make the complaint detail page the strongest single screen in the product.

## Desktop structure

Recommended:

### Left/main
- back/breadcrumb
- status + title
- media gallery
- description
- location/ward map snippet
- timeline

### Right/sticky rail
- accountability card
- official handoff/token card
- complaint metadata

Mobile stacks naturally.

## Timeline

Use existing status history/audit records.

Timeline events:
- complaint submitted
- status changes
- officer notes safe for viewer
- external handoff
- PMC token added
- resolution evidence

Respect privacy/role rules for internal notes.

## Approximate vs exact location

Public viewer:
- ward + approximate locality
- safe/approx map

Owner/officer:
- exact location according to current authorization

## Acceptance criteria

- detail page looks production-quality.
- timeline integrates existing status history.
- accountability/handoff visible.
- public privacy preserved.

## Ready-to-paste Cursor prompt

```text
Implement Slice 12 only: CivicSense V2 complaint detail + timeline.

Redesign the existing detail page using the V2 hierarchy: status/title, media, description, safe location map/ward context, status timeline, AccountabilityCard, OfficialHandoffCard/token, and metadata. Reuse existing complaint status-history records; do not create a second timeline system.

Public viewer must only receive/show approximate location and safe public events. Owner/officer can see exact location/internal data according to existing authorization.

Keep responsive mobile stacking and existing routes. Run lint/build/backend checks and stop.
```

## Suggested commit

`feat: redesign complaint detail around accountability`

---

# Slice 13 — Officer/admin compatibility and light V2 alignment

## Goal

Ensure the new city/jurisdiction fields improve officer work without a second major redesign project.

## Officer dashboard

Add filters if data exists:
- city
- electoral ward
- ward office
- department
- status

Show:
- external token indicator
- department
- ward

Do not build automated assignment unless current app already supports/needs it.

## Admin stats

Ensure existing stats can be city-scoped.

Add basic routing-data health only if simple:
- count of unverified ward-office mappings
- date of current Pune geometry

Do not build a city-data CMS.

## Visual alignment

Apply V2 header/card/status styles to officer/admin pages where low-risk.

Do not spend this slice redesigning every table from scratch.

## Acceptance criteria

- existing officer status update still works.
- admin role management still works.
- new FKs do not break stats.
- city/ward/department filters work where added.

## Ready-to-paste Cursor prompt

```text
Implement Slice 13 only: officer/admin compatibility with V2 city/jurisdiction data.

Preserve all existing role behavior. Add practical filters/labels for city, electoral ward, verified ward office and department where the current dashboard/query architecture can support them cleanly. Show external-token presence where useful.

Scope existing admin stats by city without rewriting the analytics subsystem. A small data-health indicator is acceptable; do not build a city-data CMS.

Apply V2 styling lightly to existing officer/admin surfaces, but do not launch a separate redesign project.

Run role-flow checks and stop.
```

## Suggested commit

`feat: add city routing context to officer workflows`

---

# Slice 14 — Privacy, accessibility, data-quality and performance QA

## Goal

Turn the implementation into something safe enough to demo publicly.

## 14.1 Public API privacy audit

Inspect all unauthenticated endpoints for accidental exposure of:

- exact latitude/longitude
- full address
- reporter name
- email
- phone
- Clerk ID
- internal notes

Explicitly test public vs owner vs officer complaint responses.

## 14.2 Location notice

Add a concise complaint-time privacy notice consistent with the blueprint.

Do not present legal advice; provide clear product disclosure.

## 14.3 Image metadata

Inspect current Cloudinary upload behavior.

If EXIF/GPS metadata can be removed through existing Cloudinary transformation/settings with minimal changes, do so. Do not write a custom image-processing service.

## 14.4 Accessibility audit

Check:
- keyboard navigation
- focus states
- labels
- map control buttons
- status text not color-only
- mobile targets
- issue list alternative to map

## 14.5 Performance

Check:
- ward GeoJSON cached
- no repeated geometry fetch on map pan
- marker clustering
- Cloudinary thumbnails instead of full images in cards
- complaint feed pagination
- reasonable production bundle/build

## 14.6 Data validation

Run a single validation command/script that reports:

- cities
- 41 Pune electoral wards
- 15 ward offices
- 165 representatives if source import complete
- routing rules for every current CivicSense category or explicit unmapped warnings
- active official channels with source/verified date

## Acceptance criteria

- no public PII leaks found.
- V2 pages keyboard usable.
- data validation passes or reports intentional partial mappings.
- production build succeeds.

## Ready-to-paste Cursor prompt

```text
Implement Slice 14 only: privacy/accessibility/data-quality/performance hardening.

Audit every public complaint/city/map endpoint for exact lat/lng, full address, reporter PII, Clerk IDs and internal notes. Verify role-specific responses deliberately.

Add the concise complaint privacy/location notice from the blueprint. Review Cloudinary handling and strip unnecessary EXIF/GPS using existing platform capabilities if feasible; no custom image-processing service.

Audit keyboard/focus/labels/map controls/status semantics/mobile target sizes. Preserve an issue-list alternative to the map.

Verify GeoJSON caching, marker clustering, feed pagination and Cloudinary thumbnails.

Create/extend one data validation command to report expected Pune counts and source-verification gaps.

Run production build/tests and stop.
```

## Suggested commit

`chore: harden CivicSense V2 privacy and quality`

---

# Slice 15 — Production migration, deploy and smoke test

## Goal

Deploy V2 using the **same** infrastructure.

## Pre-deploy checklist

### Git
- feature branch clean
- migrations committed
- source manifests committed
- no secrets committed

### Backend
- all Alembic migrations reviewed
- Railway variables unchanged except any genuinely new non-secret configuration
- `DATABASE_URL` still correct
- Clerk production configuration still correct
- Cloudinary credentials still correct

### Frontend
- Vercel production env has:
  - production Clerk keys
  - backend API URL
  - Google Maps API key
- Google Maps key restricted to production domain(s)
- no development-mode banners/errors

## Database migration

Run production Alembic upgrade once through the established Railway/deployment method.

Do not run ad-hoc SQL separately unless migration fails and issue is diagnosed.

## Smoke test sequence

### A. Public city/map
1. Open production root.
2. Pune map loads.
3. 41 ward boundaries visible.
4. issue feed/pins load.
5. select ward.
6. switch to Mumbai preview; reporting is not falsely enabled.
7. switch back to Pune.

### B. Citizen
1. sign up/sign in using simplified working Clerk method.
2. Report Issue.
3. pin valid Pune location.
4. upload photo.
5. choose category.
6. verify ward/department preview.
7. submit.
8. complaint appears on feed/map.
9. detail shows accountability.
10. click official PMC CARE/hand-off action.
11. attach a test external token only if using a clearly marked test value; remove it after test if necessary.

### C. Public privacy
Open complaint signed out/incognito:
- no reporter identity
- no exact address
- no exact coordinates in response/UI

### D. Officer
- open queue
- filter by city/ward/department if implemented
- update status with note
- citizen/public timeline changes correctly

### E. Admin
- stats load
- role management works
- no regression

### F. Health
Backend health:

```json
{"status":"ok","database":"connected"}
```

## Rollback

Before production deploy, identify last known-good Vercel deployment and Railway deployment.

If V2 breaks critical flows:
- rollback frontend in Vercel;
- rollback backend deployment in Railway only if DB schema remains backward-compatible;
- because migrations are additive/nullable by design, old code should tolerate new tables/nullable columns.

This backward-compatibility is why earlier slices must not drop/rename core columns casually.

## Ready-to-paste Cursor prompt

```text
Prepare Slice 15 production release only. Do not introduce new features.

Review all V2 migrations for additive/backward-compatible behavior, verify no secrets/source credentials are committed, run full frontend build + backend tests/data validators, and produce a deployment checklist for the existing Vercel + Railway + Supabase + Clerk + Cloudinary + Google Maps stack.

Do not migrate infrastructure.

After deploy, guide the exact smoke-test sequence from the execution plan: Pune map/41 wards, preview cities, citizen report, accountability, official handoff, public privacy, officer update, admin stats, backend health.

If anything fails, diagnose before making broad changes.
```

## Suggested merge/release commit

`release: CivicSense V2 Pune map and accountability`

---

# Appendix A — Recommended source files and ownership

The exact paths must follow the real repo discovered in Slice 0. This appendix describes logical ownership only.

## Backend

```text
app/
  models/
    city.py
    electoral_ward.py
    ward_office.py
    department.py
    public_official.py
    routing.py
    external_submission.py
    complaint.py                 # extend existing
  schemas/
    city.py
    accountability.py
    routing.py
    complaint.py                 # extend existing
  routers/
    cities.py
    complaints.py                # extend existing
  services/
    jurisdiction.py
    accountability.py
    routing_message.py
  data/
    cities/
      pune/
        electoral_wards_2025.geojson
        source_manifest.json
        ward_aliases.json        # only if source normalization genuinely needs it
scripts/
  validate_city_data.py
  import_pune_representatives.py # if CSV import is not part of migration seed
```

Do not create every file if current project conventions make a smaller structure cleaner.

## Frontend

Logical feature ownership:

```text
features/
  cities/
    city-selector
    city-preview-state
  map/
    civic-map
    ward-layer
    complaint-markers
    map-filters
  accountability/
    accountability-card
  complaints/
    existing wizard/detail/feed components, redesigned not duplicated
  routing/
    official-handoff-card
```

Again: adapt to actual existing feature structure.

---

# Appendix B — Suggested API contract checklist

Before changing the frontend, Cursor should confirm these contracts through FastAPI OpenAPI/Swagger.

## Cities

- [ ] `GET /api/v1/cities`
- [ ] `GET /api/v1/cities/{slug}`

## Wards

- [ ] `GET /api/v1/cities/{slug}/wards`
- [ ] `GET /api/v1/cities/{slug}/wards/geojson`

## Accountability

- [ ] `GET /api/v1/cities/{slug}/accountability`

## Complaints

Existing:
- [ ] public feed
- [ ] mine
- [ ] detail
- [ ] create
- [ ] status update

Extended filters:
- [ ] city
- [ ] ward
- [ ] department where useful

## External routing

- [ ] create handoff record
- [ ] update/add external token

---

# Appendix C — Data-quality invariants

The following should be expressed in code/validator where practical:

1. `pune` is the only `active` city at V2 launch.
2. Pune active electoral ward dataset has exactly 41 features/records.
3. Current representative import has 165 seats if complete.
4. Every imported representative has an existing electoral ward.
5. No official record is displayed without a source URL.
6. No routing channel marked `is_official=true` lacks a source/verified date.
7. No `verified` electoral→ward-office mapping lacks a source.
8. A complaint's electoral ward belongs to the same city as complaint city.
9. A complaint's department belongs to the same city.
10. Preview cities cannot accept complaint creation through the normal UI/API policy.

---

# Appendix D — Manual UX acceptance checklist

## Desktop home

- [ ] Header feels polished, not like a default scaffold.
- [ ] City selector obvious.
- [ ] Map is visually dominant.
- [ ] Ward boundaries visible but not noisy.
- [ ] Right panel readable at 1366px width.
- [ ] Report CTA prominent.
- [ ] No developer/debug text.

## Mobile home

- [ ] Map usable at ~390px width.
- [ ] bottom content does not cover essential Google attribution/controls improperly.
- [ ] issue cards readable.
- [ ] report CTA thumb-friendly.
- [ ] city selector does not overflow.

## Complaint wizard

- [ ] location feels visual and simple.
- [ ] user understands ward is auto-resolved.
- [ ] photo requirement clear.
- [ ] category manual choice always available.
- [ ] review includes accountability preview.
- [ ] official-government handoff expectation clear.

## Complaint detail

- [ ] status visible immediately.
- [ ] citizen can see responsible department without scrolling through noise.
- [ ] CivicSense ticket vs PMC token distinction obvious.
- [ ] timeline understandable.
- [ ] public viewer sees no sensitive details.

---

# Appendix E — Things Cursor must challenge instead of blindly implementing

Cursor must stop and report rather than guess if:

1. The 2025 Pune geometry source cannot be obtained.
2. Ward numbers/names between geometry and election CSV do not reconcile deterministically.
3. A proposed ward-office mapping is based only on an old 2017 polygon and would be shown as current.
4. A PMC channel cannot be verified from a reasonable source.
5. The current complaint schema has hidden coupling that would make nullable FKs unsafe.
6. Public exact coordinates are currently required by map code and privacy would be weakened.
7. A migration would delete/rename production columns.
8. A new dependency duplicates functionality already installed.
9. Deployment changes would require replacing Vercel/Railway/Supabase/Clerk/Cloudinary/Google Maps.
10. The requested direct PMC integration would rely on undocumented OTP/session behavior.

The correct response is a short technical note with the exact blocker and safest option — not a fabricated implementation.

---

# Appendix F — Master prompt to give Cursor before each work session

```text
You are implementing CivicSense V2 in an existing production-oriented repository.

First read:
1. docs/CivicSense_V2_Product_Data_Technical_Blueprint.md
2. docs/CivicSense_V2_Cursor_Execution_Plan.md
3. docs/V2_BASELINE_AUDIT.md (after Slice 0)

Non-negotiables:
- Keep Vercel, Railway, Supabase PostgreSQL, Clerk, Cloudinary and Google Maps.
- Keep Next.js 15 + FastAPI + SQLAlchemy/Alembic.
- Modular monolith; no microservices/Redis/Kafka.
- Prefer mature libraries and minimal code.
- Never fabricate government/ward/official data.
- Keep source provenance for civic data.
- No direct undocumented PMC CARE API integration.
- Public UI/API must not expose exact location or reporter PII.
- Implement only the slice I explicitly ask for; do not work ahead.

Before editing, inspect the relevant current code and tell me if the slice conflicts with existing architecture. Then implement the smallest complete change, run checks, and report files changed + commands/results + risks + proposed commit message.
```

