"""Analytics tests use tiny hand-calculated datasets.

FX fixture rates: USD=1, INR=0.01
  100 USD + 10_000 INR * 0.01 = 200 USD total, 100 USD average.
"""

from decimal import Decimal

from tests.helpers import create_employee


def test_analytics_summary_fx_math(client):
    create_employee(
        client,
        employee_number="EMP00001",
        email="usd@acme.test",
        country="United States",
        salary={"amount": "100.00", "currency": "USD"},
    )
    create_employee(
        client,
        employee_number="EMP00002",
        email="inr@acme.test",
        country="India",
        salary={"amount": "10000.00", "currency": "INR"},
    )

    response = client.get("/api/analytics/summary")
    assert response.status_code == 200
    body = response.json()

    assert body["headcount"] == 2
    assert Decimal(body["total_usd"]) == Decimal("200.00")
    assert Decimal(body["avg_usd"]) == Decimal("100.00")
    assert Decimal(body["min_usd"]) == Decimal("100.00")
    assert Decimal(body["max_usd"]) == Decimal("100.00")


def test_analytics_by_country_headcounts_and_totals(client):
    # United States: 100 USD + 50 USD = 150 USD (2 people, avg 75)
    # India: 10_000 INR * 0.01 = 100 USD (1 person)
    create_employee(
        client,
        employee_number="EMP00001",
        email="us-a@acme.test",
        country="United States",
        last_name="Adams",
        salary={"amount": "100.00", "currency": "USD"},
    )
    create_employee(
        client,
        employee_number="EMP00002",
        email="us-b@acme.test",
        country="United States",
        last_name="Brown",
        salary={"amount": "50.00", "currency": "USD"},
    )
    create_employee(
        client,
        employee_number="EMP00003",
        email="in@acme.test",
        country="India",
        last_name="Chawla",
        salary={"amount": "10000.00", "currency": "INR"},
    )

    response = client.get("/api/analytics/by-country")
    assert response.status_code == 200
    rows = {row["country"]: row for row in response.json()}

    assert set(rows) == {"United States", "India"}
    assert rows["United States"]["headcount"] == 2
    assert Decimal(rows["United States"]["total_usd"]) == Decimal("150.00")
    assert Decimal(rows["United States"]["avg_usd"]) == Decimal("75.00")
    assert rows["India"]["headcount"] == 1
    assert Decimal(rows["India"]["total_usd"]) == Decimal("100.00")
    assert Decimal(rows["India"]["avg_usd"]) == Decimal("100.00")


def test_analytics_default_status_excludes_inactive(client):
    create_employee(
        client,
        employee_number="EMP00001",
        email="active@acme.test",
        status="active",
        salary={"amount": "100.00", "currency": "USD"},
    )
    create_employee(
        client,
        employee_number="EMP00002",
        email="inactive@acme.test",
        status="inactive",
        salary={"amount": "9999.00", "currency": "USD"},
    )

    default = client.get("/api/analytics/summary")
    assert default.status_code == 200
    active_only = default.json()
    assert active_only["headcount"] == 1
    assert Decimal(active_only["total_usd"]) == Decimal("100.00")

    inactive = client.get("/api/analytics/summary", params={"status": "inactive"})
    assert inactive.status_code == 200
    inactive_only = inactive.json()
    assert inactive_only["headcount"] == 1
    assert Decimal(inactive_only["total_usd"]) == Decimal("9999.00")
