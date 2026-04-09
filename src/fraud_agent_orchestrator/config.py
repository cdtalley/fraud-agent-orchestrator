"""Central configuration for fraud agent orchestrator."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings for deterministic scoring and policy decisions."""

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_timeout_seconds: float = 3.0
    review_threshold: float = 0.45
    escalate_threshold: float = 0.75
    high_amount_threshold: float = 3000.0
    high_velocity_1h_threshold: int = 5
    geo_mismatch_penalty: float = 0.2
    risky_merchant_penalty: float = 0.15
    high_velocity_penalty: float = 0.2
    high_amount_penalty: float = 0.25
    failed_auth_penalty: float = 0.2
    max_audit_payload_chars: int = 500


DEFAULT_SETTINGS = Settings()
