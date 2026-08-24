"""Deterministic seed of 10,000 employees, current salaries, and FX rates.

Canonical invocation (from ``backend/``):

    python -m scripts.seed
    python -m scripts.seed --reset

``python scripts/seed.py`` also works; this file adds ``backend/`` to
``sys.path`` so ``app`` imports resolve either way.

Idempotency
-----------
* If ``employees`` already has >= 10,000 rows, print the counts and exit.
  Nothing is duplicated.
* If 0 < count < 10,000, refuse (unique ``employee_number`` / email would
  collide). Pass ``--reset``.
* ``--reset`` deletes salaries and employees, then re-inserts. FX rows are
  upserted in every run and are not wiped.

Re-runs with the same seed produce the same names, dates, and amounts.
"""

from __future__ import annotations

import argparse
import random
import re
import sys
import time
from datetime import date
from decimal import Decimal
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from faker import Faker
from sqlalchemy import delete, func, select, text

from app.database import Base, SessionLocal, engine
from app.models import Employee, FxRate, Salary

SEED = 42
TARGET_EMPLOYEES = 10_000
CHUNK_SIZE = 1_000
INACTIVE_RATE = 0.07
HIRE_START = date(2016, 8, 1)
HIRE_END = date(2026, 8, 1)
FX_AS_OF = date(2026, 1, 1)

# usd_rate = USD value of 1 unit of that currency (USD = 1).
FX_RATES: dict[str, Decimal] = {
    "USD": Decimal("1.00000000"),
    "GBP": Decimal("1.27000000"),
    "EUR": Decimal("1.08000000"),
    "INR": Decimal("0.01200000"),
    "SGD": Decimal("0.74000000"),
    "CAD": Decimal("0.73000000"),
    "AUD": Decimal("0.65000000"),
    "JPY": Decimal("0.00670000"),
}

# (country, currency, weight) — ACME is multi-country, not US-only.
COUNTRIES: list[tuple[str, str, int]] = [
    ("United States", "USD", 28),
    ("India", "INR", 22),
    ("United Kingdom", "GBP", 12),
    ("Germany", "EUR", 10),
    ("Singapore", "SGD", 8),
    ("Canada", "CAD", 8),
    ("Australia", "AUD", 7),
    ("Japan", "JPY", 5),
]

DEPARTMENTS: list[tuple[str, int]] = [
    ("Engineering", 32),
    ("Sales", 14),
    ("Product", 12),
    ("Support", 10),
    ("Operations", 9),
    ("Finance", 8),
    ("Marketing", 8),
    ("HR", 7),
]

JOB_LEVELS: list[tuple[str, int]] = [
    ("IC1", 12),
    ("IC2", 18),
    ("IC3", 22),
    ("IC4", 16),
    ("IC5", 10),
    ("IC6", 6),
    ("M1", 8),
    ("M2", 5),
    ("M3", 3),
]

# Annual local-currency ranges by country × level. India IC1 << US M3.
SALARY_RANGES: dict[str, dict[str, tuple[int, int]]] = {
    "United States": {
        "IC1": (72_000, 95_000),
        "IC2": (95_000, 125_000),
        "IC3": (125_000, 165_000),
        "IC4": (165_000, 210_000),
        "IC5": (210_000, 260_000),
        "IC6": (260_000, 330_000),
        "M1": (145_000, 185_000),
        "M2": (185_000, 245_000),
        "M3": (245_000, 330_000),
    },
    "United Kingdom": {
        "IC1": (35_000, 46_000),
        "IC2": (46_000, 62_000),
        "IC3": (62_000, 82_000),
        "IC4": (82_000, 110_000),
        "IC5": (110_000, 145_000),
        "IC6": (145_000, 185_000),
        "M1": (72_000, 98_000),
        "M2": (98_000, 135_000),
        "M3": (135_000, 185_000),
    },
    "India": {
        "IC1": (1_000_000, 1_800_000),
        "IC2": (1_800_000, 2_800_000),
        "IC3": (2_800_000, 4_500_000),
        "IC4": (4_500_000, 7_000_000),
        "IC5": (7_000_000, 10_000_000),
        "IC6": (10_000_000, 14_000_000),
        "M1": (3_500_000, 5_500_000),
        "M2": (5_500_000, 9_000_000),
        "M3": (9_000_000, 15_000_000),
    },
    "Germany": {
        "IC1": (46_000, 58_000),
        "IC2": (58_000, 74_000),
        "IC3": (74_000, 95_000),
        "IC4": (95_000, 125_000),
        "IC5": (125_000, 155_000),
        "IC6": (155_000, 195_000),
        "M1": (85_000, 115_000),
        "M2": (115_000, 150_000),
        "M3": (150_000, 200_000),
    },
    "Singapore": {
        "IC1": (52_000, 72_000),
        "IC2": (72_000, 98_000),
        "IC3": (98_000, 135_000),
        "IC4": (135_000, 175_000),
        "IC5": (175_000, 225_000),
        "IC6": (225_000, 285_000),
        "M1": (115_000, 155_000),
        "M2": (155_000, 210_000),
        "M3": (210_000, 280_000),
    },
    "Canada": {
        "IC1": (62_000, 82_000),
        "IC2": (82_000, 108_000),
        "IC3": (108_000, 142_000),
        "IC4": (142_000, 185_000),
        "IC5": (185_000, 235_000),
        "IC6": (235_000, 295_000),
        "M1": (125_000, 165_000),
        "M2": (165_000, 215_000),
        "M3": (215_000, 285_000),
    },
    "Australia": {
        "IC1": (68_000, 88_000),
        "IC2": (88_000, 115_000),
        "IC3": (115_000, 150_000),
        "IC4": (150_000, 190_000),
        "IC5": (190_000, 240_000),
        "IC6": (240_000, 305_000),
        "M1": (130_000, 170_000),
        "M2": (170_000, 225_000),
        "M3": (225_000, 295_000),
    },
    "Japan": {
        "IC1": (5_000_000, 7_000_000),
        "IC2": (7_000_000, 9_000_000),
        "IC3": (9_000_000, 12_000_000),
        "IC4": (12_000_000, 15_500_000),
        "IC5": (15_500_000, 19_000_000),
        "IC6": (19_000_000, 24_000_000),
        "M1": (11_000_000, 14_500_000),
        "M2": (14_500_000, 19_000_000),
        "M3": (19_000_000, 26_000_000),
    },
}

JOB_TITLES: dict[str, dict[str, str]] = {
    "Engineering": {
        "IC1": "Junior Software Engineer",
        "IC2": "Software Engineer",
        "IC3": "Senior Software Engineer",
        "IC4": "Staff Software Engineer",
        "IC5": "Principal Software Engineer",
        "IC6": "Distinguished Engineer",
        "M1": "Engineering Manager",
        "M2": "Senior Engineering Manager",
        "M3": "Director of Engineering",
    },
    "Sales": {
        "IC1": "Sales Development Representative",
        "IC2": "Account Executive",
        "IC3": "Senior Account Executive",
        "IC4": "Enterprise Account Executive",
        "IC5": "Strategic Account Lead",
        "IC6": "Principal Sales Strategist",
        "M1": "Sales Manager",
        "M2": "Senior Sales Manager",
        "M3": "Director of Sales",
    },
    "Product": {
        "IC1": "Associate Product Manager",
        "IC2": "Product Manager",
        "IC3": "Senior Product Manager",
        "IC4": "Staff Product Manager",
        "IC5": "Principal Product Manager",
        "IC6": "Distinguished Product Lead",
        "M1": "Product Lead",
        "M2": "Group Product Manager",
        "M3": "Director of Product",
    },
    "Finance": {
        "IC1": "Junior Financial Analyst",
        "IC2": "Financial Analyst",
        "IC3": "Senior Financial Analyst",
        "IC4": "Finance Business Partner",
        "IC5": "Principal Finance Partner",
        "IC6": "Distinguished Finance Advisor",
        "M1": "Finance Manager",
        "M2": "Senior Finance Manager",
        "M3": "Director of Finance",
    },
    "HR": {
        "IC1": "HR Coordinator",
        "IC2": "HR Generalist",
        "IC3": "Senior HR Generalist",
        "IC4": "HR Business Partner",
        "IC5": "Principal HR Partner",
        "IC6": "Distinguished People Advisor",
        "M1": "HR Manager",
        "M2": "Senior HR Manager",
        "M3": "Director of People",
    },
    "Support": {
        "IC1": "Support Associate",
        "IC2": "Support Specialist",
        "IC3": "Senior Support Specialist",
        "IC4": "Support Engineer",
        "IC5": "Principal Support Engineer",
        "IC6": "Distinguished Support Advisor",
        "M1": "Support Manager",
        "M2": "Senior Support Manager",
        "M3": "Director of Support",
    },
    "Operations": {
        "IC1": "Operations Coordinator",
        "IC2": "Operations Analyst",
        "IC3": "Senior Operations Analyst",
        "IC4": "Operations Lead",
        "IC5": "Principal Operations Lead",
        "IC6": "Distinguished Operations Advisor",
        "M1": "Operations Manager",
        "M2": "Senior Operations Manager",
        "M3": "Director of Operations",
    },
    "Marketing": {
        "IC1": "Marketing Coordinator",
        "IC2": "Marketing Specialist",
        "IC3": "Senior Marketing Specialist",
        "IC4": "Marketing Lead",
        "IC5": "Principal Marketing Lead",
        "IC6": "Distinguished Marketing Advisor",
        "M1": "Marketing Manager",
        "M2": "Senior Marketing Manager",
        "M3": "Director of Marketing",
    },
}


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "", value.lower())
    return cleaned or "emp"


def _pick(rng: random.Random, items: list[tuple[str, int]]) -> str:
    names = [name for name, _ in items]
    weights = [weight for _, weight in items]
    return rng.choices(names, weights=weights, k=1)[0]


def _pick_country(rng: random.Random) -> tuple[str, str]:
    countries = [(name, currency) for name, currency, _ in COUNTRIES]
    weights = [weight for _, _, weight in COUNTRIES]
    return rng.choices(countries, weights=weights, k=1)[0]


def _salary_amount(rng: random.Random, country: str, level: str) -> Decimal:
    low, high = SALARY_RANGES[country][level]
    # Whole local-currency units, then store as Decimal(12, 2).
    amount = rng.randrange(low, high + 1)
    return Decimal(amount).quantize(Decimal("0.01"))


def _build_rows(
    rng: random.Random, fake: Faker
) -> list[tuple[Employee, Decimal, str, date]]:
    rows: list[tuple[Employee, Decimal, str, date]] = []
    for index in range(1, TARGET_EMPLOYEES + 1):
        country, currency = _pick_country(rng)
        department = _pick(rng, DEPARTMENTS)
        job_level = _pick(rng, JOB_LEVELS)
        first_name = fake.first_name()
        last_name = fake.last_name()
        hire_date = fake.date_between(start_date=HIRE_START, end_date=HIRE_END)
        effective_date = fake.date_between(start_date=hire_date, end_date=HIRE_END)
        status = "inactive" if rng.random() < INACTIVE_RATE else "active"
        employee = Employee(
            employee_number=f"EMP{index:05d}",
            first_name=first_name,
            last_name=last_name,
            email=f"{_slug(first_name)}.{_slug(last_name)}.{index:05d}@acme.example",
            country=country,
            department=department,
            job_title=JOB_TITLES[department][job_level],
            job_level=job_level,
            hire_date=hire_date,
            status=status,
        )
        amount = _salary_amount(rng, country, job_level)
        rows.append((employee, amount, currency, effective_date))
    return rows


def _count(session, model) -> int:
    return int(session.scalar(select(func.count()).select_from(model)) or 0)


def _upsert_fx(session) -> None:
    existing = {
        row.currency: row for row in session.scalars(select(FxRate)).all()
    }
    for currency, usd_rate in FX_RATES.items():
        row = existing.get(currency)
        if row is None:
            session.add(
                FxRate(currency=currency, usd_rate=usd_rate, as_of=FX_AS_OF)
            )
        else:
            row.usd_rate = usd_rate
            row.as_of = FX_AS_OF


def _wipe_employees(session) -> None:
    session.execute(delete(Salary))
    session.execute(delete(Employee))
    if engine.dialect.name == "sqlite":
        session.execute(
            text(
                "DELETE FROM sqlite_sequence "
                "WHERE name IN ('employees', 'salaries')"
            )
        )
    session.commit()


def _print_summary(session) -> None:
    employees = _count(session, Employee)
    salaries = _count(session, Salary)
    fx_rows = _count(session, FxRate)
    print(f"employees: {employees}")
    print(f"salaries:  {salaries}")
    print(f"fx_rates:  {fx_rows} (expected {len(FX_RATES)})")

    country_rows = session.execute(
        select(Employee.country, func.count())
        .group_by(Employee.country)
        .order_by(Employee.country)
    ).all()
    print("countries:")
    for country, count in country_rows:
        print(f"  {country}: {count}")

    samples = session.execute(
        select(Employee, Salary)
        .join(Salary, Salary.employee_id == Employee.id)
        .order_by(Employee.employee_number)
        .limit(8)
    ).all()
    print("sample (employee_number, country, level, amount currency):")
    for employee, salary in samples:
        print(
            f"  {employee.employee_number}  {employee.country:16}  "
            f"{employee.job_level:3}  {salary.amount} {salary.currency}"
        )


def seed(*, reset: bool) -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        existing = _count(session, Employee)
        if reset:
            print(f"--reset: wiping {existing} employees and their salaries")
            _wipe_employees(session)
        elif existing >= TARGET_EMPLOYEES:
            print(
                f"Already seeded ({existing} employees >= {TARGET_EMPLOYEES}). "
                "Nothing to do. Pass --reset to wipe employees/salaries and "
                "re-seed."
            )
            _upsert_fx(session)
            session.commit()
            _print_summary(session)
            return
        elif existing > 0:
            print(
                f"Found {existing} employees (partial). Refusing to insert "
                "to avoid unique-key clashes. Re-run with --reset."
            )
            return

        rng = random.Random(SEED)
        random.seed(SEED)
        Faker.seed(SEED)
        fake = Faker()
        fake.seed_instance(SEED)

        started = time.perf_counter()
        _upsert_fx(session)
        session.commit()

        rows = _build_rows(rng, fake)
        inserted = 0
        for offset in range(0, len(rows), CHUNK_SIZE):
            chunk = rows[offset : offset + CHUNK_SIZE]
            employees = [item[0] for item in chunk]
            session.add_all(employees)
            session.flush()
            session.add_all(
                [
                    Salary(
                        employee_id=employee.id,
                        amount=amount,
                        currency=currency,
                        effective_date=effective_date,
                    )
                    for employee, amount, currency, effective_date in chunk
                ]
            )
            session.commit()
            inserted += len(chunk)
            print(f"inserted {inserted}/{TARGET_EMPLOYEES}")

        elapsed = time.perf_counter() - started
        print(f"Seed finished in {elapsed:.2f}s")
        _print_summary(session)
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Wipe employees and salaries, then re-seed (FX is upserted).",
    )
    args = parser.parse_args()
    seed(reset=args.reset)


if __name__ == "__main__":
    main()
