# ACME Salary Manager

HR tool for searching employees, updating current salary, and viewing pay insights. Product requirements are in `docs/requirements.md`.

This commit is the backend scaffold: FastAPI boots against SQLite and exposes a health check. Employee APIs, seed data, analytics, frontend, Docker, and deploy config come later.

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
