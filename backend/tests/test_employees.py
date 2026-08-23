from decimal import Decimal

from tests.helpers import create_employee, employee_payload


def test_create_employee_returns_201_with_nested_salary_and_get_by_id(client):
    created = create_employee(
        client,
        employee_number="EMP00042",
        email="ada@acme.test",
        salary={"amount": "75000.00", "currency": "USD"},
    )

    assert created["employee_number"] == "EMP00042"
    assert created["email"] == "ada@acme.test"
    assert created["salary"] is not None
    assert created["salary"]["currency"] == "USD"
    assert Decimal(created["salary"]["amount"]) == Decimal("75000.00")

    fetched = client.get(f"/api/employees/{created['id']}")
    assert fetched.status_code == 200
    body = fetched.json()
    assert body["id"] == created["id"]
    assert body["employee_number"] == "EMP00042"
    assert Decimal(body["salary"]["amount"]) == Decimal("75000.00")


def test_create_rejects_zero_amount(client):
    payload = employee_payload(salary={"amount": "0", "currency": "USD"})
    response = client.post("/api/employees", json=payload)
    assert response.status_code == 400


def test_create_rejects_negative_amount(client):
    payload = employee_payload(salary={"amount": "-1", "currency": "USD"})
    response = client.post("/api/employees", json=payload)
    assert response.status_code == 400


def test_create_rejects_unknown_currency(client):
    payload = employee_payload(salary={"amount": "100.00", "currency": "JPY"})
    response = client.post("/api/employees", json=payload)
    assert response.status_code == 400
    assert "Unknown currency" in response.json()["detail"]


def test_duplicate_email_returns_409(client):
    create_employee(client, employee_number="EMP00001", email="same@acme.test")
    response = client.post(
        "/api/employees",
        json=employee_payload(employee_number="EMP00002", email="same@acme.test"),
    )
    assert response.status_code == 409
    assert "Email" in response.json()["detail"]


def test_duplicate_employee_number_returns_409(client):
    create_employee(client, employee_number="EMP00001", email="one@acme.test")
    response = client.post(
        "/api/employees",
        json=employee_payload(employee_number="EMP00001", email="two@acme.test"),
    )
    assert response.status_code == 409
    assert "Employee number" in response.json()["detail"]


def test_get_missing_employee_returns_404(client):
    response = client.get("/api/employees/99999")
    assert response.status_code == 404
    assert "99999" in response.json()["detail"]


def test_patch_salary_updates_amount(client):
    created = create_employee(
        client, salary={"amount": "100.00", "currency": "USD"}
    )
    response = client.patch(
        f"/api/employees/{created['id']}/salary",
        json={
            "amount": "250.00",
            "currency": "USD",
            "effective_date": "2024-03-01",
        },
    )
    assert response.status_code == 200
    assert Decimal(response.json()["salary"]["amount"]) == Decimal("250.00")
    assert response.json()["salary"]["effective_date"] == "2024-03-01"


def test_patch_salary_rejects_invalid_amount_and_currency(client):
    created = create_employee(client)

    zero = client.patch(
        f"/api/employees/{created['id']}/salary",
        json={"amount": "0", "currency": "USD", "effective_date": "2024-03-01"},
    )
    assert zero.status_code == 400

    unknown = client.patch(
        f"/api/employees/{created['id']}/salary",
        json={"amount": "100.00", "currency": "JPY", "effective_date": "2024-03-01"},
    )
    assert unknown.status_code == 400
    assert "Unknown currency" in unknown.json()["detail"]


def test_list_pagination_splits_three_employees(client):
    # Default sort is last_name; names are chosen so page membership is obvious.
    ada = create_employee(
        client,
        employee_number="EMP00001",
        last_name="Adams",
        email="ada@acme.test",
    )
    beau = create_employee(
        client,
        employee_number="EMP00002",
        last_name="Brown",
        email="beau@acme.test",
    )
    cy = create_employee(
        client,
        employee_number="EMP00003",
        last_name="Clark",
        email="cy@acme.test",
    )

    page1 = client.get("/api/employees", params={"page": 1, "page_size": 2})
    page2 = client.get("/api/employees", params={"page": 2, "page_size": 2})

    assert page1.status_code == 200
    assert page2.status_code == 200
    body1, body2 = page1.json(), page2.json()

    assert body1["total"] == 3
    assert body2["total"] == 3
    assert body1["page"] == 1
    assert body2["page"] == 2
    assert body1["page_size"] == 2
    assert len(body1["items"]) == 2
    assert len(body2["items"]) == 1

    ids1 = {row["id"] for row in body1["items"]}
    ids2 = {row["id"] for row in body2["items"]}
    assert ids1.isdisjoint(ids2)
    assert ids1 | ids2 == {ada["id"], beau["id"], cy["id"]}
    assert [row["last_name"] for row in body1["items"]] == ["Adams", "Brown"]
    assert body2["items"][0]["last_name"] == "Clark"


def test_search_q_matches_employee_number_email_and_name(client):
    create_employee(
        client,
        employee_number="EMP00007",
        first_name="Grace",
        last_name="Hopper",
        email="grace.hopper@acme.test",
    )
    create_employee(
        client,
        employee_number="EMP00008",
        first_name="Alan",
        last_name="Turing",
        email="alan.turing@acme.test",
    )

    by_number = client.get("/api/employees", params={"q": "EMP00007"})
    assert by_number.status_code == 200
    assert [row["employee_number"] for row in by_number.json()["items"]] == ["EMP00007"]

    by_email = client.get("/api/employees", params={"q": "grace.hopper@"})
    assert by_email.status_code == 200
    assert [row["email"] for row in by_email.json()["items"]] == [
        "grace.hopper@acme.test"
    ]

    by_name = client.get("/api/employees", params={"q": "hopper"})
    assert by_name.status_code == 200
    assert [row["last_name"] for row in by_name.json()["items"]] == ["Hopper"]


def test_filters_country_and_department_reduce_list(client):
    create_employee(
        client,
        employee_number="EMP00001",
        email="us-eng@acme.test",
        country="United States",
        department="Engineering",
        last_name="Adams",
    )
    create_employee(
        client,
        employee_number="EMP00002",
        email="in-eng@acme.test",
        country="India",
        department="Engineering",
        last_name="Bose",
    )
    create_employee(
        client,
        employee_number="EMP00003",
        email="us-sales@acme.test",
        country="United States",
        department="Sales",
        last_name="Clark",
    )

    by_country = client.get("/api/employees", params={"country": "India"})
    assert by_country.status_code == 200
    assert by_country.json()["total"] == 1
    assert by_country.json()["items"][0]["email"] == "in-eng@acme.test"

    by_dept = client.get("/api/employees", params={"department": "Engineering"})
    assert by_dept.status_code == 200
    assert by_dept.json()["total"] == 2
    emails = {row["email"] for row in by_dept.json()["items"]}
    assert emails == {"us-eng@acme.test", "in-eng@acme.test"}
