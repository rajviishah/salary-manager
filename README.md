# ACME Salary Manager

HR tool for searching employees, updating current salary, and viewing pay insights. Product requirements are in `docs/requirements.md`.

**Current status.** SQLAlchemy models and Pydantic schemas exist for `employees`, `salaries`, and `fx_rates`. Tables are created on API startup via `Base.metadata.create_all` (no Alembic yet — deliberate for this assessment). A deterministic seed loads 10,000 employees. Employee APIs and the UI are next.

## Run the API locally (Windows PowerShell)

Python 3.11+ is required. Commands assume the `backend/` directory is the working directory (venv, `.env`, and the SQLite file all live there).

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

If `Activate.ps1` is blocked (`cannot be loaded because running scripts is disabled`), skip activation and call the venv Python directly:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

You can also activate from Command Prompt with `.\.venv\Scripts\activate.bat`.

You must run uvicorn from `backend/` so `app.main:app` can be imported. After it prints `Uvicorn running on http://127.0.0.1:8000`, open:

- http://127.0.0.1:8000 — JSON landing page (`name`, `status`, links to health and docs)
- http://127.0.0.1:8000/health — `{"status":"ok"}` (same payload at `/api/health`)
- http://127.0.0.1:8000/docs — Swagger UI (HTML, not JSON)

There is no frontend yet. The browser at `/` should show JSON, not a website.

Optional: copy `.env.example` to `.env` to override `DATABASE_URL` or `CORS_ORIGINS`. Defaults already point at `backend/data/salary.db` and `http://localhost:5173`.

## Seed the database

From `backend/` (same directory as the venv and SQLite file):

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m scripts.seed
```

`python scripts/seed.py` also works from `backend/`. The script adds that directory to `sys.path` so `app` imports resolve.

Expected counts after a successful seed:

- 10,000 employees (`EMP00001` … `EMP10000`), each with one current salary in local currency
- 10,000 salary rows
- 8 FX rows (`USD`, `GBP`, `EUR`, `INR`, `SGD`, `CAD`, `AUD`, `JPY`) — `usd_rate` is the USD value of 1 unit of that currency, `as_of` 2026-01-01

The seed is deterministic (`random` + Faker seeded at 42) and idempotent: if 10,000 employees already exist, it prints the counts and exits. Use `--reset` to wipe employees and salaries (not FX) and re-insert:

```powershell
.\.venv\Scripts\python.exe -m scripts.seed --reset
```

A partial database (more than 0 but fewer than 10,000 employees) is refused unless you pass `--reset`, so unique employee numbers and emails are not duplicated.

This slice is seed-only: there is still no employee API and no UI.
