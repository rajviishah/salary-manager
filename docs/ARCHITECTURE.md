# Architecture

Single FastAPI process, SQLite file, React (Vite + Ant Design) UI.

**Local development.** Two processes: `uvicorn` on `:8000` and Vite on `:5173`. Vite proxies `/api` and `/health` to the API. CORS defaults to `http://localhost:5173`.

**Production (Docker / Render).** One web service. Multi-stage image builds `frontend/dist`, then runs uvicorn. FastAPI serves the SPA when `index.html` is present (`STATIC_DIR` or auto-detected `frontend/dist`). The browser calls same-origin `/api/...` and `/health` (no `localhost:8000` in the client).

**Data.** `employees` (one current `salaries` row each) and `fx_rates` for USD conversion. Tables via `Base.metadata.create_all` on startup (no Alembic). Analytics are SQL aggregations with `amount * usd_rate`. Employee list is paginated in SQL (default 25, max 100).

**Startup seed.** If the employee table is empty, the API imports `scripts.seed` and loads 10k rows. Existing rows are left alone.
