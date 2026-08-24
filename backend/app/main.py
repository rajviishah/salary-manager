from contextlib import asynccontextmanager
from pathlib import Path
import logging

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import func, select, text

from app import database
from app import models as _models  # noqa: F401 — register metadata
from app.config import settings
from app.database import Base
from app.models import Employee
from app.routers import analytics, employees

logger = logging.getLogger(__name__)

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_DIR.parent
_SPA_EXCLUDED = frozenset({"health", "docs", "redoc", "openapi.json"})


def get_static_dir() -> Path | None:
    """Return the Vite build directory when index.html is present."""
    candidates: list[Path] = []
    if settings.static_dir:
        candidates.append(Path(settings.static_dir))
    candidates.extend(
        [
            _BACKEND_DIR / "app" / "static",
            _BACKEND_DIR / "frontend" / "dist",
            _REPO_ROOT / "frontend" / "dist",
        ]
    )
    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_dir() and (resolved / "index.html").is_file():
            return resolved
    return None


def _is_memory_sqlite() -> bool:
    url = str(database.engine.url)
    return ":memory:" in url or url.rstrip("/") == "sqlite://"


def _maybe_seed() -> None:
    if not settings.seed_on_startup:
        logger.info("SEED_ON_STARTUP is false; skipping seed")
        return
    if _is_memory_sqlite():
        logger.info("Skipping startup seed for in-memory SQLite")
        return
    with database.SessionLocal() as session:
        count = int(session.scalar(select(func.count()).select_from(Employee)) or 0)
    if count > 0:
        logger.info("Skipping startup seed (%s employees already present)", count)
        return
    logger.info(
        "No employees found; seeding 10,000 rows "
        "(first boot often takes 10–30 seconds)"
    )
    from scripts.seed import seed

    seed(reset=False)
    logger.info("Startup seed finished")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=database.engine)
    _maybe_seed()
    yield


app = FastAPI(title="ACME Salary Manager", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(employees.router)
app.include_router(analytics.router)


@app.exception_handler(RequestValidationError)
async def request_validation_handler(
    _request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"detail": jsonable_encoder(exc.errors())},
    )


def _health() -> dict[str, str]:
    with database.engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/health")
def health() -> dict[str, str]:
    return _health()


@app.get("/api/health")
def api_health() -> dict[str, str]:
    return _health()


@app.get("/")
def root():
    static = get_static_dir()
    if static is not None:
        return FileResponse(static / "index.html")
    return {
        "name": "ACME Salary Manager",
        "status": "ok",
        "health": "/health",
        "docs": "/docs",
    }


def _safe_static_file(static: Path, relative: str) -> Path | None:
    if not relative or relative.endswith("/"):
        return None
    candidate = (static / relative).resolve()
    try:
        candidate.relative_to(static.resolve())
    except ValueError:
        return None
    if candidate.is_file():
        return candidate
    return None


@app.get("/{full_path:path}")
def spa_fallback(full_path: str):
    if full_path.startswith("api/") or full_path == "api":
        raise HTTPException(status_code=404, detail="Not Found")
    if full_path in _SPA_EXCLUDED:
        raise HTTPException(status_code=404, detail="Not Found")
    static = get_static_dir()
    if static is None:
        raise HTTPException(status_code=404, detail="Not Found")
    existing = _safe_static_file(static, full_path)
    if existing is not None:
        return FileResponse(existing)
    return FileResponse(static / "index.html")
