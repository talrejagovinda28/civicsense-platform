# Deploy frontend on Railway

## Why it crashed before

Root `railway.toml` was forcing `uvicorn` as the start command on **every**
service — that kills the Node/Next.js frontend. Fixed in latest commit.

## Frontend service — Variables tab

Paste **all** of these:

```
RAILWAY_DOCKERFILE_PATH=Dockerfile.frontend
NEXT_PUBLIC_API_URL=https://civicsense-platform-production.up.railway.app
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_cmVhbC1vcmlvbGUtOTc1MS5jbGVyay5hY2NvdW50cy5kZXYk
CLERK_SECRET_KEY=sk_test_JaCoNNEplCD8s80kwFmSItaizQ9LhFWqKTh9W5M0NM
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=
```

## Backend service — add this variable too

```
RAILWAY_DOCKERFILE_PATH=Dockerfile.backend
```

## Clear wrong start command (frontend)

Settings → **Deploy** → **Custom Start Command** → leave **empty** → Save

(Railway must use `node server.js` from the Dockerfile, not uvicorn.)

## Then

1. Redeploy frontend
2. Settings → Networking → **Generate Domain**
3. Clerk → add that URL to Allowed origins + redirect URLs
