"""Settings read from environment variables (.env through docker compose)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    service_name: str = "service"
    jwt_secret: str = "dev-only-secret-change-me-dev-only-secret-change-me"
    jwt_issuer: str = "market-auth"
    jwt_ttl_minutes: int = 15
    refresh_ttl_days: int = 7

    database_url: str | None = None
    mongo_url: str | None = None
    kafka_bootstrap: str = "kafka:9092"
    otel_exporter_otlp_endpoint: str | None = None
    log_format: str = "json"

    # outbound calls (orders -> inventory / payment)
    inventory_url: str = "http://inventory:8000"
    payment_url: str = "http://payment:8000"
    http_timeout_s: float = 2.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
