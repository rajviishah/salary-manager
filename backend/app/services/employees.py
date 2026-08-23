from typing import Literal

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, contains_eager, joinedload
from sqlalchemy.sql.elements import ColumnElement

from app.models import Employee, FxRate, Salary

ConflictField = Literal["email", "employee_number"]

ALLOWED_SORTS = {
    "last_name": Employee.last_name,
    "employee_number": Employee.employee_number,
    "hire_date": Employee.hire_date,
    "amount": Salary.amount,
}


def parse_sort(sort: str) -> tuple[ColumnElement, bool]:
    descending = sort.startswith("-")
    key = sort[1:] if descending else sort
    column = ALLOWED_SORTS.get(key)
    if column is None:
        allowed = ", ".join(ALLOWED_SORTS)
        raise ValueError(
            f"Invalid sort '{sort}'. Allowed: {allowed} (prefix '-' for descending)."
        )
    return column, descending


def employee_filters(
    *,
    q: str | None = None,
    country: str | None = None,
    department: str | None = None,
    job_level: str | None = None,
    status: str | None = None,
) -> list[ColumnElement[bool]]:
    filters: list[ColumnElement[bool]] = []
    if q and q.strip():
        term = f"%{q.strip().lower()}%"
        filters.append(
            or_(
                func.lower(Employee.first_name).like(term),
                func.lower(Employee.last_name).like(term),
                func.lower(Employee.first_name + " " + Employee.last_name).like(term),
                func.lower(Employee.email).like(term),
                func.lower(Employee.employee_number).like(term),
            )
        )
    if country:
        filters.append(Employee.country == country)
    if department:
        filters.append(Employee.department == department)
    if job_level:
        filters.append(Employee.job_level == job_level)
    if status:
        filters.append(Employee.status == status)
    return filters


def count_employees(db: Session, filters: list[ColumnElement[bool]]) -> int:
    stmt: Select[tuple[int]] = select(func.count()).select_from(Employee)
    if filters:
        stmt = stmt.where(*filters)
    return int(db.scalar(stmt) or 0)


def list_employees(
    db: Session,
    *,
    filters: list[ColumnElement[bool]],
    sort: str,
    page: int,
    page_size: int,
) -> tuple[list[Employee], int]:
    column, descending = parse_sort(sort)
    total = count_employees(db, filters)
    order = column.desc() if descending else column.asc()
    stmt = (
        select(Employee)
        .outerjoin(Salary, Salary.employee_id == Employee.id)
        .options(contains_eager(Employee.salary))
    )
    if filters:
        stmt = stmt.where(*filters)
    stmt = stmt.order_by(order, Employee.id.asc()).limit(page_size).offset(
        (page - 1) * page_size
    )
    items = list(db.scalars(stmt).unique().all())
    return items, total


def get_employee(db: Session, employee_id: int) -> Employee | None:
    return db.scalar(
        select(Employee)
        .options(joinedload(Employee.salary))
        .where(Employee.id == employee_id)
    )


def currency_exists(db: Session, currency: str) -> bool:
    return db.scalar(select(FxRate.id).where(FxRate.currency == currency)) is not None


def find_conflict(
    db: Session,
    *,
    email: str | None = None,
    employee_number: str | None = None,
    exclude_id: int | None = None,
) -> ConflictField | None:
    clauses: list[ColumnElement[bool]] = []
    if email is not None:
        clauses.append(Employee.email == email)
    if employee_number is not None:
        clauses.append(Employee.employee_number == employee_number)
    if not clauses:
        return None
    stmt = select(Employee).where(or_(*clauses))
    if exclude_id is not None:
        stmt = stmt.where(Employee.id != exclude_id)
    for row in db.scalars(stmt):
        if email is not None and row.email == email:
            return "email"
        if employee_number is not None and row.employee_number == employee_number:
            return "employee_number"
    return None


def list_lookups(db: Session) -> dict[str, list[str]]:
    return {
        "countries": list(
            db.scalars(select(Employee.country).distinct().order_by(Employee.country))
        ),
        "departments": list(
            db.scalars(
                select(Employee.department).distinct().order_by(Employee.department)
            )
        ),
        "job_levels": list(
            db.scalars(
                select(Employee.job_level).distinct().order_by(Employee.job_level)
            )
        ),
        "statuses": list(
            db.scalars(select(Employee.status).distinct().order_by(Employee.status))
        ),
        "currencies": list(
            db.scalars(select(FxRate.currency).order_by(FxRate.currency))
        ),
    }
