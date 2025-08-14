import os, tempfile, json
from fastapi.testclient import TestClient
from app.main import app
from app import db as dbmod

def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["message"] == "ok"

def test_crud_routes(tmp_path, monkeypatch):
    # Use temp ZODB file
    test_db = tmp_path / "test_routes.fs"
    monkeypatch.setenv("ZODB_PATH", str(test_db))

    client = TestClient(app)

    payload = {
        "start_text": "Zürich HB",
        "end_text": "Bern Bahnhof",
        "start_coords": {"lon": 8.5402, "lat": 47.3782},
        "end_coords": {"lon": 7.4391, "lat": 46.9480},
        "distance": 120000.5,
        "duration": 5400.2,
        "geometry": {"type": "LineString", "coordinates": [[8.5402,47.3782],[7.4391,46.9480]]}
    }

    r = client.post("/api/routes", json=payload)
    assert r.status_code == 201
    rid = r.json()["id"]

    r2 = client.get(f"/api/routes/{rid}")
    assert r2.status_code == 200
    assert r2.json()["start_text"] == "Zürich HB"

    r3 = client.get("/api/routes")
    assert r3.status_code == 200
    assert len(r3.json()) >= 1

    r4 = client.delete(f"/api/routes/{rid}")
    assert r4.status_code == 200

    r5 = client.get(f"/api/routes/{rid}")
    assert r5.status_code == 404
