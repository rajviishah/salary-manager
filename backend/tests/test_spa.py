from app.config import settings
from app.main import get_static_dir


def test_spa_index_and_client_route(client, tmp_path, monkeypatch):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html><title>ui</title>", encoding="utf-8")
    assets = dist / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log(1)", encoding="utf-8")
    monkeypatch.setattr(settings, "static_dir", str(dist))

    assert get_static_dir() == dist.resolve()

    home = client.get("/")
    assert home.status_code == 200
    assert "text/html" in home.headers["content-type"]
    assert b"<title>ui</title>" in home.content

    nested = client.get("/employees/42")
    assert nested.status_code == 200
    assert b"<title>ui</title>" in nested.content

    asset = client.get("/assets/app.js")
    assert asset.status_code == 200
    assert b"console.log(1)" in asset.content

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    missing_api = client.get("/api/does-not-exist")
    assert missing_api.status_code == 404
    assert missing_api.json()["detail"] == "Not Found"

    spec = client.get("/openapi.json")
    assert spec.status_code == 200
    assert spec.json()["info"]["title"] == "ACME Salary Manager"


def test_json_root_when_static_disabled(client, monkeypatch):
    monkeypatch.setattr("app.main.get_static_dir", lambda: None)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["health"] == "/health"
