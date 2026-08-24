# AI usage

Work was done in **Cursor** with an agent on incremental slices (models/seed, APIs, Employees UI, Dashboard, Docker/Render). The human reviewed SQL, pagination, tests, and Docker/Render constraints (one free web service, ephemeral SQLite, `PORT` / `0.0.0.0`).

AI drafted boilerplate (FastAPI routers, Ant Design tables, Dockerfile). Assertions, seed idempotency, and “do not re-seed if data exists” were checked by running pytest and reading the seed/analytics SQL, not by trusting the first generated patch.

Commits were meant to stay small and reviewable (schema → seed → API → UI → deploy). This environment did not create the git commit for the Docker slice.
