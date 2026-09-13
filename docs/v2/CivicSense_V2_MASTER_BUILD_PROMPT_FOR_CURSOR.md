# CivicSense V2 — MASTER BUILD PROMPT FOR CURSOR

You are now responsible for implementing CivicSense V2 end-to-end in the existing repository.

## READ FIRST — SOURCE OF TRUTH

Before changing any code, read these files completely:

- `docs/v2/README_FOR_CURSOR.md`
- `docs/v2/CivicSense_V2_Product_Data_Technical_Blueprint.md`
- `docs/v2/CivicSense_V2_Cursor_Execution_Plan.md`
- all diagrams/wireframes under `docs/v2/assets/`

The blueprint defines WHAT the product must become.
The execution plan defines HOW it must be built.
The existing repository defines WHAT already works and must be preserved.

Do not begin implementation until you have inspected the full repository and reconciled it against the V2 blueprint.

---

# PRIMARY OBJECTIVE

Transform the existing CivicSense MVP into a polished, map-first, multi-city civic accountability platform for India.

For this phase:

- Pune is the only fully functional city.
- Mumbai, Bengaluru, Hyderabad, Delhi and Chennai are visible as preview/coming-soon cities.
- Pune must have a real ward-based map experience.
- Complaints must be shown on the map.
- Users must be able to report civic issues.
- CivicSense must determine jurisdiction and show “Who is responsible?”
- CivicSense must model official routing/handoff without falsely claiming government submission.
- Existing officer/admin workflows must remain functional and be upgraded to fit V2.
- The product must feel polished, modern and credible — not like a basic scaffold.

---

# NON-NEGOTIABLE INFRASTRUCTURE

Do NOT replace or migrate these providers:

- Frontend: Vercel
- Backend: Railway
- Database: Supabase PostgreSQL
- Authentication: Clerk
- Images: Cloudinary
- Maps: Google Maps Platform
- Source control: GitHub

This is NOT an infrastructure rewrite.

---

# EXECUTION MODE

Execute the entire V2 implementation in one autonomous run.

Do NOT stop after each slice for user approval.

However, internally follow the slice order from the execution plan exactly.

For each slice:

1. inspect current code relevant to that slice,
2. implement the smallest correct change,
3. run relevant tests/checks,
4. fix failures before continuing,
5. create a logical commit if Git access is available,
6. continue automatically to the next slice.

Only stop and ask the user if you encounter a TRUE hard blocker such as:

- missing secret/API credential required to continue,
- unavailable external dataset that cannot legally or technically be replaced,
- destructive migration ambiguity that risks data loss,
- an architectural contradiction that cannot be resolved from the blueprint,
- an external platform configuration that requires manual user action.

Do NOT stop for:
- lint errors,
- TypeScript errors,
- migration errors you can fix,
- ordinary dependency issues,
- styling issues,
- test failures,
- small uncertainties that can be resolved from existing code/docs.

Fix those yourself and continue.

---

# IMPLEMENT ALL SLICES

Implement every slice in `CivicSense_V2_Cursor_Execution_Plan.md`, in order:

0. Baseline repository audit
1. Multi-city data model and seed configuration
2. Pune electoral ward data package
3. Electoral ward model, GeoJSON API and jurisdiction resolver
4. Pune ward offices + elected representatives
5. Departments, routing rules and accountability API
6. V2 visual foundation + app shell + city selector
7. Pune ward map + preview city maps
8. Complaint pins, clustering and map/feed synchronization
9. Complaint wizard V2 + server-derived jurisdiction
10. “Who is responsible?” UX and accountability integration
11. Official handoff UX + external submission tracking
12. Complaint detail page V2
13. Officer/Admin V2 upgrades
14. QA, accessibility, privacy, performance and resilience
15. Production readiness and deployment verification

If the execution-plan numbering or titles differ slightly, follow the actual document as source of truth.

---

# PRODUCT BEHAVIOR

## Multi-city

The platform should present India as the product scope.

City selector:
- Pune — ACTIVE
- Mumbai — COMING SOON
- Bengaluru — COMING SOON
- Hyderabad — COMING SOON
- Delhi — COMING SOON
- Chennai — COMING SOON

Do not hardcode city logic throughout components.
Use city configuration/data models.

Preview cities may show the same visual map shell but must not pretend that ward routing, complaints or accountability data is live.

---

# PUNE MAP EXPERIENCE

Pune is map-first.

The primary home experience should include:

- polished CivicSense header
- city selector
- summary metrics
- interactive Pune ward map
- ward polygons
- complaint pins
- clustering at lower zoom
- synchronized complaint list / side panel
- category/status filters
- selected ward state
- selected complaint state
- primary “Report Issue” CTA

Desktop:
- map + right-side complaint panel

Mobile:
- map + bottom sheet

Use the V2 wireframes as layout guidance, not as pixel-perfect constraints.

---

# GOVERNANCE MODEL — DO NOT COLLAPSE THESE

Treat these as separate concepts:

1. Electoral ward
   - political/elected representative context

2. Administrative ward office
   - PMC service-delivery context

3. Department
   - Roads, Drainage, Solid Waste, Water, etc.

4. Routing channel
   - PMC CARE / official portal / WhatsApp / phone / email / future API

Never use one generic “ward” field to represent all four.

---

# ACCOUNTABILITY

Every complaint should resolve, where data allows, into a clear “Who is responsible?” section.

Show:

- civic authority: Pune Municipal Corporation
- electoral ward
- administrative ward office when mapping is verified
- responsible department
- elected representative(s), where verified
- official citizen-routing options
- data provenance / last verified date where appropriate

Do not invent officer names or government data.

---

# COMPLAINT FLOW

Preserve the functional complaint flow but redesign it.

Recommended flow:

1. Location
2. Photo
3. Category
4. Description
5. Review
6. Submit

Important:

- city context comes from app selection
- Pune location should be resolved server-side to jurisdiction
- photo remains required if existing product rules require it
- category may be AI-assisted, but AI must never block submission
- title may be auto-generated and editable
- after submission, redirect to complaint detail page
- public feed must preserve privacy rules from blueprint

---

# OFFICIAL HANDOFF

CivicSense creates its own internal ticket first.

Then provide official handoff options.

For Pune, support the verified official channels defined in the blueprint/data package.

Possible UX:
- Open PMC CARE
- WhatsApp where valid
- Call helpline
- Email where valid
- Copy complaint summary
- record external complaint/token number later

CRITICAL:
- never claim “Submitted to PMC” unless CivicSense has evidence that a handoff happened
- do not automate undocumented/reverse-engineered PMC APIs in production
- keep CivicSense status separate from external-government routing status

---

# DATA INTEGRITY

Government/civic data must be stored as data, not buried in UI strings.

For civic datasets, include provenance metadata such as:

- source URL
- source name
- source type
- retrieved/verified date
- license where known
- notes
- active/version flags where appropriate

Source priority:

Tier A:
- official government sources

Tier B:
- reputable curated/open datasets with explicit provenance

Tier C:
- community/reference/reverse-engineered sources

Tier C must not silently become authoritative production truth.

---

# PUNE WARD DATA

Use the Pune electoral ward dataset specified in the blueprint/execution plan.

Requirements:

- normalize it into a repository-owned data package or import pipeline
- preserve source attribution
- validate geometry
- expose GeoJSON through backend API
- resolve latitude/longitude to electoral ward in backend
- handle points outside PMC boundaries
- do not trust frontend-only polygon resolution

If remote download is unavailable during implementation:
- create the ingestion/validation pipeline,
- clearly identify the missing source artifact,
- do NOT fabricate boundaries,
- continue with the rest of the product using a clearly marked fallback/demo geometry only if the blueprint explicitly permits it.

---

# BACKEND

Keep FastAPI + SQLAlchemy + Alembic.

Continue the modular monolith.

Add only the domain modules/services needed for:

- cities
- electoral wards
- ward offices
- departments
- officials
- jurisdiction resolution
- accountability
- routing
- external submissions

Prefer simple services over deep abstraction.

Authoritative jurisdiction calculation belongs in backend.

Add APIs defined in the blueprint, including:

- cities
- city details
- ward list
- ward GeoJSON
- accountability resolver
- complaint creation updates
- external handoff tracking

Preserve:
- existing complaint status history
- officer role behavior
- admin role behavior
- Clerk auth
- health endpoint

---

# DATABASE

Use UUIDs.

Use Alembic migrations.

Do not destructively rewrite existing complaint data.

Implement additive migrations where possible.

Add the V2 entities described in the blueprint, including:

- cities
- electoral_wards
- ward_offices
- ward_jurisdiction_mappings
- departments
- category_routing_rules
- public_officials
- official_jurisdictions
- routing_channels
- complaint additions
- external_submissions

Keep migrations reversible where practical.

Seed Pune and preview cities appropriately.

---

# FRONTEND

Keep:

- Next.js 15
- App Router
- React
- TypeScript
- Tailwind CSS v4
- shadcn/ui
- TanStack Query
- React Hook Form
- Zod
- Clerk

Do not rebuild auth from scratch.

Do not introduce another state-management library unless genuinely necessary.

Use feature-based organization.

Keep route files thin.

---

# VISUAL DIRECTION

The current UI is too basic. V2 must look like a credible civic-tech product.

Target feel:

- modern
- calm
- premium
- trustworthy
- civic/institutional without looking bureaucratic
- map-centric
- clean visual hierarchy
- generous whitespace
- high-quality typography
- polished cards
- subtle shadows
- restrained motion
- strong mobile experience

Avoid:
- neon/hacker aesthetic
- toy-like gradients
- dense admin-dashboard look
- excessive borders
- giant forms
- generic template appearance

Use the design tokens, typography, color and surface rules from the blueprint.

---

# MAP IMPLEMENTATION

Keep Google Maps.

Implement:

- ward GeoJSON polygons
- hover state
- selected ward state
- complaint markers
- marker clustering
- list/map synchronization
- viewport-aware behavior where appropriate
- loading/empty/error states
- graceful handling when Maps key is missing

Do not expose private exact complaint coordinates publicly if blueprint privacy rules prohibit it.

---

# PRIVACY

Public complaint data must NOT expose:

- reporter email
- phone
- private Clerk identifiers
- internal notes
- exact address where privacy rules say approximate location only
- exact coordinates where not appropriate

Owner/officer/admin views may see more based on existing authorization rules.

Do not log secrets.

Do not leak auth tokens.

---

# AUTH

Keep Clerk.

For MVP simplicity:
- email-based sign-in must work
- social login is optional
- do not make Google/GitHub OAuth a blocker
- do not require phone/SMS auth

Do not refactor working auth unless necessary for V2 routes.

---

# CLOUDINARY

Keep existing Cloudinary integration.

Use it for complaint images.

Do not replace it with Supabase Storage.

---

# TESTING

Before declaring completion:

Backend:
- run unit/integration tests
- test jurisdiction resolver
- test accountability resolver
- test auth/role restrictions
- test complaint creation
- test external submission tracking
- test migrations from current schema

Frontend:
- TypeScript passes
- lint passes
- production build passes
- critical routes render
- responsive behavior checked
- map states checked
- complaint wizard works
- city selector works
- preview cities work
- officer/admin pages still work

End-to-end smoke path:

1. open CivicSense
2. Pune selected
3. view Pune map
4. select ward / complaint
5. sign in with email
6. report complaint
7. jurisdiction is resolved
8. “Who is responsible?” appears
9. complaint appears in map/feed
10. official handoff options appear
11. officer can update status
12. admin view works

---

# DEPLOYMENT

Keep the current deployment model.

Frontend:
- Vercel

Backend:
- Railway

Database:
- Supabase

After implementation, verify:

- frontend production build
- backend deployment
- DATABASE_URL connectivity
- Alembic migrations
- Clerk production keys
- Cloudinary variables
- Google Maps key
- CORS
- production API URL
- health endpoint

Do not expose secrets in output.

---

# ENGINEERING RULES

Follow these throughout:

- KISS
- DRY
- YAGNI
- no microservices
- no Redis unless absolutely required
- no Kafka
- no WebSockets unless explicitly required
- no unnecessary design-pattern abstractions
- no placeholder folders
- no duplicate APIs
- no dead code
- no unnecessary dependencies
- prefer mature libraries over custom infrastructure
- preserve working code where possible
- delete obsolete code only after verifying it is replaced
- keep functions/components understandable
- explain non-obvious dependencies in comments/docs

---

# RESEARCH RULE

Do not fabricate civic/government facts.

If a required government fact is unavailable or ambiguous:

- leave the field nullable,
- mark the data as unverified,
- document the gap,
- continue building the rest of the system.

Do not block the entire build because one official contact or mapping cannot be verified.

---

# AUTONOMOUS DECISION POLICY

You are authorized to make normal implementation decisions without asking the user when:

- the blueprint already establishes intent,
- the decision is reversible,
- it does not change infrastructure,
- it does not invent government data,
- it does not cause destructive data loss.

When choosing between multiple valid implementations:
- choose the simplest one,
- prefer the existing project conventions,
- prefer maintained libraries,
- avoid creating additional services.

---

# END-OF-RUN REQUIREMENTS

Do not simply say “done”.

At the end, provide a structured completion report containing:

## 1. Completion status
For every slice:
- DONE
- PARTIAL
- BLOCKED

## 2. Files changed
Grouped by:
- backend
- frontend
- database/migrations
- data
- docs
- deployment/config

## 3. Database migrations
List migration IDs and what each does.

## 4. New APIs
List method + path + purpose.

## 5. Data sources used
For every Pune civic dataset:
- source
- URL
- date/version
- what it powers

## 6. Tests/checks run
Show command and result.

## 7. Remaining blockers
Only real blockers.

## 8. Manual actions required from user
Examples:
- add Maps API key
- add/rotate secrets
- run a production migration
- configure a domain

## 9. Deployment readiness
State whether:
- Vercel ready
- Railway ready
- Supabase ready
- Clerk ready
- Cloudinary ready
- Maps ready

## 10. Final smoke-test instructions
Give exact steps the user should follow to verify the product.

---

# DEFINITION OF SUCCESS

The run is successful when CivicSense is no longer a basic complaint form.

It should feel like a real civic accountability product:

- India-first
- Pune live
- multi-city-ready
- map-first
- ward-aware
- complaint-aware
- accountability-aware
- polished
- responsive
- privacy-conscious
- deployment-compatible
- grounded in real civic data
- honest about official government handoff

Begin now.

Read all V2 source-of-truth documents first, audit the current repository, then execute every implementation slice through production-readiness without waiting for intermediate approval.
