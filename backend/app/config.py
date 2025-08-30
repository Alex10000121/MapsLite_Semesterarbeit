from functools import lru_cache
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    database_file: str = os.getenv("DATABASE_FILE", "./data/appdata.fs")
    cors_allow_origins: list[str] = (
        os.getenv("CORS_ALLOW_ORIGINS", "http://127.0.0.1:5500,http://localhost:5500")
        .split(",")
        if os.getenv("CORS_ALLOW_ORIGINS")
        else ["http://127.0.0.1:5500", "http://localhost:5500"]
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
