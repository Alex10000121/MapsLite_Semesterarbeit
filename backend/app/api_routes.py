from __future__ import annotations
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from .schemas import RouteCreateRequest, RouteResponse, RouteListResponse
from .models import PersonalRoute, Coordinates, OpenRouteServiceGeometry
from .repository import create_route, list_routes, get_route, delete_route

router = APIRouter(prefix="/api/routes", tags=["PersonalRoutes"])

@router.get("", response_model=List[RouteResponse])
def list_personal_routes() -> List[Dict[str, Any]]:
    return list_routes()

@router.post("", response_model=RouteResponse, status_code=201)
def create_personal_route(payload: RouteCreateRequest) -> Dict[str, Any]:
    model = PersonalRoute(
        start_text=payload.start_text,
        end_text=payload.end_text,
        start_coordinates=Coordinates(**payload.start_coordinates),
        end_coordinates=Coordinates(**payload.end_coordinates),
        distance_meters=payload.distance_meters,
        duration_seconds=payload.duration_seconds,
        geometry=OpenRouteServiceGeometry(**payload.geometry) if payload.geometry else None,
    )
    return create_route(model)

@router.get("/{route_identifier}", response_model=RouteResponse)
def get_personal_route(route_identifier: str) -> Dict[str, Any]:
    item = get_route(route_identifier)
    if not item:
        raise HTTPException(status_code=404, detail="Route nicht gefunden")
    return item

@router.delete("/{route_identifier}", status_code=204)
def delete_personal_route(route_identifier: str) -> None:
    ok = delete_route(route_identifier)
    if not ok:
        raise HTTPException(status_code=404, detail="Route nicht gefunden")
