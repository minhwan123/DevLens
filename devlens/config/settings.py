from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    github_token: str | None = None
    github_api_base_url: str = "https://api.github.com"
    github_cache_ttl_seconds: int = 3600
    gemini_api_key: str | None = None
    gemini_model_name: str = "gemini-flash-latest"
    gemini_cache_ttl_seconds: int = 3600
    # SQLite file backing SnapshotRepository (radar score history across re-analyses).
    snapshot_db_path: str = "./data/snapshots.db"
    # Comma-separated allowed origins for the frontend SPA (CORSMiddleware in interface/api/app.py).
    cors_origins: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
