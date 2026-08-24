# Tradeoffs

**SQLite vs Postgres.** SQLite is zero-ops and enough for 10k rows and SQL analytics in an assessment. On Render’s free web service the filesystem is ephemeral: sleep/restart wipes the DB and the next boot re-seeds. A paid disk or Postgres would persist data; that was out of scope for a single free instance.

**One service, not two.** Free Render allows one web service here. Serving the built UI from FastAPI avoids a second static site and keeps same-origin fetch. Cost: Python serves static files (fine at demo traffic).

**No auth.** The spec is an internal HR demo. Adding login would dominate the slice without changing the salary/analytics story. Do not put real payroll on a public URL.

**No Alembic.** `create_all` matches a greenfield SQLite file. A real product would migrate.

**Seed on empty only.** Avoids duplicating unique emails/numbers after a restart that *did* keep the file (local Docker volume). Partial DBs still need `python -m scripts.seed --reset`.
