# CivicSense V2 — Product, UX, Data & Technical Blueprint

**Status:** Implementation specification for Cursor  
**Date:** 13 September 2026  
**Scope:** CivicSense multi-city India product architecture, with **Pune as the only fully functional launch city**  
**Repository:** `talrejagovinda28/civicsense-platform`  
**Audience:** Cursor / software engineer implementing the next product phase

---

## 0. Read this first — non-negotiable constraints

This document is a **redesign and expansion specification**, not a request to rewrite the product from scratch.

### Infrastructure must stay exactly as-is

Do **not** migrate providers or introduce substitutes unless explicitly approved later.

| Concern | Keep |
|---|---|
| Frontend hosting | **Vercel** |
| Backend hosting | **Railway** |
| Database | **Supabase PostgreSQL** |
| Authentication | **Clerk** |
| Image storage | **Cloudinary** |
| Maps | **Google Maps Platform** |
| Source control | **GitHub** |
| Backend framework | **FastAPI** |
| Frontend framework | **Next.js 15 App Router** |
| ORM / migrations | **SQLAlchemy 2.x + Alembic** |

### Engineering philosophy

1. Preserve the existing working complaint, authentication, officer and admin flows wherever possible.
2. Prefer mature libraries over custom infrastructure.
3. Keep a modular monolith; **no microservices**.
4. Do not add Redis, Kafka, WebSockets, Elasticsearch, a GIS server, or a new cloud provider for this phase.
5. Do not build an undocumented direct integration into PMC CARE as a production dependency.
6. Every civic/government data record that can become stale must carry **source and verification metadata**.
7. Build one vertical slice at a time. Do not attempt this entire document in one Cursor run.

---

# 1. Product vision

## 1.1 One-line definition

**CivicSense is a map-first civic accountability platform for Indian cities that helps a citizen see local issues, report a problem, understand which public body is responsible, and track both the CivicSense ticket and any official-government complaint reference.**

## 1.2 Positioning

CivicSense should not feel like another generic form or admin dashboard.

The product should feel like:

> **A civic operating layer for a city — map, issues, jurisdictions, responsible departments, elected representatives, official routing and progress in one place.**

The first city is Pune. The architecture must make future cities data/config additions rather than rewrites.

## 1.3 Product promise

A citizen should be able to answer five questions quickly:

1. **What civic issues are happening near me?**
2. **Which ward am I in?**
3. **Who is operationally responsible for this issue?**
4. **Who are my elected local representatives?**
5. **What happened after I reported the issue?**

---

# 2. Research findings that drive the design

This section distinguishes verified findings from assumptions. Cursor must not convert a weak source into authoritative application behavior.

## 2.1 Pune has two different concepts that must not be conflated

### Electoral wards

The current Pune Municipal Corporation electoral structure is **41 wards and 165 elected corporators**. The 2026 municipal election elected four corporators from 40 wards and five from one ward. Maharashtra State Election Commission results and current election reporting corroborate this structure.

**Use electoral wards for:**
- the public ward map;
- ward identity and ward-level issue statistics;
- elected representative lookup;
- political/accountability context.

### Administrative ward offices

PMC also operates through **15 ward offices**. These are administrative service-delivery units and are operationally more relevant to many local complaints.

A recent PMC Environmental Status Report lists the 15 current ward-office names:

1. Aundh - Baner
2. Bhavani Peth
3. Bibwewadi
4. Dhankawadi - Sahakar Nagar
5. Dhole Patil Road
6. Hadapsar - Mundhwa
7. Kasaba Vishrambagwada
8. Kondhwa - Yewalewadi
9. Kothrud - Bavdhan
10. Nagar Road - Vadgaonsheri
11. Shivajinagar - Ghole Road
12. Sinhgad Road
13. Wanawadi / Wanowrie - Ramtekdi
14. Warje - Karvenagar
15. Yerawada - Kalas - Dhanori

**Use administrative ward offices for:**
- operational responsibility when the mapping is verified;
- ward-office contact/routing context;
- officer-dashboard filters if applicable.

### Critical rule

**Do not assume an electoral ward and an administrative ward office are the same thing.**

Boundaries and administrative assignments can change. Therefore, the product needs a versioned mapping/provenance layer rather than hard-coded permanent assumptions.

---

## 2.2 Pune spatial data is available, but source/version matters

OpenCity publishes a public-domain **PMC Electoral Wards 2025 KML** with **41 electoral wards**, updated November 2025. Its Pune wards dataset cites PMC as the dataset source and identifies Parisar as credit for the 2025 resource.

DataMeet also publishes Pune municipal spatial data, including historical 2017 administrative ward polygons, but its documentation explicitly states that some boundaries were manually traced and therefore can contain inaccuracies.

### Decision

For the active Pune public ward map:

- **Primary electoral geometry:** OpenCity `PMC Electoral Wards 2025` (41 wards).
- Convert once to validated **GeoJSON / WGS84** and commit a normalized copy with a source manifest.
- Do not fetch third-party KML from the browser at runtime.
- Historical DataMeet administrative polygons may be used only as a **fallback/reference** and must be labelled with their year/source/confidence.

---

## 2.3 Current elected representatives are obtainable

OpenCity publishes a public-domain **PMC Election Results 2026** CSV sourced from Maharashtra election data. Fields include:

- Ward No.
- Ward Name
- Seat
- Reservation
- Elected Candidate Name
- Party

### Decision

Import the 2026 ward winners into CivicSense as **public elected representatives** linked to electoral wards. Do not invent phone numbers or emails if the official/public dataset does not include them.

The representative section must say **“Elected representatives”**, not “people responsible for fixing the complaint.” Operational responsibility belongs primarily to PMC departments/ward administration.

---

## 2.4 PMC CARE is the real official grievance channel

PMC officially operates **PMC CARE** as its citizen-engagement/grievance platform. The current Google Play listing (updated July 2026) explicitly includes grievance redressal and location-based services.

Official PMC material also documents multiple contact channels. Verified sources currently include:

- **PMC Helpline:** `1800-103-0222`
- **PMC main contact:** `020-25501000`
- **General email:** `info@punecorporation.org`
- **SMS/WhatsApp documented in PMC CARE booklet:** `9689900002`
- **PMC CARE:** official web/app service

### Important data-quality rule

Channels can change. **Do not hard-code them permanently in JSX or Python constants.** Store them as versioned routing-channel records with:

- source URL;
- verified date;
- `is_official` flag;
- active/inactive status.

The general PMC email should be labelled **general contact**, not guaranteed complaint intake, unless a current official source explicitly states otherwise.

---

## 2.5 PMC complaint routing is department/ward based

September 2026 reporting on PMC CARE states that complaints are spread across **15 ward offices and roughly 43 civic departments**, and that complaints are categorised/routed to the relevant ward office, department or engineer.

Current department examples visible in PMC reporting include:

- Health
- Water Supply
- Road
- Chief Engineer / Projects
- Encroachment
- Environment
- Building Permission
- Drainage
- Solid Waste Management
- Electrical
- Property Tax
- Estate and Management

### Decision

CivicSense needs a first-class **Department** concept and a versioned **category → department routing rule**.

---

## 2.6 There is evidence of an underlying PMC CARE API — but it is undocumented

The open-source `ForceGT/pmc-care-cli` project reverse-engineers live calls to `api.pmccare.in` using the developer's own user session and OTP. Its README explicitly states that **PMC does not publish API documentation** and that endpoint behavior was derived from observed authenticated requests.

The CLI demonstrates that the live system exposes:

- complaint category/subcategory taxonomy;
- ward/prabhag choices;
- complaint filing;
- official token numbers (example format `PC45012`);
- complaint status.

It also shows 34 main categories at the time tested, including a road/pothole category and Water Supply.

### Production decision

**Do not use the reverse-engineered API as the default production integration in this phase.**

Reasons:

- undocumented behavior can change;
- legal/terms/authorization status is not established;
- it relies on a user's PMC session/OTP;
- jurisdiction naming changes over time.

Treat it as **research evidence** that future direct integration may be technically possible if PMC provides approval or stable documentation.

### Phase-1 official handoff

CivicSense must:

1. create its own internal trackable complaint;
2. resolve ward/department/accountability;
3. offer official handoff actions controlled by the citizen;
4. allow the user to capture the PMC token number once received;
5. keep CivicSense and PMC status as separate concepts.

---

## 2.7 PuneCivicAI is a useful UX/reference pattern, not our architecture

PuneCivicAI currently provides:

- a map of unresolved/resolved complaints;
- image + AI autofill;
- GPS/map location;
- ward office / electoral ward / prabhag fields;
- WhatsApp forwarding to PMC/corporators;
- public issue tracking.

The creator describes the flow publicly as:

> submit to PuneCivicAI → complaint appears on map → user clicks forward → WhatsApp opens on the end user's device → PMC later registers it and provides a token.

This validates the usefulness of **user-controlled official handoff + token capture**.

### What CivicSense should improve

- calmer, more trustworthy visual design;
- clear separation of operational authority vs elected representative;
- visible data-source provenance;
- multi-city architecture;
- versioned jurisdiction data;
- separate CivicSense status and external-government status;
- stronger privacy rules.

---

# 3. Product principles

## 3.1 Map first, not form first

The default authenticated citizen experience should be the civic map. Reporting is a primary action, but the app must immediately show value even before a complaint is created.

## 3.2 Accountability must be explicit

Every complaint detail page should answer:

- Municipality
- Electoral ward
- Operational department
- Ward office (when verified)
- Elected representatives
- Official grievance route
- When the accountability data was last verified

## 3.3 Never imply government affiliation

Unless CivicSense later receives formal authorization, wording must clearly say:

> “CivicSense is an independent civic platform. Official complaint registration is completed through the listed government channel.”

Do not use PMC logos in a way that implies endorsement without permission.

## 3.4 Never pretend a handoff happened

An internal CivicSense complaint and an official PMC complaint are different records.

Show both explicitly:

- **CivicSense ticket:** created immediately.
- **PMC handoff:** Not forwarded / Forwarded / Token received / Unknown / Resolved.

## 3.5 AI assists, never blocks

Existing AI/category suggestion behavior can remain optional. If AI fails, manual category selection must continue to work.

---

# 4. Multi-city India model

![Multi-city model](../assets/city_expansion.png)

## 4.1 Global hierarchy

For now:

- Country: **India** (fixed in UI, architecture allows future country field)
- City: user-selectable

Initial city records:

| City | State/UT | Status | Functionality |
|---|---|---|---|
| Pune | Maharashtra | `active` | Full ward map, reporting, routing, accountability |
| Mumbai | Maharashtra | `preview` | Same map shell, city centered, “Coming soon” |
| Bengaluru | Karnataka | `preview` | Same map shell, city centered, “Coming soon” |
| Hyderabad | Telangana | `preview` | Same map shell, city centered, “Coming soon” |
| Delhi | NCT of Delhi | `preview` | Same map shell, city centered, “Coming soon” |
| Chennai | Tamil Nadu | `preview` | Same map shell, city centered, “Coming soon” |

### Preview behavior

A preview city should:

- update the city name in the shell;
- recenter Google Maps;
- use the same visual layout;
- optionally load a non-authoritative/preview outline only if source and license are stored;
- show a visible **“Coming soon — verified ward and routing data is not yet active”** notice;
- disable complaint submission for that city unless explicit future support is implemented;
- never fabricate officials/departments.

Do **not** build waitlists, notifications, city voting or marketing flows unless explicitly requested.

## 4.2 City configuration is data, not conditionals

Do not scatter code like:

```ts
if (city === "Pune") { ... }
```

Instead, use a city object/config returned by the API:

```json
{
  "slug": "pune",
  "name": "Pune",
  "state": "Maharashtra",
  "country": "India",
  "status": "active",
  "center": { "lat": 18.5204, "lng": 73.8567 },
  "defaultZoom": 11,
  "municipalityName": "Pune Municipal Corporation",
  "supportsReporting": true,
  "supportsWardMap": true,
  "supportsAccountability": true
}
```

For a preview city, these support flags are false.

---

# 5. Target information architecture

## 5.1 Citizen-facing routes

Preserve existing route semantics where practical; do not churn URLs without need.

Recommended target pages:

- `/` — map-first city home
- `/complaints` — filtered/list view of public issues
- `/complaints/new` — report issue flow
- `/complaints/[id]` — complaint details
- `/my-complaints` — citizen's complaints
- `/wards/[wardId]` — optional ward view if it naturally fits existing routing
- `/dashboard` — only keep if it has a meaningful citizen dashboard; otherwise map home is primary

## 5.2 Role routes

Existing officer/admin modules should continue to work:

- officer queue/dashboard
- complaint status update
- admin stats
- admin role management

Redesign them visually after the citizen map/routing experience is stable; do not block the core redesign on admin cosmetics.

---

# 6. Home experience — exact UX direction

![Desktop map-first wireframe](../assets/desktop_home_wireframe.png)

![Mobile map-first wireframe](../assets/mobile_home_wireframe.png)

These are layout references, not pixel-perfect assets to copy literally.

## 6.1 Header

Desktop:

- CivicSense wordmark
- Country selector: India (can look selectable but only one country now)
- City selector
  - Pune — Active
  - other cities — Coming soon
- primary button: **Report an issue**
- user avatar/menu

Mobile:

- CivicSense
- compact city selector
- avatar
- Report action as a floating/bottom-sheet CTA

## 6.2 Hero copy

Suggested:

**What’s happening around Pune?**  
Explore civic issues by ward, track progress, and see who is responsible.

When a preview city is selected:

**CivicSense for Mumbai is coming soon**  
You can explore the city map now. Verified wards, reporting and official routing will be enabled after the city dataset is validated.

## 6.3 Summary metrics

Show small, calm metrics:

- Open
- In progress
- Resolved

Do not manufacture numbers. Query actual CivicSense complaint counts for the selected city.

## 6.4 Map

Pune map features:

- Google base map
- 41 electoral ward polygons
- complaint markers/pins
- marker clustering at lower zoom
- ward hover/focus style
- ward click selection
- status filter
- category filter if clean enough
- search locality/landmark
- current location control
- selected ward statistics

### Polygon behavior

Default:
- low-opacity neutral fill
- fine slate border

Hover:
- slightly stronger border/fill
- tooltip with ward number/name

Selected:
- civic blue stroke
- subtle blue fill

Do not color all 41 wards with rainbow colors.

### Marker behavior

Status semantics:

- submitted/open: blue
- in progress: amber
- resolved: green
- closed: neutral slate

Do not encode status only by color; tooltip/list/status text must also state it.

## 6.5 Right panel / mobile bottom sheet

When nothing is selected:
- Nearby issues or city issues

When a ward is selected:
- ward name/number
- open/in-progress/resolved counts
- compact “Who is responsible?” summary
- issue cards for that ward

Mobile uses a draggable-looking bottom sheet pattern, but it does not need a complex gesture library in the first implementation. A fixed responsive sheet/section is acceptable if it feels polished.

---

# 7. Complaint cards

Each public card should show only safe public information:

- thumbnail
- auto/generated or user-edited title
- category
- status
- created time/date
- approximate area / ward
- resolution state

It must **not** show:

- reporter name
- reporter email/phone
- exact street address if sensitive
- exact latitude/longitude
- internal officer notes
- Clerk user ID

Click opens complaint details.

---

# 8. Complaint creation — preserve logic, redesign experience

Existing flow can remain conceptually:

1. Location
2. Photo
3. Category
4. Description
5. Review
6. Submit

Do not rewrite the entire form engine unless the current code is genuinely obstructive.

## 8.1 Global city context

The complaint inherits the currently selected city.

For Pune:
- reporting enabled.

For preview cities:
- reporting disabled with a clear explanation.

## 8.2 Location step

For Pune:

- location search / Google Places if already configured;
- map pin;
- “Use my location”;
- address preview;
- after the pin is selected, call the backend accountability/jurisdiction resolver.

Show:

> “We found your Pune ward and will use it to route the issue. You can verify the location before continuing.”

The server, not the browser, is authoritative for ward/department IDs.

## 8.3 Photo step

- at least one photo required, preserving existing rule;
- Cloudinary stays;
- show clean preview/remove/replace;
- no new storage provider.

## 8.4 Category step

For now, retain the existing CivicSense categories if they are already used throughout the app.

Add a mapping layer to PMC departments rather than replacing the entire complaint taxonomy immediately.

Later, the live PMC CARE category taxonomy can be mapped/imported after legal/technical approval.

## 8.5 Review step

This is where the redesign becomes meaningfully better.

Review must show:

### Your report
- title
- category
- description
- photo(s)
- approximate location

### Jurisdiction
- Pune Municipal Corporation
- Electoral Ward
- Administrative Ward Office if verified

### Who is responsible?
- Operational department
- Local ward office if verified
- Elected ward representatives

### What happens after submission?
1. CivicSense ticket is created.
2. You can forward the report through an official PMC channel.
3. If PMC sends you a token number, add it to CivicSense to track the official reference alongside your CivicSense ticket.

---

# 9. “Who is responsible?” — exact product semantics

This section is central to V2.

## 9.1 Responsibility hierarchy

### Operational authority

This is the organization expected to act on the civic service problem.

Examples:
- Pune Municipal Corporation
- Road Department
- Water Supply Department
- Drainage Department
- Solid Waste Management

### Local administrative office

Show the ward office only when CivicSense can resolve it from verified data.

Example:
- Aundh-Baner Ward Office

If the mapping is uncertain:

> “Local ward office mapping is being verified.”

Do not guess.

### Elected representatives

Show the corporators elected from the complaint’s electoral ward.

Label clearly:

> **Elected representatives for this ward**

Do not label them “department responsible” or “assigned officer.”

### Government officer

PMC has an official **Know Your Officer** GIS portal. If officer data is later imported, store it with source and last-verified time. Until a reliable import/API is available, link to or reference the official lookup rather than scraping fragile names into permanent code.

## 9.2 Accountability card layout

Suggested card:

```
WHO IS RESPONSIBLE?

Pune Municipal Corporation
Road Department

Local office
Aundh-Baner Ward Office      [Verified 09 Sep 2026]

Electoral ward
Ward 08 — <ward name>

Elected representatives
• Name — Party
• Name — Party
• Name — Party
• Name — Party

Official route
PMC CARE                     [Open official service]

Data source
PMC / Maharashtra SEC / OpenCity
Last verified: <date>
```

Do not expose politician phone numbers unless the number is clearly public/officially sourced and the product has a source link.

---

# 10. Real Pune complaint routing — phase 1

![Pune routing flow](../assets/routing_flow.png)

## 10.1 Internal ticket first

Every successful report creates a CivicSense complaint in Supabase.

CivicSense is responsible for:
- public visibility (with privacy rules);
- status history;
- photo evidence;
- routing context;
- accountability context;
- external-token association.

## 10.2 Official handoff after submission

The detail/success page should show an **Official PMC handoff** module.

Actions, in order:

### A. Open PMC CARE

Primary official action.

- opens the official service in a new tab/app where supported;
- user remains in control;
- CivicSense can record that the handoff action was clicked, but **must not mark an official complaint as registered** merely from the click.

### B. Send via WhatsApp

Only if the official WhatsApp channel is currently enabled in routing configuration.

Use a `wa.me`-style user-initiated link from the user's device with a prefilled, concise message.

Do not send a WhatsApp message from CivicSense servers in this phase.

Suggested generated message structure:

```
Civic issue report — Pune
Category: Road / Pothole
Area: <approximate locality>
Electoral ward: <ward>
Ward office: <if verified>
Description: <short description>
CivicSense reference: <ticket id>
Public evidence link: <safe public complaint link>
```

Do not put the citizen's private data into the prefilled message unless explicitly necessary and consented.

### C. Call PMC helpline

Use a visible `tel:` action for the current official helpline.

### D. Copy summary

Copy a clean complaint summary for use in PMC CARE or another official channel.

## 10.3 External token capture

After a citizen receives a PMC token, allow:

- **Add PMC token**
- token value
- optional status URL if known
- date received

Do not assume token shape in database validation beyond safe length/characters; current observed examples use `PC...` but external formats can change.

## 10.4 Separate statuses

### CivicSense status (existing)
- `submitted`
- `in_progress`
- `resolved`
- `closed`

### External government routing status
Recommended enum:
- `not_forwarded`
- `handoff_started`
- `forwarded`
- `token_received`
- `external_in_progress`
- `external_resolved`
- `unknown`

Do not automatically infer one status from the other.

---

# 11. Technical architecture

![System architecture](../assets/system_architecture.png)

## 11.1 Continue the modular monolith

Frontend and backend remain separate deployable services but backend logic stays one FastAPI application.

### Backend domains to add

Prefer feature/domain folders only if the existing backend already follows such organization. Otherwise follow its current style.

Logical modules:

- cities
- jurisdictions
- departments
- officials
- routing
- complaints (existing)

Avoid introducing a repository pattern, CQRS, event bus, service mesh or dependency-injection framework merely for this feature.

## 11.2 Authoritative jurisdiction calculation belongs in backend

The frontend may highlight a ward visually, but complaint submission must not trust client-provided jurisdiction IDs.

Server derives:

`lat/lng + city → electoral ward → ward office mapping (if verified) → category → department`

Recommended mature spatial library:

- **Shapely** in Python for point-in-polygon.

Why not PostGIS now?

- no need to change database capability for 41 Pune polygons;
- avoids schema/extension complexity;
- easy to cache 41 geometries in process;
- migration to PostGIS remains possible if city count/geometry volume becomes large.

## 11.3 Geometry storage

Recommended V2 approach:

- normalized GeoJSON file is a versioned project data asset;
- metadata/provenance is stored in DB and/or source manifest;
- FastAPI exposes GeoJSON to frontend through a cacheable endpoint;
- backend also loads the same canonical file for resolution.

Suggested canonical location (adapt to repo after inspection):

```text
backend/app/data/cities/pune/electoral_wards_2025.geojson
backend/app/data/cities/pune/source_manifest.json
```

Do not maintain separate hand-edited geometry copies in frontend and backend.

Expose:

`GET /api/v1/cities/pune/wards/geojson`

Frontend loads that endpoint.

## 11.4 Google Maps implementation

Stay with Google Maps.

Use official **Maps JavaScript API Data Layer** to render GeoJSON polygons. It supports loading/adding GeoJSON, style functions, click/hover events and feature-level style overrides.

Use official/mature:

- `@googlemaps/markerclusterer` for complaint marker clustering.

Do not introduce Leaflet/Mapbox alongside Google Maps.

### Map loading

Use the loader already in the project if it is sound. Do not add a second Google Maps wrapper library just for convenience.

### GeoJSON requirements

- WGS84 (`EPSG:4326`)
- valid polygons/multipolygons
- stable feature ID / ward number properties
- 41 current electoral ward features for Pune

---

# 12. Proposed data model

![Data model](../assets/data_model_er.png)

The exact SQLAlchemy naming can adapt to current conventions, but the semantics below should be preserved.

## 12.1 `cities`

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| slug | string unique | `pune` |
| name | string | Pune |
| state_name | string | Maharashtra |
| state_code | string nullable | e.g. MH |
| country_code | string | IN |
| status | enum/string | `active`, `preview`, `disabled` |
| municipality_name | string nullable | Pune Municipal Corporation |
| center_lat | decimal | map center |
| center_lng | decimal | map center |
| default_zoom | decimal/int | map zoom |
| supports_reporting | bool | Pune true |
| supports_ward_map | bool | Pune true |
| supports_accountability | bool | Pune true |
| map_data_version | string nullable | e.g. `pmc-electoral-2025` |
| created_at / updated_at | timestamp | existing timestamp mixin |

## 12.2 `electoral_wards`

| Field | Type |
|---|---|
| id | UUID |
| city_id | UUID FK |
| external_code | string nullable |
| ward_no | string |
| name | string |
| geometry_feature_id | string |
| valid_from | date nullable |
| valid_to | date nullable |
| source_url | text |
| source_license | string nullable |
| verified_at | timestamp nullable |

Unique: `(city_id, ward_no, valid_to/null-active-version strategy)` according to implementation simplicity.

## 12.3 `ward_offices`

| Field | Type |
|---|---|
| id | UUID |
| city_id | UUID FK |
| code | string nullable |
| name | string |
| address | text nullable |
| phone | string nullable |
| email | string nullable |
| source_url | text |
| verified_at | timestamp nullable |

Do not seed officer/person names from stale pages as if permanent.

## 12.4 `ward_jurisdiction_mappings`

Needed because electoral and administrative structures differ and evolve.

| Field | Type |
|---|---|
| id | UUID |
| electoral_ward_id | UUID FK |
| ward_office_id | UUID FK |
| valid_from | date nullable |
| valid_to | date nullable |
| confidence | enum/string | `verified`, `official_source`, `legacy`, `manual_review` |
| source_url | text |
| verified_at | timestamp nullable |

If mapping cannot be verified, do not fabricate a row.

## 12.5 `departments`

| Field | Type |
|---|---|
| id | UUID |
| city_id | UUID FK |
| code | string |
| name | string |
| description | text nullable |
| source_url | text nullable |
| verified_at | timestamp nullable |

## 12.6 `category_routing_rules`

Map the existing CivicSense category to the operational department.

| Field | Type |
|---|---|
| id | UUID |
| city_id | UUID |
| category_id | UUID |
| department_id | UUID |
| priority | int default 100 |
| source_url | text nullable |
| verified_at | timestamp nullable |

One category may later have multiple routing rules if needed, but do not implement a rules engine now.

## 12.7 `public_officials`

| Field | Type |
|---|---|
| id | UUID |
| city_id | UUID |
| role_type | enum/string | `corporator`, `ward_officer`, `department_officer` |
| name | string |
| party | string nullable |
| public_phone | string nullable |
| public_email | string nullable |
| valid_from | date nullable |
| valid_to | date nullable |
| source_url | text |
| verified_at | timestamp nullable |

## 12.8 `official_jurisdictions`

Associates an official with an electoral ward, ward office or department without forcing all role types into one FK.

Keep implementation simple: nullable FKs are acceptable here.

## 12.9 `routing_channels`

| Field | Type |
|---|---|
| id | UUID |
| city_id | UUID |
| department_id | UUID nullable |
| ward_office_id | UUID nullable |
| type | enum/string | `official_portal`, `whatsapp`, `phone`, `email`, `api`, `manual` |
| label | string |
| endpoint_value | text |
| is_official | bool |
| requires_user_action | bool |
| status | enum/string | `active`, `inactive`, `experimental` |
| source_url | text |
| verified_at | timestamp |

## 12.10 Complaint additions

Extend the existing complaint rather than replacing it.

Add nullable fields first for migration safety:

- `city_id`
- `electoral_ward_id`
- `ward_office_id`
- `department_id`

Backfill existing Pune complaints as feasible.

The backend computes these during create/update-location flows.

## 12.11 `external_submissions`

| Field | Type |
|---|---|
| id | UUID |
| complaint_id | UUID FK |
| routing_channel_id | UUID nullable |
| provider | string | `pmc_care` |
| status | string/enum |
| external_token | string nullable |
| status_url | text nullable |
| forwarded_at | timestamp nullable |
| token_received_at | timestamp nullable |
| last_checked_at | timestamp nullable |
| created_at / updated_at | timestamp |

Do not store PMC passwords/OTP/session tokens.

---

# 13. API additions

Keep `/api/v1`.

## 13.1 Cities

### `GET /api/v1/cities`

Public.

Returns active + preview cities and capability flags.

### `GET /api/v1/cities/{slug}`

Public.

Returns city metadata/capabilities.

## 13.2 Ward map

### `GET /api/v1/cities/{slug}/wards/geojson`

Public, cacheable.

For Pune returns current electoral ward FeatureCollection.

For preview city:
- 404/empty with explicit capability false is acceptable; frontend should not treat as failure if `supports_ward_map=false`.

### `GET /api/v1/cities/{slug}/wards`

Public.

Metadata/stats without geometry.

## 13.3 Accountability resolver

### `GET /api/v1/cities/{slug}/accountability?lat={lat}&lng={lng}&category_id={uuid}`

Public or signed-in depending existing policy. It does not expose private user data.

Example response:

```json
{
  "city": {
    "slug": "pune",
    "name": "Pune",
    "municipality_name": "Pune Municipal Corporation"
  },
  "electoral_ward": {
    "id": "...",
    "ward_no": "23",
    "name": "...",
    "source_url": "...",
    "verified_at": "2026-09-..."
  },
  "ward_office": {
    "id": "...",
    "name": "...",
    "confidence": "verified",
    "source_url": "...",
    "verified_at": "..."
  },
  "department": {
    "id": "...",
    "name": "Road Department"
  },
  "elected_representatives": [
    {
      "name": "...",
      "party": "...",
      "source_url": "..."
    }
  ],
  "routing_channels": [
    {
      "type": "official_portal",
      "label": "PMC CARE",
      "is_official": true,
      "requires_user_action": true
    }
  ],
  "warnings": []
}
```

If an administrative mapping is uncertain, return `ward_office: null` plus a warning instead of guessing.

## 13.4 Complaint creation

Keep existing create endpoint.

The request may provide location/category, but server resolves and persists jurisdiction IDs.

The response should include the accountability summary to avoid an unnecessary immediate refetch if convenient.

## 13.5 Official handoff tracking

Recommended minimal endpoints:

- `POST /api/v1/complaints/{id}/external-submissions`
- `PATCH /api/v1/complaints/{id}/external-submissions/{externalId}`

Use these to record user-initiated handoff and token capture.

Do not overbuild external polling.

---

# 14. Backend services

## 14.1 `JurisdictionResolver`

Responsibilities:

- load/cached current city geometry;
- validate point belongs to supported city polygon/ward;
- return electoral ward;
- resolve verified ward-office mapping if available.

Implementation:

- Shapely `Point`
- parsed polygons loaded once and cached by city/version
- no database query per polygon

Failure behavior:

- point outside supported boundary → structured `outside_service_area` result / 422 where appropriate;
- geometry unavailable → degrade gracefully; complaint creation should only proceed if product policy allows; for Pune V2, geometry is a required dataset.

## 14.2 `AccountabilityService`

Input:
- city
- lat/lng
- category

Output:
- municipality
- electoral ward
- ward office if verified
- department
- elected reps
- routing channels
- provenance/warnings

## 14.3 `RoutingMessageService`

Generates a concise prefilled official-handoff message.

Do not call an LLM for this. Deterministic template is safer and cheaper.

---

# 15. Data ingestion and provenance

## 15.1 Source tiers

### Tier A — official

Use as authoritative where applicable:
- Pune Municipal Corporation / PMC Open Data
- Maharashtra State Election Commission
- MeitY / Government of India
- official Google Maps docs for implementation behavior

### Tier B — curated dataset with explicit provenance/license

Examples:
- OpenCity datasets that state source and license

Can be used in production with source metadata and validation.

### Tier C — community/reverse-engineered/reference

Examples:
- DataMeet manually traced historical geometry
- `pmc-care-cli`
- PuneCivicAI and Reddit descriptions

Use to understand workflows or fill explicitly labelled fallback data, not as silent authoritative truth.

## 15.2 Mandatory provenance fields

Every imported ward/official/routing record should retain:

- `source_url`
- `source_name`
- `source_tier`
- `source_license` where relevant
- `source_data_date` if known
- `verified_at`
- optional `notes`

A future maintainer should be able to answer “Where did this value come from?” without reading Git history.

## 15.3 Data scripts

Add small, purposeful scripts under the existing scripts convention, e.g.:

- validate normalized ward GeoJSON
- seed/import city configuration
- import 2026 elected representatives CSV
- validate routing configuration

Do not make production startup scrape the web.

---

# 16. Pune data package target

A successful Pune data package should contain:

1. city record
2. current 41 electoral ward records
3. normalized current electoral ward GeoJSON
4. 15 current administrative ward-office records
5. verified electoral→ward-office mappings where available
6. current 2026 corporators linked to wards
7. core PMC departments relevant to CivicSense categories
8. CivicSense category→PMC department mapping
9. current official routing channels
10. provenance/source manifest

### Important

If item 5 cannot be fully verified in the first pass, **ship partial verified mappings** and show a graceful “local office mapping being verified” state. Accuracy is more important than appearing complete.

---

# 17. Visual design system

The desired feeling is:

**trustworthy, civic, modern, clean, calm, professional, map-centric.**

Not:

- neon
- gamified
- crypto-dashboard-like
- overly patriotic
- bureaucratic form portal
- generic shadcn default demo

## 17.1 Typography

Use existing project font if already deliberate. Otherwise prefer **Geist** (native fit with Next.js ecosystem) or Inter.

Suggested hierarchy:

- page title: 28–34px desktop / 24–28 mobile, semibold/bold
- section title: 18–22px
- card title: 14–16px semibold
- body: 14–16px
- metadata: 12–14px

## 17.2 Color tokens

Suggested starting values; implement as CSS variables/theme tokens, not scattered raw values:

```css
--cs-bg: #F7F8FA;
--cs-surface: #FFFFFF;
--cs-text: #0F172A;
--cs-muted: #64748B;
--cs-border: #E2E8F0;
--cs-navy: #0F2E4E;
--cs-primary: #2563EB;
--cs-primary-soft: #EFF6FF;
--cs-success: #15803D;
--cs-success-soft: #F0FDF4;
--cs-warning: #D97706;
--cs-warning-soft: #FFFBEB;
--cs-danger: #DC2626;
```

Use existing Tailwind tokens if they can represent these cleanly.

## 17.3 Surfaces

- 12–16px radius
- 1px borders
- minimal shadow
- generous spacing
- no strong gradients

## 17.4 Icons

Use the icon library already in the project (likely Lucide via shadcn). Do not add a second icon system.

## 17.5 Motion

Keep subtle:
- 150–200ms hover/focus transitions
- map selection transitions
- skeleton/loading states

Do not add a large animation library solely for this redesign.

---

# 18. Complaint detail page target

Recommended hierarchy:

1. Back / breadcrumb
2. status + title
3. image gallery
4. complaint metadata (category, created, approximate location)
5. map snippet with approximate location / ward
6. **Who is responsible?** card
7. **Official PMC handoff** card
8. timeline/status history
9. resolution evidence if present

For public viewers, exact pin/address remains hidden or appropriately approximated.

For owner/officer, full location can be shown according to existing authorization logic.

---

# 19. Officer/admin impact

Do not rewrite these first.

After citizen-facing V2 is stable:

### Officer dashboard additions
- city filter
- electoral ward filter
- ward office filter
- department filter
- external token indicator

### Admin additions
- city configuration visibility
- routing data health (stale/unverified source count)
- possibly a minimal data-verification admin later

Do not build a full CMS for city data in V2 unless explicitly requested.

---

# 20. Privacy and safety requirements

CivicSense handles personal data and precise location. India’s DPDP framework makes data minimization and clear notice important product requirements.

## 20.1 Public/private boundary

### Public
- complaint title
- category
- status
- created time/date
- approximate locality/ward
- safe thumbnail
- timeline events safe for public view

### Private / owner + authorized officers
- exact address
- exact lat/lng
- user identity
- email/phone
- internal notes
- Clerk identifiers

## 20.2 Consent / notice

Before first complaint submission, provide a concise, standalone notice explaining:

- location is collected to determine jurisdiction and route the report;
- photo/description are used to document the civic issue;
- public complaint pages hide direct personal identity and precise coordinates;
- official handoff may send selected complaint details to the government channel chosen by the user.

Do not bury this only in a generic privacy policy.

## 20.3 Image privacy

Cloudinary stays. Consider stripping unnecessary EXIF metadata during upload/transformation if not already done, especially GPS EXIF. The canonical complaint location must come from the explicit location step, not hidden photo metadata.

## 20.4 Logs

Never log:
- Clerk secrets
- Cloudinary secrets
- database passwords
- auth tokens
- PMC OTP/session tokens

---

# 21. Accessibility

Minimum requirements:

- keyboard-accessible city selector, filters and report button;
- visible focus states;
- sufficient contrast;
- map cannot be the only way to access complaints — right/list panel is required;
- native buttons and labels for custom map controls;
- status is represented with text, not only color;
- image alt text or meaningful fallback;
- mobile target sizes around 44px.

Google Maps official guidance recommends native HTML elements and ARIA/title/labels for custom controls.

---

# 22. Performance

Do not over-optimize prematurely, but follow these boundaries:

- cache ward GeoJSON response with sensible HTTP cache headers;
- load geometry once per city selection, not on every map movement;
- cluster complaint markers;
- paginate complaint feed API;
- lazy-load noncritical images;
- use thumbnail transformations from Cloudinary for map/feed cards;
- avoid sending full complaint descriptions for thousands of markers.

Recommended map-feed API representation should include only fields needed for pins/cards.

---

# 23. Error and empty states

Every map-dependent screen needs intentional states:

### Google Maps key missing
Development only: clear configuration message.  
Production: should be caught before release; do not expose developer `.env` instructions to ordinary users.

### Unsupported city
Show preview state.

### Location outside Pune PMC boundary

> “This location is outside the currently supported Pune Municipal Corporation area. CivicSense reporting for this area is not active yet.”

### Ward cannot be resolved

Allow location adjustment. Do not guess.

### Ward office mapping unavailable

Still show:
- municipality
- electoral ward
- department
- elected representatives

and mark local office as “being verified.”

---

# 24. Deployment remains unchanged

## Frontend — Vercel

Continue with current deployment. Ensure only required production env variables remain.

## Backend — Railway

Continue with current FastAPI Docker deployment.

## Database — Supabase

Alembic migrations target the same production Postgres.

## Auth — Clerk

Keep the simplified production auth path. Social OAuth is not a prerequisite for this redesign.

## Images — Cloudinary

No change.

## Maps — Google Maps

No provider migration. The map UX becomes richer through GeoJSON/Data Layer and clustering.

---

# 25. Migration strategy — protect the existing MVP

1. Add new tables first.
2. Add complaint FKs as nullable.
3. Seed cities and Pune governance data.
4. Introduce new read endpoints.
5. Build new frontend shell/map against the new endpoints.
6. Update complaint creation to persist derived jurisdiction.
7. Backfill existing Pune complaints where possible.
8. Only after verification, make any field non-null if truly necessary.

Do not drop existing complaint/status tables.

---

# 26. Definition of done for CivicSense V2 Pune core

The core redesign is complete when all of the following work in production:

### City experience
- India shown as country.
- Pune is active.
- Mumbai/Bengaluru/Hyderabad/Delhi/Chennai are preview cities.
- preview selection changes map context without pretending reporting works.

### Pune map
- current 41 electoral ward polygons render.
- ward click/hover works.
- complaint pins render and cluster.
- status filtering works.
- selected ward filters the issue list.

### Reporting
- citizen can report in Pune with photo/location/category/description.
- backend computes electoral ward.
- backend maps to department.
- ward office is shown only when verified.
- complaint appears on map/feed.

### Accountability
- complaint shows municipality.
- department shown.
- electoral ward shown.
- 2026 elected corporators shown from sourced data.
- source and last-verified context available.

### Official handoff
- user can open official PMC CARE.
- current configured official channels are displayed.
- WhatsApp action is user-initiated if enabled.
- PMC token can be attached later.
- CivicSense status and PMC/external status remain distinct.

### Privacy
- public APIs/UI do not leak exact coordinates/address/user PII.

### Infrastructure
- Vercel/Railway/Supabase/Clerk/Cloudinary/Google Maps unchanged.

---

# 27. Explicit non-goals for this phase

Do not implement yet unless separately approved:

- direct undocumented PMC API submission;
- automated PMC OTP handling;
- scraping officer names every request;
- WhatsApp Business API/server messaging;
- native mobile app;
- microservices;
- Kafka/Redis;
- live WebSockets;
- nationwide ward ingestion all at once;
- AI duplicate detection;
- predictive hotspots;
- citizen reputation;
- public voting/upvotes;
- complex SLA/escalation engine;
- public politician contact scraping;
- map provider migration.

---

# 28. Research source register

**Accessed/reviewed:** 13 September 2026.

## Tier A — official / primary

1. Pune Municipal Corporation Open Data — PMC CARE booklet  
   https://opendata.pmc.gov.in/opendata/PMCReports/PMC-CARE-Booklet.pdf  
   Relevant: PMC CARE concept; SMS/WhatsApp number documented as 9689900002.

2. PMC Open Data — Departments / helpline  
   https://opendata.pmc.gov.in/departments  
   Relevant: official PMC helpline 1800-103-0222; department portal.

3. PMC eFAQ  
   https://efaq.pmc.gov.in/en  
   Relevant: PMC main contact 020-25501000, info@punecorporation.org, links to PMC CARE 2.0.

4. PMC Environmental Status Report 2024-25  
   https://opendata.pmc.gov.in/opendata/PMCReports/ESR_2024-25.pdf  
   Relevant: current PMC ward-office naming; report table lists 15 ward offices. Treat boundary assignments separately from office names.

5. PMC CARE Google Play listing  
   https://play.google.com/store/apps/details?id=in.gov.pmc.pmccare  
   Relevant: current 2026 official app, grievance redressal, location-based info, data-safety disclosure.

6. PMC CARE privacy policy  
   https://privacy.pmccare.in/  
   Relevant: official ownership of pmccare.in and privacy context.

7. PMC “Know Your Officer” GIS  
   https://iwmsgis.pmc.gov.in/know_your_officer/index.html  
   Relevant: official officer lookup concept.

8. Maharashtra State Election Commission — municipal corporation final party position  
   https://mahasec.maharashtra.gov.in/Site/Upload/Pdf/Municipal%20Corporations%20final%20party%20wise%20position.pdf  
   Relevant: Pune 41 wards, 165 seats, 2026 results summary.

9. MeitY — Digital Personal Data Protection Rules, 2025  
   https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa?pageTitle=Digital-Personal-Data-Protection-Rules-2025  
   Relevant: final rules publication and privacy-design context.

10. MeitY — Digital Personal Data Protection Act, 2023  
   https://www.meity.gov.in/documents/act-and-policies?page=2  
   Relevant: primary Indian personal-data framework.

11. Google Maps JavaScript — Data Layer / GeoJSON  
    https://developers.google.com/maps/documentation/javascript/datalayer  
    https://developers.google.com/maps/documentation/javascript/reference/data

12. Google Maps — marker clustering  
    https://developers.google.com/maps/documentation/javascript/marker-clustering

13. Google Maps — controls/accessibility guidance  
    https://developers.google.com/maps/documentation/javascript/controls

## Tier B — curated data with source/license

14. OpenCity — PMC Wards Info  
    https://data.opencity.in/dataset/pune-wards-info  
    Relevant: Pune electoral/admin ward resources, including 2025 41-ward KML.

15. OpenCity — PMC Electoral Wards 2025 resource  
    https://data.opencity.in/dataset/pune-wards-info/resource/2badcc86-489c-4b7e-b7dd-a273ef01b798  
    Relevant: 41-ward KML, public-domain metadata, Nov 2025 update, Parisar credit.

16. OpenCity — PMC Election Results 2026  
    https://data.opencity.in/dataset/pmc-election-results-2026  
    Relevant: public-domain ward winner dataset sourced from Maharashtra election system.

17. OpenCity — 2026 winner CSV resource  
    https://data.opencity.in/dataset/pmc-election-results-2026/resource/ac74e3a3-0fce-4ce5-bcdf-b3b6271ae722  
    Fields: Ward No., Ward Name, Seat, Reservation, Elected Candidate Name, Party.

## Tier C — reference / community / reverse engineered

18. DataMeet — Municipal Spatial Data / Pune  
    https://github.com/datameet/Municipal_Spatial_Data/blob/master/Pune/Readme.md  
    Relevant: historical admin/electoral ward geometry; manual-tracing caveat; license.

19. `ForceGT/pmc-care-cli`  
    https://github.com/ForceGT/pmc-care-cli  
    Relevant: observed PMC CARE categories, ward/prabhag calls, token/status flow. **Undocumented reverse-engineered integration; not authoritative public API documentation.**

20. PuneCivicAI  
    https://www.punecivicai.in/  
    Relevant: reference UX and current independent forwarding flow.

21. PuneCivicAI creator flow discussion  
    https://www.reddit.com/r/punemeetup/comments/1t6duhr/1st_resolved_civic_complaint_through_a_project_i/  
    https://www.reddit.com/r/pune/comments/1urr3o0/just_a_reminder_you_can_report_potholes_garbage/  
    Relevant: user-device WhatsApp forwarding, later PMC token capture; community source only.

## Corroborating current reporting

22. Indian Express — PMC elections / 15 ward-office counting centres / 41 wards  
    https://indianexpress.com/article/cities/pune/pmc-elections-2026-polling-over-all-eyes-on-counting-of-votes-tomorrow-10476216/

23. Indian Express — 2026 elected general body  
    https://indianexpress.com/article/cities/pune/srinath-bhimale-pmc-standing-committee-chairperson-bjp-candidate-10539284/

24. Punekar News — PMC CARE pending complaint breakdown, September 2026  
    https://www.punekarnews.in/pmc-care-2-0-14644-citizen-complaints-pending-across-pune/  
    Relevant: current 15 ward offices/~43 departments and routing/backlog context.

---

# 29. Final instruction to Cursor

Before writing code:

1. Read this entire blueprint.
2. Read `CivicSense_V2_Cursor_Execution_Plan.md`.
3. Inspect the actual repository; do not assume old file paths from chat history are exact.
4. Report any conflict between this blueprint and current code.
5. Implement **only the requested slice** from the execution plan.
6. Keep infrastructure unchanged.
7. Never fabricate civic/government data to make a screen look complete.

