# CivicSense India — Migration & Deploy Runbook (human-owned)

**Branch:** `feature/civicsense-accountability-social`  
**Alembic:** `001` → `008` → **`009`** (India social/accountability additive)

## Critical warning

Railway `railway.toml` currently starts **uvicorn only**. If any Railway **pre-deploy** command runs `python -m alembic upgrade head`, merging this branch **will apply `009` to production automatically**. Review Railway service settings before merge. This build does **not** apply production migrations.

## Isolated dry-run (required before production)

```powershell
# Point at a disposable Postgres clone (NOT production)
$env:DATABASE_URL = "postgresql+psycopg://...isolated..."
Set-Location backend
py -m alembic heads          # expect: 009 (head)
py -m alembic history        # expect linear 001..009
py -m alembic upgrade head   # from empty OR from 008
py -m alembic current
```

Also verify upgrade-from-008 against a dump of production schema at `008`.

## Production apply sequence (human)

1. Backup Supabase.
2. Merge/deploy only after PR review.
3. Confirm Railway does **or does not** auto-migrate; apply `alembic upgrade head` once accordingly.
4. Deploy backend, then frontend.
5. Smoke: `/api/v1/health`, `/api/v1/feed?city=pune`, `/map`, create complaint (no live channel).
6. Keep `EXTERNAL_DISPATCH_GLOBAL_ENABLED=false` until channel matrix approved.

## Rollback

- Prefer code rollback + leave additive schema (safe).
- Destructive `downgrade` of `009` only on clones; drops many tables — not recommended on production with user data.
- Reconcile any `submission_intents` in `UNKNOWN_OUTCOME` before re-enabling dispatch.

## Live channels

All `external_channels.enabled=false` by default. Fake/TEST_ONLY adapters only in tests. No WhatsApp/email/API send without per-route verification + citizen consent.
