from __future__ import annotations
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class Coordinates(BaseModel):
    longitude: float = Field(..., description="Längengrad (lon)")
    latitude: float = Field(..., description="Breitengrad (lat)")

class OpenRouteServiceGeometry(BaseModel):
    # Wir speichern die ORS-GeoJSON-ähnliche Struktur so, wie der Client sie liefert
    type: Optional[str] = None
    coordinates: Optional[list[list[float]]] = None  # [ [lon, lat], ... ]
    # Falls ORS nur 'geometry' als kodierten Polyline liefert, lassen wir das Feld dennoch zu:
    # In diesem Projekt nutzen wir 'decoded' Koordinaten auf dem Client.

class PersonalRoute(BaseModel):
    route_identifier: Optional[str] = None
    start_text: str
    end_text: str
    start_coordinates: Coordinates
    end_coordinates: Coordinates
    distance_meters: float
    duration_seconds: float
    geometry: Optional[OpenRouteServiceGeometry] = None
    created_at_iso: Optional[str] = None  # ISO-String für Klarheit (statt datetime-Objekt)
