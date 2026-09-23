# Deploy frontend on Railway

## Why it crashed before

Root `railway.toml` was forcing `uvicorn` as the start command on **every**
service — that kills the Node/Next.js frontend. Fixed in latest commit.

## Frontend service — Variables tab

Paste **all** of these (use values from Clerk / Railway dashboards — never commit real secrets):

```
RAILWAY_DOCKERFILE_PATH=Dockerfile.frontend
NEXT_PUBLIC_API_URL=https://<your-backend-host>
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard
```

Do **not** set `NEXT_PUBLIC_CLERK_PROXY_URL` on Railway unless you have configured
a working Clerk Frontend API proxy for that exact host.

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
