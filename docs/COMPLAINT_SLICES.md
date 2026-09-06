# Complaint Module — Vertical Slices

Build and verify each slice before starting the next.

| # | Slice | Status |
|---|--------|--------|
| 1 | Database model + migration + seed | ✅ Code done — verify with live `.env` |
| 2 | API (read endpoints) | ✅ Done |
| 3 | Backend validation + create endpoint | ✅ Done |
| 4 | Frontend wizard shell + form state | ✅ Done |
| 5 | Map picker step | ✅ Done |
| 6 | Image upload step | ✅ Done |
| 7 | Review page | ✅ Done |
| 8 | Submit + feed redirect | ✅ Done |
| 9 | Complaint detail + status timeline | ✅ Done |
| 10 | Officer queue + status updates | ✅ Done |
| 11 | Admin stats + role management | ✅ Done |
| 12 | Production deployment setup | ✅ Done |

## Slice 1 — Verify (Windows PowerShell)

From the project root:

```powershell
# 1. Go to project root (adjust path if needed)
Set-Location "C:\Users\govindat\Desktop\PROJECTS FOR LEARNING\Pune Civilian App\civicsense_platform"

# 2. Create .env from example (skip if .env already exists)
Copy-Item .env.example .env

# 3. Edit .env — fill DATABASE_URL, Clerk keys, etc.
notepad .env

# 4. Run migrations + verify from backend folder
Set-Location backend
py -m alembic upgrade head
py scripts/verify_db.py --live
```

Expected: 3 tables, 7 Pune categories.

### PowerShell notes

- Use `;` to chain commands, **not** `&&` (older PowerShell versions).
- Use `py` (Python launcher) or `python` — whichever works on your machine.
- `.env` lives in the **project root** (`civicsense_platform\.env`), not inside `backend\`.
- Supabase `DATABASE_URL` must include SSL: `?sslmode=require` at the end.

## Foundation checks (run before Slice 3)

```powershell
Set-Location backend
py -m ruff check app scripts
py -m ruff format app scripts --check
py scripts/verify_api.py
py scripts/verify_db.py --live
```

- `GET /api/v1/categories`
- `GET /api/v1/complaints` (public feed)
- `GET /api/v1/complaints/mine`
- `GET /api/v1/complaints/{id}`

Stop and test each endpoint in `/docs` before Slice 3.
