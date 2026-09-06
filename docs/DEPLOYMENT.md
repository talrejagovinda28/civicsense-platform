# CivicSense — Production Deployment

This guide covers deploying the CivicSense MVP after Sprint 4.

## Architecture

| Component | Recommended host | Notes |
|-----------|------------------|-------|
| Frontend (Next.js) | [Vercel](https://vercel.com) | Uses `output: "standalone"`; Vercel is zero-config |
| Backend (FastAPI) | [Railway](https://railway.app) or [Render](https://render.com) | Docker or `uvicorn` start command |
| Database | [Supabase](https://supabase.com) | PostgreSQL only (not Supabase Auth) |
| Auth | [Clerk](https://clerk.com) | Roles in `public_metadata.role` |
| Images | [Cloudinary](https://cloudinary.com) | Signed uploads via backend |
| Maps | Google Cloud | Maps JavaScript API + Places API |

## Pre-deploy checklist

1. Create a **production Supabase project** and run migrations:
   ```powershell
   Set-Location backend
   py -m alembic upgrade head
   ```
2. Create a **production Clerk application** (or use the same test app for staging).
3. Create a **Cloudinary folder** (e.g. `civicsense/complaints-prod`).
4. Restrict **Google Maps API key** to your production domain.
5. Set at least one Clerk user to `public_metadata.role = "admin"`.

## Environment variables

Copy `.env.example` and set every value. Production-specific notes:

| Variable | Production value |
|----------|------------------|
| `DATABASE_URL` | Supabase prod connection string with `?sslmode=require` |
| `NEXT_PUBLIC_API_URL` | `https://your-api.example.com` (no trailing slash) |
| `CORS_ORIGINS` | `https://your-app.example.com` (comma-separated if multiple) |
| `CLERK_JWKS_URL` | Production Clerk JWKS URL |
| `CLERK_SECRET_KEY` | Required for backend admin role updates |
| `CLOUDINARY_FOLDER` | Use a prod-specific folder name |

### Clerk JWT template (required for middleware role checks)

In Clerk Dashboard → **Sessions** → **Customize session token**, add:

```json
{
  "metadata": "{{user.public_metadata}}"
}
```

Without this, `/officer` and `/admin` middleware redirects may fail even when roles are set correctly.

## Deploy backend (Railway example)

1. Connect your Git repo.
2. Set root directory to `backend/`.
3. Start command:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. Add all backend env vars from `.env.example` (except `NEXT_PUBLIC_*`).
5. Run migrations once via Railway shell or locally against prod DB.

## Deploy frontend (Vercel example)

1. Import repo, set root directory to `frontend/`.
2. Add all `NEXT_PUBLIC_*` env vars plus Clerk keys Vercel needs.
3. Set `NEXT_PUBLIC_API_URL` to your deployed backend URL.
4. Deploy — Next.js is auto-detected.

Update Clerk **Allowed redirect URLs** and **Allowed origins** with your Vercel domain.

## Docker production (self-hosted)

From the project root with a filled `.env`:

```powershell
docker compose -f docker-compose.prod.yml up --build -d
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

Run migrations against your Supabase DB before first use.

## Post-deploy verification

1. `GET https://your-api/api/v1/health` → `status: ok`, `database: connected`
2. Sign in on the frontend → `/dashboard` loads user role
3. Submit a test complaint end-to-end
4. As officer → `/officer` queue works
5. As admin → `/admin` stats load and role update works

## Security notes

- Never commit `.env` or secrets.
- Use separate Supabase/Clerk/Cloudinary projects for prod vs dev.
- Restrict Google Maps and Cloudinary keys by domain/IP where possible.
- Keep `CORS_ORIGINS` limited to your frontend URL(s).
