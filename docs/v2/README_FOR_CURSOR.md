# CivicSense V2 — Start Here for Cursor

This pack is the implementation source of truth for the next CivicSense phase.

## Objective

Turn the existing functional MVP into a **map-first, multi-city civic accountability platform for India**, while keeping **Pune as the only fully functional city in this phase**.

## Non-negotiable infrastructure

Do not migrate or replace:

- Vercel — frontend
- Railway — FastAPI backend
- Supabase PostgreSQL — database
- Clerk — authentication
- Cloudinary — complaint images
- Google Maps Platform — maps
- GitHub — source control

This is a product/data/frontend expansion, not an infrastructure rewrite.

## Files Cursor must read before coding

1. `docs/CivicSense_V2_Product_Data_Technical_Blueprint.md`
   - product vision
   - research and source hierarchy
   - Pune ward/governance model
   - UX and visual system
   - data model and APIs
   - complaint routing/accountability model
   - privacy/performance/accessibility rules

2. `docs/CivicSense_V2_Cursor_Execution_Plan.md`
   - exact implementation order
   - 16 slices
   - acceptance criteria
   - ready-to-paste Cursor prompt for every slice

3. `assets/`
   - architecture diagram
   - routing flow
   - ER/data model
   - multi-city expansion model
   - desktop homepage wireframe
   - mobile homepage wireframe

## How to place this pack in the repository

Recommended target structure:

```text
civicsense-platform/
  docs/
    v2/
      CivicSense_V2_Product_Data_Technical_Blueprint.md
      CivicSense_V2_Cursor_Execution_Plan.md
      README_FOR_CURSOR.md
      assets/
        system_architecture.png
        routing_flow.png
        data_model_er.png
        city_expansion.png
        desktop_home_wireframe.png
        mobile_home_wireframe.png
```

The exact folder can change if the current repository has a stronger convention, but do not scatter these files.

## First Cursor instruction

Paste this into Cursor after adding the pack to the repository:

```text
We are beginning CivicSense V2.

Read these files completely before changing code:
- docs/v2/README_FOR_CURSOR.md
- docs/v2/CivicSense_V2_Product_Data_Technical_Blueprint.md
- docs/v2/CivicSense_V2_Cursor_Execution_Plan.md

Then inspect the actual repository and do Slice 0 ONLY from the execution plan.

Important rules:
- Do not change infrastructure providers.
- Do not rewrite working features unnecessarily.
- Do not invent government data.
- Do not use undocumented PMC APIs as a production dependency.
- Do not start Slice 1 or later in the same run.
- Preserve current auth, deployment, complaint status/history, officer and admin behavior unless the slice explicitly requires change.
- Never print secrets.

At the end, show:
1. files changed,
2. commands run and results,
3. conflicts between the current repository and the blueprint,
4. unresolved risks,
5. proposed commit message.

Stop after Slice 0 and wait for review.
```

## Development rhythm

For every slice:

1. Cursor reads the relevant blueprint + execution-plan section.
2. Cursor inspects existing code first.
3. Cursor implements only that slice.
4. Cursor runs lint/build/tests/migrations relevant to the slice.
5. Review result manually.
6. Commit.
7. Move to next slice only after approval.

## Data integrity rule

Government/civic data must be treated as data, not UI copy. Every potentially stale fact should have provenance and verification metadata.

The product must distinguish:

- **electoral ward** — political/elected-representative context;
- **administrative ward office** — service-delivery context;
- **department** — functional operational responsibility;
- **routing channel** — how the citizen can hand the complaint to the official system.

Do not collapse these into one generic "ward" field.

## Pune launch principle

Pune is active and functional.

Mumbai, Bengaluru, Hyderabad, Delhi and Chennai can appear in the city selector as **preview / coming soon** with the same visual map shell, but they must not pretend that complaint routing, ward geometry or accountability data is live until real datasets are added and verified.

## Official handoff principle

For Pune V2, CivicSense should create its own internal complaint first, then help the citizen route it to official PMC channels and capture the external PMC token later.

Do not automate an undocumented/reverse-engineered PMC CARE API in production without explicit approval and legal/technical validation.
