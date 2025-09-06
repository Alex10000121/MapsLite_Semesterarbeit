from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings(BaseModel):
    database_file: str = os.getenv(
        "DATABASE_FILE", str(BASE_DIR / "data" / "appdata.fs")
    )
    cors_allow_origins: list[str] = (
        os.getenv("CORS_ALLOW_ORIGINS", "http://127.0.0.1:5500,http://localhost:5500")
        .split(",")
        if os.getenv("CORS_ALLOW_ORIGINS")
        else ["http://127.0.0.1:5500", "http://localhost:5500"]
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
