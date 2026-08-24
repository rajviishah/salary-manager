# ACME Salary Manager

HR tool for searching employees, updating current salary, and viewing pay insights. Product requirements are in `docs/requirements.md`.

**Current status.** SQLAlchemy models and Pydantic schemas exist for `employees`, `salaries`, and `fx_rates`. Tables are created on API startup via `Base.metadata.create_all` (no Alembic yet — deliberate for this assessment). A deterministic seed loads 10,000 employees. Employee and analytics REST APIs are available under `/api`. The Employees page is a server-paginated directory (search, country/department/level/status filters, sort). HR can add employees from the directory, then edit profile fields and current salary on the employee detail page. Dashboard charts are not built yet.

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

You must run uvicorn from `backend/` so `app.main:app` can be imported. After it prints `Uvicorn running on http://127.0.0.1:8000`, the API is at:

- http://127.0.0.1:8000 — JSON landing page (`name`, `status`, links to health and docs)
- http://127.0.0.1:8000/health — `{"status":"ok"}` (same payload at `/api/health`)
- http://127.0.0.1:8000/docs — Swagger UI (HTML, not JSON)

Optional: copy `.env.example` to `.env` to override `DATABASE_URL` or `CORS_ORIGINS`. Defaults already point at `backend/data/salary.db` and `http://localhost:5173`.

## Run the UI locally (second terminal)

Node.js 20+ is required. Keep the API running in the first terminal, then:

```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — not port 8000. Vite proxies `/api` and `/health` to `http://127.0.0.1:8000`, so the browser talks to the UI origin only.

You should see an Ant Design shell titled “ACME Salary Manager” with Dashboard and Employees links. The header badge is `API ok` when FastAPI is up (or `API down` if it is not). The Employees directory supports search, filters, and pagination against `GET /api/employees` (page size 25). Use **Add employee** to `POST /api/employees` (profile plus starting salary). Open a row or **View** to edit profile (`PATCH /api/employees/{id}`) and current salary (`PATCH /api/employees/{id}/salary`). Duplicate email or employee number shows as a conflict; unknown currency or invalid amount is shown from the API. Dashboard charts are not in the UI yet.

## API

Interactive docs: http://127.0.0.1:8000/docs (Swagger UI).

Paginated employee list (never returns all 10k rows; default `page_size` 25, max 100). Nested `salary` is included. Search `q` matches name, email, or employee number (case-insensitive). Filters are exact. Sort fields: `last_name` (default), `employee_number`, `hire_date`, `amount`; prefix `-` for descending.

```
GET /api/employees
GET /api/employees?q=EMP00001
GET /api/employees?country=India&department=Engineering&job_level=IC3&status=active
GET /api/employees?page=2&page_size=25&sort=-hire_date
GET /api/employees/1
GET /api/lookups
```

Writes: `POST /api/employees` (profile + starting salary, `201`), `PATCH /api/employees/{id}` (profile), `PATCH /api/employees/{id}/salary` (current salary). Duplicate email or employee number returns `409`. Unknown currency or non-positive amount returns `400`. Missing id returns `404`.

Filter dropdown values come from `GET /api/lookups` (`countries`, `departments`, `job_levels`, `statuses` from employees; `currencies` from `fx_rates`).

## Analytics

Pay insights in USD. Local salary is converted as `amount * fx_rates.usd_rate` (the USD value of 1 unit of that currency). Aggregations run in SQL. Default `status=active`; pass `status=inactive` to include only inactive employees.

Money fields are JSON strings (same convention as employee salary).

```
GET /api/analytics/summary
GET /api/analytics/summary?status=inactive
GET /api/analytics/by-country
GET /api/analytics/by-department
GET /api/analytics/by-level
```

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

## Tests

From `backend/` (uses a fresh in-memory SQLite per test; does not touch `data/salary.db`):

```powershell
cd backend
python -m pytest -q
```

Frontend typecheck + production bundle (from `frontend/`):

```powershell
cd frontend
npm run build
```
