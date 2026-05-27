from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


DEFAULT_GOLD_SNAPSHOT_DIR = Path(__file__).resolve().parents[4] / "data" / "gold_snapshots"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    clubos_api_host: str = "0.0.0.0"
    clubos_api_port: int = 8000
    clubos_cors_origins: str = ",".join(
        [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:5176",
            "http://127.0.0.1:5176",
            "http://localhost:5177",
            "http://127.0.0.1:5177",
        ]
    )
    clubos_databricks_host: Optional[str] = None
    clubos_databricks_token: Optional[str] = None
    clubos_databricks_http_path: Optional[str] = None
    clubos_databricks_catalog: Optional[str] = None
    clubos_databricks_schema: Optional[str] = None
    # Local development defaults to repository snapshots when available.
    clubos_gold_snapshot_dir: Optional[str] = (
        str(DEFAULT_GOLD_SNAPSHOT_DIR) if DEFAULT_GOLD_SNAPSHOT_DIR.exists() else None
    )
    clubos_ai_provider: Optional[str] = None
    clubos_ai_api_key: Optional[str] = None


settings = Settings()


def get_cors_origins() -> list[str]:
    return [origin.strip() for origin in settings.clubos_cors_origins.split(",") if origin.strip()]
