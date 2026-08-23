"""Pydantic v2 request/response shapes.

Money fields use Decimal in Python. On the wire they are JSON strings
(e.g. ``"75000.00"``) so clients never see IEEE-754 rounding. Requests
may send a string or a number; Pydantic coerces both to Decimal.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

Money = Annotated[
    Decimal,
    PlainSerializer(lambda value: format(value, "f"), return_type=str, when_used="json"),
]


class SalaryCreate(BaseModel):
    amount: Money = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    effective_date: date


class SalaryUpdate(BaseModel):
    amount: Money = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    effective_date: date


class SalaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    amount: Money
    currency: str
    effective_date: date
    created_at: datetime | None = None
    updated_at: datetime | None = None


class EmployeeCreate(BaseModel):
    employee_number: str = Field(max_length=32)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    email: str = Field(max_length=255)
    country: str = Field(max_length=100)
    department: str = Field(max_length=100)
    job_title: str = Field(max_length=150)
    job_level: str = Field(max_length=50)
    hire_date: date
    status: str = Field(default="active", max_length=20)
    salary: SalaryCreate


class EmployeeUpdate(BaseModel):
    employee_number: str | None = Field(default=None, max_length=32)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    country: str | None = Field(default=None, max_length=100)
    department: str | None = Field(default=None, max_length=100)
    job_title: str | None = Field(default=None, max_length=150)
    job_level: str | None = Field(default=None, max_length=50)
    hire_date: date | None = None
    status: str | None = Field(default=None, max_length=20)


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_number: str
    first_name: str
    last_name: str
    email: str
    country: str
    department: str
    job_title: str
    job_level: str
    hire_date: date
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    salary: SalaryRead | None = None


class FxRateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    currency: str
    usd_rate: Money
    as_of: date


class EmployeeListResponse(BaseModel):
    items: list[EmployeeRead]
    total: int
    page: int
    page_size: int


class LookupsRead(BaseModel):
    countries: list[str]
    departments: list[str]
    job_levels: list[str]
    statuses: list[str]
    currencies: list[str]


class CurrencyMixItem(BaseModel):
    currency: str
    headcount: int
    total_local: Money


class AnalyticsSummary(BaseModel):
    headcount: int
    total_usd: Money
    avg_usd: Money
    median_usd: Money
    p90_usd: Money
    min_usd: Money
    max_usd: Money
    currency_mix: list[CurrencyMixItem]


class AnalyticsByCountry(BaseModel):
    country: str
    headcount: int
    total_usd: Money
    avg_usd: Money
    median_usd: Money


class AnalyticsByDepartment(BaseModel):
    department: str
    headcount: int
    total_usd: Money
    avg_usd: Money
    median_usd: Money


class AnalyticsByLevel(BaseModel):
    job_level: str
    headcount: int
    total_usd: Money
    avg_usd: Money
    median_usd: Money

