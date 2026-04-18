"""Application settings (env + defaults) for API, DB, Temporal, OPA, auth."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
    )

    # API (env: FRAUD_API_HOST, etc.)
    fraud_api_host: str = "127.0.0.1"
    fraud_api_port: int = 8000
    fraud_api_cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173"
    )

    # Database — sqlite default; use postgresql+asyncpg://... in production
    database_url: str = "sqlite+aiosqlite:///./fraud_orchestrator.db"

    redis_url: str | None = None

    temporal_target: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "fraud-triage"
    temporal_enabled: bool = True

    opa_url: str | None = "http://127.0.0.1:8181"

    evidence_hmac_secret: str = "dev-only-change-me-use-openssl-rand-hex-32"

    auth_disabled: bool = True
    oidc_issuer: str | None = None
    oidc_audience: str | None = None
    oidc_jwks_url: str | None = None
    auth_roles_claim: str = "roles"

    dev_default_roles: str = "analyst,supervisor,admin,auditor"

    rate_limit_per_minute: int = 120

    hitl_on_escalate: bool = True
    hitl_timeout_seconds: int = 120


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
