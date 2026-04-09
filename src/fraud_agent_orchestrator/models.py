"""Typed models for fraud triage workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

Decision = Literal["approve", "review", "escalate"]


def utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


@dataclass(slots=True)
class TransactionAlert:
    transaction_id: str
    user_id: str
    timestamp: str
    amount: float
    currency: str
    merchant_category: str
    country: str
    card_present: bool
    auth_attempts_24h: int
    failed_auth_attempts_24h: int
    prior_transactions_1h: int
    user_home_country: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DerivedFeatures:
    amount_z_bucket: str
    is_geo_mismatch: bool
    is_high_velocity: bool
    is_high_amount: bool
    is_risky_merchant: bool
    auth_failure_ratio: float


@dataclass(slots=True)
class RiskResult:
    score: float
    reasons: list[str]
    llm_notes: str
    model_used: str


@dataclass(slots=True)
class PolicyResult:
    decision: Decision
    violations: list[str]
    policy_version: str


@dataclass(slots=True)
class FinalReport:
    transaction_id: str
    decision: Decision
    risk_score: float
    reasons: list[str]
    policy_violations: list[str]
    investigator_summary: str
    created_at_utc: str = field(default_factory=utc_now_iso)
