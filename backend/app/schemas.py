from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

class Coord(BaseModel):
    lon: float
    lat: float

class RouteIn(BaseModel):
    start_text: str = Field(min_length=1, max_length=256)
    end_text: str = Field(min_length=1, max_length=256)
    start_coords: Coord
    end_coords: Coord
    distance: float = Field(ge=0)
    duration: float = Field(ge=0)
    geometry: dict

class RouteOut(RouteIn):
    id: str
    created_at: datetime

class Message(BaseModel):
    message: str
