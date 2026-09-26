from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "OrderPilot"
    database_url: str = "postgresql+psycopg://orderpilot:orderpilot@localhost:5432/orderpilot"
    cors_origins: str = "http://localhost:5173"
    seed_demo_data: bool = True
    max_upload_size_bytes: int = 5 * 1024 * 1024
    max_spreadsheet_rows: int = 2_000
    max_pdf_pages: int = 50
    langflow_enabled: bool = False
    langflow_url: str = "http://langflow:7860"
    langflow_flow_id: str | None = None
    langflow_api_key: str | None = None
    langflow_timeout_seconds: float = 15.0
    ai_confidence_threshold: float = 0.85

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
