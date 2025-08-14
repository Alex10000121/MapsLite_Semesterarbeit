import os
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .db import get_connection, ensure_root, close, Route
from .schemas import RouteIn, RouteOut, Message
import transaction

app = FastAPI(title="LiteMaps API", version="1.0.0")

# CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=Message)
def health():
    return {"message": "ok"}

@app.get("/api/routes", response_model=list[RouteOut])
def list_routes():
    db, conn = get_connection()
    try:
        root = ensure_root(conn)
        routes = []
        for _, r in root["routes"].items():
            routes.append(RouteOut(
                id=r.id,
                start_text=r.start_text,
                end_text=r.end_text,
                start_coords={"lon": r.start_coords[0], "lat": r.start_coords[1]},
                end_coords={"lon": r.end_coords[0], "lat": r.end_coords[1]},
                distance=r.distance,
                duration=r.duration,
                geometry=r.geometry,
                created_at=r.created_at,
            ))
        # sort newest first
        routes.sort(key=lambda x: x.created_at, reverse=True)
        return routes
    finally:
        close(db, conn)

@app.post("/api/routes", response_model=RouteOut, status_code=201)
def create_route(payload: RouteIn):
    db, conn = get_connection()
    try:
        root = ensure_root(conn)
        rid = str(uuid.uuid4())
        r = Route(
            route_id=rid,
            start_text=payload.start_text.strip(),
            start_coords=[payload.start_coords.lon, payload.start_coords.lat],
            end_text=payload.end_text.strip(),
            end_coords=[payload.end_coords.lon, payload.end_coords.lat],
            distance=float(payload.distance),
            duration=float(payload.duration),
            geometry=payload.geometry,
            created_at=datetime.utcnow(),
        )
        root["routes"][rid] = r
        transaction.commit()
        return RouteOut(
            id=r.id,
            start_text=r.start_text,
            end_text=r.end_text,
            start_coords={"lon": r.start_coords[0], "lat": r.start_coords[1]},
            end_coords={"lon": r.end_coords[0], "lat": r.end_coords[1]},
            distance=r.distance,
            duration=r.duration,
            geometry=r.geometry,
            created_at=r.created_at,
        )
    finally:
        close(db, conn)

@app.get("/api/routes/{route_id}", response_model=RouteOut)
def get_route(route_id: str):
    db, conn = get_connection()
    try:
        root = ensure_root(conn)
        r = root["routes"].get(route_id)
        if not r:
            raise HTTPException(status_code=404, detail="Not found")
        return RouteOut(
            id=r.id,
            start_text=r.start_text,
            end_text=r.end_text,
            start_coords={"lon": r.start_coords[0], "lat": r.start_coords[1]},
            end_coords={"lon": r.end_coords[0], "lat": r.end_coords[1]},
            distance=r.distance,
            duration=r.duration,
            geometry=r.geometry,
            created_at=r.created_at,
        )
    finally:
        close(db, conn)

@app.delete("/api/routes/{route_id}", response_model=Message)
def delete_route(route_id: str):
    db, conn = get_connection()
    try:
        root = ensure_root(conn)
        if route_id in root["routes"]:
            del root["routes"][route_id]
            transaction.commit()
            return {"message": "deleted"}
        raise HTTPException(status_code=404, detail="Not found")
    finally:
        close(db, conn)
