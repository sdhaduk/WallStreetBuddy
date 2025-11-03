"""
FastAPI Configuration using Pydantic BaseSettings
"""
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 8000
    debug: bool = True

    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_index_pattern: str = "ticker-mentions-*"

    # CORS Configuration
    allowed_origins: List[str] = ["*"]  # Allow all origins (restrict in production)

    # API Configuration
    api_prefix: str = "/api"
    api_title: str = "WallStreetBuddy API"
    api_version: str = "1.0.0"
    api_description: str = "REST API for Reddit ticker mention analytics"

    # Internal API Security (set via environment variable)
    internal_api_key: str = ""  

    class Config:
        case_sensitive = False

settings = Settings()