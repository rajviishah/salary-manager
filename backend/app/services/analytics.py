"""Org-pay aggregations in SQL with USD conversion via fx_rates.

USD salary is ``amount * fx_rates.usd_rate`` (usd_rate = USD per 1 local unit).
Employees without a matching FX row are excluded (INNER JOIN).

Median: middle row(s) after ``ROW_NUMBER() OVER (ORDER BY usd)``.
p90: nearest-rank 90th percentile, ``ROUND(n * 0.9)`` clamped to ``[1, n]``.
"""

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import Integer, Select, case, cast, func, literal, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.models import Employee, FxRate, Salary
from app.schemas import (
    AnalyticsByCountry,
    AnalyticsByDepartment,
    AnalyticsByLevel,
    AnalyticsSummary,
    CurrencyMixItem,
)

_MONEY = Decimal("0.01")

# Sensible org-chart order for GET /api/analytics/by-level.
_LEVEL_ORDER = ("IC1", "IC2", "IC3", "IC4", "IC5", "IC6", "M1", "M2", "M3")


def _money(value: object) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        quantized = value
    else:
        quantized = Decimal(str(value))
    return quantized.quantize(_MONEY, rounding=ROUND_HALF_UP)


def _int(value: object) -> int:
    return int(value or 0)


def _usd_rows(status: str) -> Select[tuple]:
    """Employees × current salary × FX. Filter by employment status."""
    return (
        select(
            Employee.country,
            Employee.department,
            Employee.job_level,
            Salary.currency,
            Salary.amount,
            (Salary.amount * FxRate.usd_rate).label("usd"),
        )
        .select_from(Employee)
        .join(Salary, Salary.employee_id == Employee.id)
        .join(FxRate, FxRate.currency == Salary.currency)
        .where(Employee.status == status)
    )


def _middle_ranks(n: ColumnElement) -> tuple[ColumnElement, ColumnElement]:
    """1-based indexes of the median row(s): odd n → one row; even n → two."""
    return (
        cast((n + 1) / 2, Integer),
        cast((n + 2) / 2, Integer),
    )


def get_summary(db: Session, status: str) -> AnalyticsSummary:
    usd_rows = _usd_rows(status).cte("usd_rows")
    numbered = (
        select(
            usd_rows.c.usd,
            func.row_number().over(order_by=usd_rows.c.usd.asc()).label("rn"),
            func.count().over().label("n"),
        )
    ).cte("numbered")

    mid_lo, mid_hi = _middle_ranks(numbered.c.n)
    median_sq = (
        select(func.round(func.avg(numbered.c.usd), 2))
        .where(numbered.c.rn.in_((mid_lo, mid_hi)))
        .scalar_subquery()
    )
    p90_rank = func.max(
        1,
        func.min(
            numbered.c.n,
            cast(func.round(numbered.c.n * literal(0.9)), Integer),
        ),
    )
    p90_sq = (
        select(func.round(numbered.c.usd, 2))
        .where(numbered.c.rn == p90_rank)
        .limit(1)
        .scalar_subquery()
    )

    stats = db.execute(
        select(
            func.count().label("headcount"),
            func.round(func.sum(usd_rows.c.usd), 2).label("total_usd"),
            func.round(func.avg(usd_rows.c.usd), 2).label("avg_usd"),
            median_sq.label("median_usd"),
            p90_sq.label("p90_usd"),
            func.round(func.min(usd_rows.c.usd), 2).label("min_usd"),
            func.round(func.max(usd_rows.c.usd), 2).label("max_usd"),
        ).select_from(usd_rows)
    ).one()

    mix_rows = db.execute(
        select(
            usd_rows.c.currency,
            func.count().label("headcount"),
            func.round(func.sum(usd_rows.c.amount), 2).label("total_local"),
        )
        .group_by(usd_rows.c.currency)
        .order_by(func.count().desc(), usd_rows.c.currency.asc())
    ).all()

    return AnalyticsSummary(
        headcount=_int(stats.headcount),
        total_usd=_money(stats.total_usd),
        avg_usd=_money(stats.avg_usd),
        median_usd=_money(stats.median_usd),
        p90_usd=_money(stats.p90_usd),
        min_usd=_money(stats.min_usd),
        max_usd=_money(stats.max_usd),
        currency_mix=[
            CurrencyMixItem(
                currency=row.currency,
                headcount=_int(row.headcount),
                total_local=_money(row.total_local),
            )
            for row in mix_rows
        ],
    )


def _by_group(
    db: Session,
    status: str,
    group_col: ColumnElement[str],
    *,
    order_levels: bool = False,
) -> list[tuple]:
    usd_rows = (
        select(
            group_col.label("grp"),
            (Salary.amount * FxRate.usd_rate).label("usd"),
        )
        .select_from(Employee)
        .join(Salary, Salary.employee_id == Employee.id)
        .join(FxRate, FxRate.currency == Salary.currency)
        .where(Employee.status == status)
        .cte("usd_rows")
    )
    numbered = (
        select(
            usd_rows.c.grp,
            usd_rows.c.usd,
            func.row_number()
            .over(partition_by=usd_rows.c.grp, order_by=usd_rows.c.usd.asc())
            .label("rn"),
            func.count().over(partition_by=usd_rows.c.grp).label("n"),
        )
    ).cte("numbered")

    mid_lo, mid_hi = _middle_ranks(numbered.c.n)
    medians = (
        select(
            numbered.c.grp,
            func.round(func.avg(numbered.c.usd), 2).label("median_usd"),
        )
        .where(numbered.c.rn.in_((mid_lo, mid_hi)))
        .group_by(numbered.c.grp)
        .cte("medians")
    )

    stmt = (
        select(
            usd_rows.c.grp,
            func.count().label("headcount"),
            func.round(func.sum(usd_rows.c.usd), 2).label("total_usd"),
            func.round(func.avg(usd_rows.c.usd), 2).label("avg_usd"),
            medians.c.median_usd,
        )
        .join(medians, medians.c.grp == usd_rows.c.grp)
        .group_by(usd_rows.c.grp, medians.c.median_usd)
    )
    if order_levels:
        stmt = stmt.order_by(
            case(
                {level: index for index, level in enumerate(_LEVEL_ORDER)},
                value=usd_rows.c.grp,
                else_=len(_LEVEL_ORDER),
            ),
            usd_rows.c.grp.asc(),
        )
    else:
        stmt = stmt.order_by(func.round(func.sum(usd_rows.c.usd), 2).desc())

    return list(db.execute(stmt).all())


def by_country(db: Session, status: str) -> list[AnalyticsByCountry]:
    rows = _by_group(db, status, Employee.country)
    return [
        AnalyticsByCountry(
            country=row.grp,
            headcount=_int(row.headcount),
            total_usd=_money(row.total_usd),
            avg_usd=_money(row.avg_usd),
            median_usd=_money(row.median_usd),
        )
        for row in rows
    ]


def by_department(db: Session, status: str) -> list[AnalyticsByDepartment]:
    rows = _by_group(db, status, Employee.department)
    return [
        AnalyticsByDepartment(
            department=row.grp,
            headcount=_int(row.headcount),
            total_usd=_money(row.total_usd),
            avg_usd=_money(row.avg_usd),
            median_usd=_money(row.median_usd),
        )
        for row in rows
    ]


def by_level(db: Session, status: str) -> list[AnalyticsByLevel]:
    rows = _by_group(db, status, Employee.job_level, order_levels=True)
    return [
        AnalyticsByLevel(
            job_level=row.grp,
            headcount=_int(row.headcount),
            total_usd=_money(row.total_usd),
            avg_usd=_money(row.avg_usd),
            median_usd=_money(row.median_usd),
        )
        for row in rows
    ]
