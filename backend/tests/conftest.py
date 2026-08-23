"""Isolated API test fixtures: fresh in-memory SQLite per test.

Does not touch ``backend/data/salary.db``.
"""

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app import database
from app.main import app
from app.models import FxRate

# Hand-picked rates so analytics USD math is trivial:
# 100 USD + 10_000 INR * 0.01 = 200 USD.
FX_USD = Decimal("1")
FX_INR = Decimal("0.01")
FX_AS_OF = date(2026, 1, 1)


@pytest.fixture
def client():
    database.configure_database("sqlite:///:memory:")
    with TestClient(app) as test_client:
        db = database.SessionLocal()
        try:
            db.add_all(
                [
                    FxRate(currency="USD", usd_rate=FX_USD, as_of=FX_AS_OF),
                    FxRate(currency="INR", usd_rate=FX_INR, as_of=FX_AS_OF),
                ]
            )
            db.commit()
        finally:
            db.close()
        yield test_client
