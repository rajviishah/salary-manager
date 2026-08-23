"""Shared arrange helpers for API tests."""


def employee_payload(**overrides) -> dict:
    """Minimal valid POST /api/employees body. Nested ``salary`` can be overridden."""
    salary_overrides = overrides.pop("salary", None)
    payload = {
        "employee_number": "EMP00001",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@acme.test",
        "country": "United States",
        "department": "Engineering",
        "job_title": "Software Engineer",
        "job_level": "IC3",
        "hire_date": "2020-06-01",
        "status": "active",
        "salary": {
            "amount": "100.00",
            "currency": "USD",
            "effective_date": "2020-06-01",
        },
    }
    payload.update(overrides)
    if salary_overrides:
        payload["salary"] = {**payload["salary"], **salary_overrides}
    return payload


def create_employee(client, **overrides) -> dict:
    response = client.post("/api/employees", json=employee_payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()
