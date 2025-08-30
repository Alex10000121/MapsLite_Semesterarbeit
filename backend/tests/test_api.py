# backend/tests/test_api.py
import os
from contextlib import ExitStack
from datetime import datetime
from typing import Any, Dict
import json

import pytest
from fastapi.testclient import TestClient


def _load_app_with_env(tmp_path):
    """
    Lädt das FastAPI-App-Modul mit frischem Datenbankpfad aus der Umgebung
    und gibt (modul, client) zurück.
    """
    # Saubere Umgebung
    db_file = tmp_path / "appdata.fs"
    os.environ["DATABASE_FILE"] = str(db_file)
    os.environ["CORS_ALLOW_ORIGINS"] = "http://127.0.0.1:5500"
    os.environ["ORS_API_KEY"] = "test-key-not-used-in-mocked-tests"

    # Import erst NACH dem Setzen der Env-Variablen
    from app import main  # type: ignore

    # TestClient in Lifespan-Context
    stack = ExitStack()
    client = stack.enter_context(TestClient(main.app))
    return main, client, stack


def test_health_endpoint(tmp_path):
    main, client, stack = _load_app_with_env(tmp_path)
    try:
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        # sinnvolle Felder prüfen
        assert body["status"] == "ok"
        assert isinstance(body["database_open"], bool)
        assert "now_utc" in body
        # ISO-Format plausibel?
        datetime.fromisoformat(body["now_utc"].replace("Z", "+00:00"))
    finally:
        stack.close()


def _route_payload() -> Dict[str, Any]:
    return {
        "start_text": "Zürich HB, Schweiz",
        "end_text": "Bern Bahnhof, Schweiz",
        "start_coordinates": {"longitude": 8.537087, "latitude": 47.378177},
        "end_coordinates": {"longitude": 7.439136, "latitude": 46.94809},
        "distance_meters": 124543.6,
        "duration_seconds": 5535.9,
        "geometry_encoded": "_p~iF~ps|U_ulLnnqC_mqNvxq`@",
        "profile": "driving-car",
    }


def test_crud_routes(tmp_path):
    main, client, stack = _load_app_with_env(tmp_path)
    try:
        # 1) Liste ist leer
        r = client.get("/api/routes")
        assert r.status_code == 200
        assert r.json() == []

        # 2) Anlegen
        payload = _route_payload()
        r = client.post("/api/routes", json=payload)
        assert r.status_code == 201
        created = r.json()
        assert created["start_text"] == payload["start_text"]
        assert "identifier" in created
        identifier = created["identifier"]

        # 3) Liste enthält genau einen Datensatz
        r = client.get("/api/routes")
        assert r.status_code == 200
        lst = r.json()
        assert len(lst) == 1
        assert lst[0]["identifier"] == identifier

        # 4) Löschen (204, ohne Body)
        r = client.delete(f"/api/routes/{identifier}")
        assert r.status_code == 204
        assert r.text in ("", None)

        # 5) Liste wieder leer
        r = client.get("/api/routes")
        assert r.status_code == 200
        assert r.json() == []
    finally:
        stack.close()


# -----------------------
# ORS-Proxy-Tests (mocked)
# -----------------------
class _MockResp:
    def __init__(self, status=200, data=None):
        self.status_code = status
        self._data = data or {}

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    def json(self):
        return self._data

    @property
    def text(self):
        return json.dumps(self._data)


def test_ors_autocomplete_proxy(tmp_path, monkeypatch):
    main, client, stack = _load_app_with_env(tmp_path)
    try:
        # requests.get in app.main mocken
        def fake_get(url, params=None, timeout=None, **kwargs):
            assert "/geocode/autocomplete" in url
            assert "text" in params
            return _MockResp(
                200,
                {
                    "features": [
                        {
                            "properties": {"label": "Zürich HB, Schweiz"},
                            "geometry": {"coordinates": [8.537087, 47.378177]},
                        }
                    ]
                },
            )

        monkeypatch.setattr(main.requests, "get", fake_get)

        r = client.get("/api/ors/autocomplete", params={"text": "Zuerich", "size": 5})
        assert r.status_code == 200
        j = r.json()
        assert "features" in j and len(j["features"]) == 1
        assert j["features"][0]["properties"]["label"].startswith("Zürich")
    finally:
        stack.close()


def test_ors_geocode_proxy(tmp_path, monkeypatch):
    main, client, stack = _load_app_with_env(tmp_path)
    try:
        def fake_get(url, params=None, timeout=None, **kwargs):
            assert "/geocode/search" in url
            return _MockResp(
                200,
                {
                    "features": [
                        {
                            "properties": {"label": "Bern Bahnhof, Schweiz"},
                            "geometry": {"coordinates": [7.439136, 46.94809]},
                        }
                    ]
                },
            )

        monkeypatch.setattr(main.requests, "get", fake_get)

        r = client.get("/api/ors/geocode", params={"text": "Bern Bahnhof", "size": 1})
        assert r.status_code == 200
        j = r.json()
        assert j["features"][0]["properties"]["label"].startswith("Bern")
    finally:
        stack.close()


def test_ors_directions_proxy(tmp_path, monkeypatch):
    main, client, stack = _load_app_with_env(tmp_path)
    try:
        def fake_post(url, json=None, timeout=None, **kwargs):
            assert "/v2/directions/" in url
            assert json and "start" in json and "end" in json
            return _MockResp(
                200,
                {
                    "routes": [
                        {
                            "geometry": "_p~iF~ps|U_ulLnnqC_mqNvxq`@",
                            "summary": {"distance": 1000.0, "duration": 120.0},
                        }
                    ]
                },
            )

        monkeypatch.setattr(main.requests, "post", fake_post)

        body = {
            "start": [8.537087, 47.378177],
            "end": [7.439136, 46.94809],
            "profile": "driving-car",
        }
        r = client.post("/api/ors/directions", json=body)
        assert r.status_code == 200
        j = r.json()
        assert j["routes"][0]["summary"]["distance"] == 1000.0
    finally:
        stack.close()