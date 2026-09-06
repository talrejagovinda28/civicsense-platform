# CivicSense Platform

Civic complaint reporting MVP for Pune.

## Windows setup (PowerShell)

### 1. Environment file

**Do not** run `New-Item .env.example` if the file already exists — it creates a zero-byte file and wipes content.

```powershell
Set-Location "C:\Users\govindat\Desktop\PROJECTS FOR LEARNING\Pune Civilian App\civicsense_platform"

# Only if .env does not exist yet:
Copy-Item .env.example .env

notepad .env
```

Replace **every placeholder** in `.env`, especially:

| Variable | Where to get it |
|----------|-----------------|
| `DATABASE_URL` | Supabase → Project Settings → Database → URI |
| `CLERK_JWKS_URL` | `https://<your-clerk-slug>.clerk.accounts.dev/.well-known/jwks.json` |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk dashboard |
| `CLERK_SECRET_KEY` | Clerk dashboard |

**Supabase `DATABASE_URL` example** (use your real project ref and password):

```
postgresql+psycopg://postgres:YOUR_REAL_PASSWORD@db.abcdefghijklmnop.supabase.co:5432/postgres?sslmode=require
```

The host must look like `db.xxxxx.supabase.co` — **not** `db.YOUR_PROJECT.supabase.co`.

If your password contains `@`, `#`, or `%`, [URL-encode](https://www.urlencoder.org/) it.

### 2. Database migration

```powershell
Set-Location backend
py -m ruff check app scripts
py scripts/verify_api.py
py -m alembic upgrade head
py scripts/verify_db.py --live
```

Expected: `Live DB OK — 7 categories seeded`

### 3. Run the app

```powershell
# Backend (from backend/)
py -m uvicorn app.main:app --reload

# Frontend (from frontend/, requires Node.js)
npm install
npm run dev
```

## Docs

- [BACKLOG.md](docs/BACKLOG.md)
- [COMPLAINT_MODULE.md](docs/COMPLAINT_MODULE.md)
- [COMPLAINT_SLICES.md](docs/COMPLAINT_SLICES.md)
- [DEPLOYMENT.md](docs/DEPLOYMENT.md)
