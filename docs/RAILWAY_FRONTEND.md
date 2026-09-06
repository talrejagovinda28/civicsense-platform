# Deploy frontend on Railway (skip broken Vercel monorepo setup)

## 1. Add a second Railway service

1. Railway project → **+ New** → **GitHub Repo** → same `civicsense-platform` repo
2. Name it `frontend`

## 2. Variables tab — paste all of these

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

## 3. Generate public domain

Settings → Networking → **Generate Domain** for the frontend service.

## 4. Clerk

Add your new frontend `https://....up.railway.app` URL to Clerk → Allowed redirect URLs and Allowed origins.

Backend CORS already allows `*.up.railway.app` automatically.
