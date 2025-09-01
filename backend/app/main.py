import os
import transaction
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import requests
from dotenv import load_dotenv

from ZODB import FileStorage, DB
from persistent import Persistent
from BTrees.OOBTree import OOBTree

# ==========================================================
# Konfiguration
# ==========================================================
load_dotenv()

DATABASE_FILE = os.getenv("DATABASE_FILE", "./data/appdata.fs")
ORS_API_KEY = os.getenv("ORS_API_KEY")
CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "http://127.0.0.1:5500,http://localhost:5500").split(",")

# ==========================================================
# Datenbank-Hilfen
# ==========================================================
_storage = FileStorage.FileStorage(DATABASE_FILE)
_database = DB(_storage)


def get_root_connection():
    connection = _database.open()
    root = connection.root()
    return connection, root


def get_routes_store(existing_connection=None) -> OOBTree:
    if existing_connection:
        root = existing_connection.root()
    else:
        connection, root = get_root_connection()
    if "routes" not in root:
        root["routes"] = OOBTree()
        transaction.commit()
    return root["routes"]


# ==========================================================
# Datenmodell
# ==========================================================
class Route(Persistent):
    def __init__(
        self,
        start_text: str,
        end_text: str,
        start_coordinates: Dict[str, float],
        end_coordinates: Dict[str, float],
        distance_meters: Optional[float],
        duration_seconds: Optional[float],
        geometry_encoded: Optional[str],
        profile: str,
    ):
        self.start_text = start_text
        self.end_text = end_text
        self.start_coordinates = start_coordinates
        self.end_coordinates = end_coordinates
        self.distance_meters = distance_meters
        self.duration_seconds = duration_seconds
        self.geometry_encoded = geometry_encoded
        self.profile = profile
        self.created_at = datetime.utcnow()


class RouteIn(BaseModel):
    start_text: str
    end_text: str
    start_coordinates: Dict[str, float]
    end_coordinates: Dict[str, float]
    distance_meters: Optional[float]
    duration_seconds: Optional[float]
    geometry_encoded: Optional[str]
    profile: str


class RouteOut(BaseModel):
    identifier: str
    start_text: str
    end_text: str
    start_coordinates: Dict[str, float]
    end_coordinates: Dict[str, float]
    distance_meters: Optional[float]
    duration_seconds: Optional[float]
    geometry_encoded: Optional[str]
    profile: str
    created_at: datetime


# ==========================================================
# FastAPI Setup
# ==========================================================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================================
# Health Endpoint
# ==========================================================
@app.get("/health")
def health() -> Dict[str, Any]:
    now_utc: Optional[str] = None
    database_open: Optional[bool] = None
    problems: List[str] = []

    # Zeitpunkt ermitteln
    try:
        now_utc = datetime.utcnow().isoformat() + "Z"
    except Exception:
        pass

    # Prüfen: Datenbank erreichbar?
    try:
        _ = get_routes_store()
        database_open = True
    except Exception as ex:
        database_open = False
        problems.append(f"database not ready: {ex}")

    # Prüfen: ORS-Key konfiguriert?
    if not ORS_API_KEY:
        problems.append("ORS_API_KEY missing")

    response: Dict[str, Any] = {"status": "ok" if not problems else "unhealthy"}
    if problems:
        response["problems"] = problems
    if database_open is not None:
        response["database_open"] = database_open
    if now_utc is not None:
        response["now_utc"] = now_utc

    return response


# ==========================================================
# ORS-Proxy (Backend ruft ORS auf, nicht das Frontend)
# ==========================================================
ORS_BASE = "https://api.openrouteservice.org"


@app.get("/api/ors/autocomplete")
def ors_autocomplete(text: str, size: int = 5):
    if not ORS_API_KEY:
        raise HTTPException(status_code=500, detail="ORS_API_KEY not configured")
    url = f"{ORS_BASE}/geocode/autocomplete"
    r = requests.get(url, params={"api_key": ORS_API_KEY, "text": text, "size": size})
    if not r.ok:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


@app.get("/api/ors/geocode")
def ors_geocode(text: str, size: int = 1):
    if not ORS_API_KEY:
        raise HTTPException(status_code=500, detail="ORS_API_KEY not configured")
    url = f"{ORS_BASE}/geocode/search"
    r = requests.get(url, params={"api_key": ORS_API_KEY, "text": text, "size": size})
    if not r.ok:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


class DirectionsIn(BaseModel):
    start: List[float]
    end: List[float]
    profile: str = "driving-car"


@app.post("/api/ors/directions")
def ors_directions(payload: DirectionsIn):
    if not ORS_API_KEY:
        raise HTTPException(status_code=500, detail="ORS_API_KEY not configured")
    url = f"{ORS_BASE}/v2/directions/{payload.profile}"
    r = requests.post(
        url,
        headers={"Authorization": ORS_API_KEY, "Content-Type": "application/json"},
        json={"coordinates": [payload.start, payload.end]},
    )
    if not r.ok:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return r.json()


# ==========================================================
# CRUD-Endpunkte für gespeicherte Routen
# ==========================================================
@app.get("/api/routes", response_model=List[RouteOut])
def list_routes():
    connection, root = get_root_connection()
    try:
        routes_store: OOBTree = get_routes_store(existing_connection=connection)
        result: List[RouteOut] = []
        for identifier, route in routes_store.items():  # type: ignore
            result.append(
                RouteOut(
                    identifier=identifier,
                    start_text=route.start_text,
                    end_text=route.end_text,
                    start_coordinates=route.start_coordinates,
                    end_coordinates=route.end_coordinates,
                    distance_meters=route.distance_meters,
                    duration_seconds=route.duration_seconds,
                    geometry_encoded=route.geometry_encoded,
                    profile=route.profile,
                    created_at=route.created_at,
                )
            )
        return result
    finally:
        connection.close()


@app.post("/api/routes", response_model=RouteOut, status_code=201)
def create_route(route_in: RouteIn):
    connection, root = get_root_connection()
    try:
        routes_store: OOBTree = get_routes_store(existing_connection=connection)
        identifier = str(int(datetime.utcnow().timestamp() * 1000))
        new_route = Route(
            start_text=route_in.start_text,
            end_text=route_in.end_text,
            start_coordinates=route_in.start_coordinates,
            end_coordinates=route_in.end_coordinates,
            distance_meters=route_in.distance_meters,
            duration_seconds=route_in.duration_seconds,
            geometry_encoded=route_in.geometry_encoded,
            profile=route_in.profile,
        )
        routes_store[identifier] = new_route  # type: ignore
        transaction.commit()
        return RouteOut(
            identifier=identifier,
            start_text=new_route.start_text,
            end_text=new_route.end_text,
            start_coordinates=new_route.start_coordinates,
            end_coordinates=new_route.end_coordinates,
            distance_meters=new_route.distance_meters,
            duration_seconds=new_route.duration_seconds,
            geometry_encoded=new_route.geometry_encoded,
            profile=new_route.profile,
            created_at=new_route.created_at,
        )
    finally:
        connection.close()


@app.delete("/api/routes/{identifier}", status_code=204, response_model=None)
def delete_route(identifier: str) -> Response:
    connection, root = get_root_connection()
    try:
        routes_store: OOBTree = get_routes_store(existing_connection=connection)
        if identifier in routes_store:  # type: ignore
            del routes_store[identifier]  # type: ignore
            transaction.commit()
            return Response(status_code=204)
        else:
            raise HTTPException(status_code=404, detail="route not found")
    finally:
        connection.close()
