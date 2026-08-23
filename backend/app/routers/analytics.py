from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    AnalyticsByCountry,
    AnalyticsByDepartment,
    AnalyticsByLevel,
    AnalyticsSummary,
)
from app.services import analytics as analytics_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummary)
def analytics_summary(
    db: Annotated[Session, Depends(get_db)],
    status: Annotated[str, Query()] = "active",
) -> AnalyticsSummary:
    return analytics_service.get_summary(db, status)


@router.get("/by-country", response_model=list[AnalyticsByCountry])
def analytics_by_country(
    db: Annotated[Session, Depends(get_db)],
    status: Annotated[str, Query()] = "active",
) -> list[AnalyticsByCountry]:
    return analytics_service.by_country(db, status)


@router.get("/by-department", response_model=list[AnalyticsByDepartment])
def analytics_by_department(
    db: Annotated[Session, Depends(get_db)],
    status: Annotated[str, Query()] = "active",
) -> list[AnalyticsByDepartment]:
    return analytics_service.by_department(db, status)


@router.get("/by-level", response_model=list[AnalyticsByLevel])
def analytics_by_level(
    db: Annotated[Session, Depends(get_db)],
    status: Annotated[str, Query()] = "active",
) -> list[AnalyticsByLevel]:
    return analytics_service.by_level(db, status)
