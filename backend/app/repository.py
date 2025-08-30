from __future__ import annotations
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import uuid

from .database import (
    add_personal_route,
    list_personal_routes as _list,
    get_personal_route as _get,
    delete_personal_route as _delete,
)
from .models import PersonalRoute

def create_route(payload: PersonalRoute) -> Dict[str, Any]:
    route_identifier = payload.route_identifier or str(uuid.uuid4())
    payload.route_identifier = route_identifier
    payload.created_at_iso = payload.created_at_iso or datetime.now(timezone.utc).isoformat()

    stored = add_personal_route(
        route_identifier,
        {
            "start_text": payload.start_text,
            "end_text": payload.end_text,
            "start_coordinates": payload.start_coordinates.dict(),
            "end_coordinates": payload.end_coordinates.dict(),
            "distance_meters": payload.distance_meters,
            "duration_seconds": payload.duration_seconds,
            "geometry": payload.geometry.dict() if payload.geometry else None,
            "created_at_iso": payload.created_at_iso,
        },
    )
    return {"route_identifier": route_identifier, **stored}

def list_routes() -> List[Dict[str, Any]]:
    return _list()

def get_route(route_identifier: str) -> Optional[Dict[str, Any]]:
    return _get(route_identifier)

def delete_route(route_identifier: str) -> bool:
    return _delete(route_identifier)
