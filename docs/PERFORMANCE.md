# Performance

**10k employees** is the target dataset. The directory never downloads the full table: `GET /api/employees` pages in SQL (`page_size` default 25, max 100) with filters and sort on indexed columns (name, country, department, level, status, employee number).

**Analytics** (`/api/analytics/*`) run in the database: USD = `amount * fx_rates.usd_rate`, then `COUNT`/`SUM` and percentile-style aggregates grouped by country, department, or job level. The browser charts pre-aggregated rows, not 10k salary lines.

**First boot.** Empty SQLite → insert 10k employees + salaries (chunked). Local and Render cold start after a wipe often take **10–30 seconds** before `/health` succeeds. Later starts skip seed if rows exist. Render free-tier **sleep** typically comes back to an empty disk, so that cost repeats.

**SQLite concurrency.** Fine for a single uvicorn worker and a demo. Heavy write + analytics would want Postgres.
