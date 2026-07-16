from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Scenic Guide API"
    service_name: str = "ai-scenic-guide-api"
    version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
        ]
    )
    answer_provider: Literal["mock", "dify"] = "mock"
    mock_data_path: Path = Path(__file__).resolve().parents[4] / "data" / "mock" / "faq.json"
    dify_api_base_url: str = "https://api.dify.ai/v1"
    dify_api_key: str | None = None
    dify_timeout_seconds: float = 30.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="GUIDE_",
        env_nested_delimiter="__",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
