from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, List

class RouteCreateRequest(BaseModel):
    start_text: str
    end_text: str
    start_coordinates: dict
    end_coordinates: dict
    distance_meters: float
    duration_seconds: float
    geometry: Optional[dict] = None

class RouteResponse(BaseModel):
    route_identifier: str
    start_text: str
    end_text: str
    start_coordinates: dict
    end_coordinates: dict
    distance_meters: float
    duration_seconds: float
    geometry: Optional[dict] = None
    created_at_iso: Optional[str] = None

class RouteListResponse(BaseModel):
    items: List[RouteResponse]
