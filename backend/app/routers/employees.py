from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Employee, Salary
from app.schemas import (
    EmployeeCreate,
    EmployeeListResponse,
    EmployeeRead,
    EmployeeUpdate,
    LookupsRead,
    SalaryUpdate,
)
from app.services import employees as employee_service

router = APIRouter(prefix="/api", tags=["employees"])


def _conflict_http(field: str) -> HTTPException:
    if field == "email":
        detail = "Email already exists"
    elif field == "employee_number":
        detail = "Employee number already exists"
    else:
        detail = "Email or employee_number already exists"
    return HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail=detail)


def _unknown_currency(currency: str) -> HTTPException:
    return HTTPException(
        status_code=http_status.HTTP_400_BAD_REQUEST,
        detail=f"Unknown currency: {currency}",
    )


def _not_found(employee_id: int) -> HTTPException:
    return HTTPException(
        status_code=http_status.HTTP_404_NOT_FOUND,
        detail=f"Employee {employee_id} not found",
    )


@router.get("/employees", response_model=EmployeeListResponse)
def list_employees(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str | None, Query()] = None,
    country: Annotated[str | None, Query()] = None,
    department: Annotated[str | None, Query()] = None,
    job_level: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
    sort: Annotated[str, Query()] = "last_name",
) -> EmployeeListResponse:
    filters = employee_service.employee_filters(
        q=q,
        country=country,
        department=department,
        job_level=job_level,
        status=status,
    )
    try:
        items, total = employee_service.list_employees(
            db,
            filters=filters,
            sort=sort,
            page=page,
            page_size=page_size,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return EmployeeListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/employees/{employee_id}", response_model=EmployeeRead)
def get_employee(
    employee_id: int, db: Annotated[Session, Depends(get_db)]
) -> Employee:
    employee = employee_service.get_employee(db, employee_id)
    if employee is None:
        raise _not_found(employee_id)
    return employee


@router.post(
    "/employees",
    response_model=EmployeeRead,
    status_code=http_status.HTTP_201_CREATED,
)
def create_employee(
    payload: EmployeeCreate, db: Annotated[Session, Depends(get_db)]
) -> Employee:
    if not employee_service.currency_exists(db, payload.salary.currency):
        raise _unknown_currency(payload.salary.currency)
    conflict = employee_service.find_conflict(
        db,
        email=payload.email,
        employee_number=payload.employee_number,
    )
    if conflict:
        raise _conflict_http(conflict)

    employee = Employee(
        employee_number=payload.employee_number,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        country=payload.country,
        department=payload.department,
        job_title=payload.job_title,
        job_level=payload.job_level,
        hire_date=payload.hire_date,
        status=payload.status,
    )
    db.add(employee)
    try:
        db.flush()
        db.add(
            Salary(
                employee_id=employee.id,
                amount=payload.salary.amount,
                currency=payload.salary.currency,
                effective_date=payload.salary.effective_date,
            )
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _conflict_http("email or employee_number") from None

    created = employee_service.get_employee(db, employee.id)
    assert created is not None
    return created


@router.patch("/employees/{employee_id}", response_model=EmployeeRead)
def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> Employee:
    employee = employee_service.get_employee(db, employee_id)
    if employee is None:
        raise _not_found(employee_id)

    updates = payload.model_dump(exclude_unset=True)
    conflict = employee_service.find_conflict(
        db,
        email=updates.get("email"),
        employee_number=updates.get("employee_number"),
        exclude_id=employee.id,
    )
    if conflict:
        raise _conflict_http(conflict)

    for field, value in updates.items():
        setattr(employee, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _conflict_http("email or employee_number") from None

    updated = employee_service.get_employee(db, employee_id)
    assert updated is not None
    return updated


@router.patch("/employees/{employee_id}/salary", response_model=EmployeeRead)
def update_salary(
    employee_id: int,
    payload: SalaryUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> Employee:
    employee = employee_service.get_employee(db, employee_id)
    if employee is None:
        raise _not_found(employee_id)
    if employee.salary is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Salary for employee {employee_id} not found",
        )
    if not employee_service.currency_exists(db, payload.currency):
        raise _unknown_currency(payload.currency)

    employee.salary.amount = payload.amount
    employee.salary.currency = payload.currency
    employee.salary.effective_date = payload.effective_date
    db.commit()

    updated = employee_service.get_employee(db, employee_id)
    assert updated is not None
    return updated


@router.get("/lookups", response_model=LookupsRead)
def get_lookups(db: Annotated[Session, Depends(get_db)]) -> LookupsRead:
    return LookupsRead(**employee_service.list_lookups(db))
