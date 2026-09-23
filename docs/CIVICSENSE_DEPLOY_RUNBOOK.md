# CivicSense India — Migration & Deploy Runbook (human-owned)

**Branch:** `feature/civicsense-accountability-social`  
**Alembic:** `001` → `008` → **`009`** (India social/accountability additive)

## Critical warning — Railway pre-deploy

Production backend currently has a **Railway dashboard** pre-deploy / release command:

```text
python -m alembic upgrade head
```

Repo `backend/railway.toml` start command is **uvicorn only**, but the **dashboard pre-deploy overrides** that and will apply `009` on the next deploy of this branch.

### Safe release sequence (required)

1. **Verified production backup** using `Desktop\CivicSense-Private-Backups` scripts (`VERIFY_OK`).
2. In Railway → Backend service → Settings → Deploy:
   - **Temporarily clear / disable** the pre-deploy command `python -m alembic upgrade head`
     (or replace with a no-op) so merge/deploy does **not** auto-migrate.
3. Deploy backend code **without** migrating.
4. Human reviews migration `009` + backup restore drill.
5. Manually run once (Railway shell or approved one-off), only after backup:
   `python -m alembic upgrade head`
6. Confirm `alembic_version` = `009` and smoke `/api/v1/health`.
7. Only then re-enable auto-migrate if the team explicitly wants it (optional; prefer manual).

Do **not** alter Railway from this agent. Do **not** migrate production without the verified backup.

## Isolated dry-run (already done on agent host)

Disposable local Postgres `civicsense_mig_test` (dropped after): `008 → 009` succeeded. Not Supabase.

## Production apply sequence (human)

1. Backup Supabase (private folder scripts).
2. Disable Railway auto-migrate as above.
3. Merge/deploy only after PR review + backup VERIFY_OK.
4. Manual `alembic upgrade head` once.
5. Deploy frontend.
6. Smoke: `/api/v1/health`, `/api/v1/feed?city=pune`, `/map`, signed-in report (Clerk).
7. Keep dispatch flags false (below).

## Rollback

- Prefer code rollback + leave additive schema (safe).
- Destructive `downgrade` of `009` only on clones.

## Live channels / safety flags

Production must keep:

```
ENVIRONMENT=production
CIVICSENSE_ALLOW_FAKE_ADAPTERS=false
EXTERNAL_DISPATCH_GLOBAL_ENABLED=false
```

Optional: `CLERK_ISSUER=https://<your-clerk-slug>.clerk.accounts.dev` to pin JWT issuer.

No WhatsApp/email/API send without per-route verification + citizen consent.
