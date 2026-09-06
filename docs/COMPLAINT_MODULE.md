# Complaint Module — Design Spec

Status: **Approved for Sprint 2**  
City: **Pune** (hardcoded string for MVP)

This document defines the complaint feature before implementation. All Sprint 2 work should follow this spec.

---

## 1. User flow (wizard, not a single form)

Raising a complaint is a **multi-step wizard**. The UX must support plugging in AI category suggestion later without changing the flow.

```
Home
  ↓  [Raise Complaint]
Choose Location        ← Google Maps pin + address
  ↓
Take / Upload Photo    ← 1–3 images via Cloudinary
  ↓
AI Suggests Category   ← placeholder in Sprint 2; real AI later
  ↓
User Confirms Category ← can override AI suggestion
  ↓
Description            ← title + description
  ↓
Review & Submit
  ↓
Confirmation           ← redirect to complaint detail
```

### Frontend routes (Sprint 2)

| Step | Route |
|------|-------|
| Start | `/complaints/new` → redirects to location |
| Location | `/complaints/new/location` |
| Photo | `/complaints/new/photo` |
| Category | `/complaints/new/category` |
| Description | `/complaints/new/description` |
| Review | `/complaints/new/review` |

### Wizard state

- Held in **client state** (React context or Zustand) until final submit.
- User can go **back** to any previous step; forward requires valid step data.
- **Single API call** on submit — `POST /api/v1/complaints`.
- If submit fails, wizard state is preserved so the user can retry.

### AI category (placeholder → real)

| Phase | Behaviour |
|-------|-----------|
| Sprint 2 | Backend returns a stub suggestion (e.g. first matching category or rule-based default). Store `ai_suggested_category_id` and `ai_confidence`. |
| Later | Swap stub service for vision/LLM API. Same endpoint contract, same UX step. |

The category step UI always shows: **"Suggested: Pothole (85%)"** with option to pick another category.

---

## 2. Data model

All primary keys are **UUID**. No integer IDs.

### Category

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK |
| `name` | string | e.g. "Pothole" |
| `slug` | string | unique, e.g. `pothole` |
| `is_active` | bool | hide without deleting |
| `created_at` | timestamp | |
| `updated_at` | timestamp | |

**Pune seed categories (Sprint 2):** pothole, garbage, streetlight, drainage, water_leak, illegal_construction, other.

### Complaint

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK |
| `user_id` | string | Clerk user ID |
| `title` | string | max 200 chars |
| `description` | text | required |
| `status` | enum | see §3 |
| `category_id` | UUID | FK → categories |
| `ai_suggested_category_id` | UUID, nullable | FK → categories |
| `ai_confidence` | float, nullable | 0.0–1.0 |
| `latitude` | float | required |
| `longitude` | float | required |
| `google_place_id` | string | from Maps |
| `address` | string | formatted address |
| `ward` | string, nullable | filled async via reverse geocoding |
| `city` | string | default `"Pune"` |
| `created_at` | timestamp | |
| `updated_at` | timestamp | |

### ComplaintImage

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK |
| `complaint_id` | UUID | FK → complaints |
| `cloudinary_url` | string | secure URL |
| `cloudinary_public_id` | string | for deletion |
| `sort_order` | int | 0-based display order |
| `created_at` | timestamp | |

### ComplaintStatusHistory (Sprint 3)

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | PK |
| `complaint_id` | UUID | FK |
| `status` | enum | new status |
| `note` | text, nullable | officer comment |
| `updated_by` | string | Clerk user ID |
| `created_at` | timestamp | |

### UserProfile (optional, Sprint 2+)

Users authenticate via **Clerk**. Local `user_profiles` table is optional for display names only — not required for Sprint 2 complaint creation.

---

## 3. Statuses

| Status | Meaning |
|--------|---------|
| `submitted` | Just filed by citizen |
| `in_progress` | Officer is working on it |
| `resolved` | Issue fixed |
| `closed` | Final state (auto or manual after resolved) |

### Allowed transitions

```
submitted → in_progress → resolved → closed
submitted → closed        (admin only — spam/duplicate)
```

Citizens **cannot** change status. Officers and admins can.

---

## 4. Permissions

| Action | Citizen | Officer | Admin |
|--------|---------|---------|-------|
| Create complaint | ✅ | ✅ | ✅ |
| View own complaints | ✅ | ✅ | ✅ |
| View public feed | ✅ | ✅ | ✅ |
| View full address | ❌ (area only) | ✅ | ✅ |
| View reporter identity | ❌ | ✅ | ✅ |
| Update status | ❌ | ✅ | ✅ |
| Add status note | ❌ | ✅ | ✅ |
| Edit complaint after submit | ❌ | ❌ | ❌ |
| Delete complaint | ❌ | ❌ | ✅ (soft archive) |

**Roles** come from Clerk `public_metadata.role`.

---

## 5. Edit & delete rules

### Can citizens edit after submission?

**No.** Once submitted, the complaint is immutable. This keeps the audit trail clean and prevents gaming.

If the citizen made a mistake, they file a new complaint. Sprint 4+ may add "Report duplicate" linking.

### Can citizens delete?

**No** in MVP. Only **admin** can archive/close as spam via status → `closed` with a note.

---

## 6. Officer comments

Officers do **not** get a free-form chat thread in MVP.

They add a **status note** when changing status (stored in `complaint_status_history`). Citizens see these notes on the complaint detail timeline (Sprint 3).

Example: *"Team dispatched to Sinhagad Road. Expected fix in 48h."*

---

## 7. Public vs private

| Data | Public feed | Citizen (own) | Officer / Admin |
|------|-------------|---------------|-----------------|
| Category | ✅ | ✅ | ✅ |
| Status | ✅ | ✅ | ✅ |
| Photo | ✅ | ✅ | ✅ |
| Approximate area | ✅ (ward/landmark) | ✅ | ✅ |
| Full address | ❌ | ✅ | ✅ |
| Exact lat/lng | ❌ | ✅ | ✅ |
| Reporter name | ❌ | ✅ (self) | ✅ |
| Description | ✅ (truncated in feed) | ✅ | ✅ |

Complaints appear on the **public feed immediately** after submission (no moderation queue in MVP).

---

## 8. Duplicate complaints

**MVP: no automatic deduplication.**

| Behaviour | MVP | Future |
|-----------|-----|--------|
| Block duplicate submit | ❌ | Maybe within 50m + same category + 24h |
| Show "similar nearby" | ❌ | Sprint 4+ |
| Officer merge | ❌ | Admin tool later |

Officers may manually `close` duplicates with note: *"Duplicate of #abc-123"*.

---

## 9. After submission

1. Complaint saved with `status = submitted`.
2. Images already on Cloudinary; URLs stored in `complaint_images`.
3. Complaint appears in:
   - Citizen's **My Complaints**
   - **Public feed** (Pune)
   - **Officer dashboard** (all open complaints)
4. `ward` is `null` initially; background job reverse-geocodes lat/lng → ward (post-Sprint 2).
5. User redirected to `/complaints/{id}` (Sprint 3 detail page; Sprint 2 can redirect to feed with toast).

---

## 10. API endpoints (Sprint 2)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET` | `/api/v1/categories` | optional | List active categories |
| `POST` | `/api/v1/complaints/suggest-category` | required | AI stub → category + confidence |
| `POST` | `/api/v1/complaints` | required | Create complaint |
| `GET` | `/api/v1/complaints` | optional | Public feed (paginated) |
| `GET` | `/api/v1/complaints/mine` | required | Current user's complaints |
| `GET` | `/api/v1/complaints/{id}` | optional | Detail (field visibility by role) |

Cloudinary upload: signed upload from backend or unsigned preset from frontend (TBD in Sprint 2 implementation).

---

## 11. Validation rules

- **Location:** lat/lng required; must fall within Pune bounding box (soft check, warn only).
- **Photos:** 1–3 images; max 5 MB each; jpeg/png/webp.
- **Category:** must be active category ID.
- **Description:** min 20 chars, max 2000.
- **Title:** min 5 chars, max 200 (auto-suggest from category + landmark allowed).
- **Rate limit:** max 5 complaints per user per hour.

---

## 12. Out of scope (Sprint 2)

- Push / email notifications
- Ward auto-fill (schema ready, job later)
- Real AI vision model
- Duplicate detection
- Complaint editing
- Officer assignment per ward
- Marathi i18n

---

## 13. Open questions (decide before coding)

- [ ] **Title auto-generation:** default `"Pothole near {landmark}"` or require manual title?
- [ ] **Cloudinary upload:** signed from backend vs unsigned preset on frontend?
- [ ] **Post-submit redirect:** detail page stub vs feed + success toast for Sprint 2?

*Recommendation:* auto-generate title from category + truncated address; signed upload from backend; redirect to feed with toast until Sprint 3 detail page exists.
