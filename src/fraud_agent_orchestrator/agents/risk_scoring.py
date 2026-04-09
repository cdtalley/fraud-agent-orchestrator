"""Risk scoring agent with deterministic + LLM augmentation."""

from __future__ import annotations

from fraud_agent_orchestrator.config import Settings
from fraud_agent_orchestrator.models import DerivedFeatures, RiskResult, TransactionAlert
from fraud_agent_orchestrator.ollama_client import ask_ollama


class RiskScoringAgent:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(self, alert: TransactionAlert, features: DerivedFeatures) -> RiskResult:
        score = 0.05
        reasons: list[str] = []
        if features.is_geo_mismatch:
            score += self.settings.geo_mismatch_penalty
            reasons.append("geo_mismatch")
        if features.is_risky_merchant:
            score += self.settings.risky_merchant_penalty
            reasons.append("risky_merchant_category")
        if features.is_high_velocity:
            score += self.settings.high_velocity_penalty
            reasons.append("high_transaction_velocity")
        if features.is_high_amount:
            score += self.settings.high_amount_penalty
            reasons.append("high_amount")
        if features.auth_failure_ratio >= 0.5 and alert.auth_attempts_24h > 2:
            score += self.settings.failed_auth_penalty
            reasons.append("elevated_auth_failures")
        score = max(0.0, min(1.0, round(score, 4)))
        prompt = (
            "You are a fraud analyst. Keep answer under 40 words.\n"
            f"Transaction amount: {alert.amount} {alert.currency}\n"
            f"Country/home mismatch: {features.is_geo_mismatch}\n"
            f"High velocity: {features.is_high_velocity}\n"
            f"Risky merchant: {features.is_risky_merchant}\n"
            f"Auth failure ratio: {features.auth_failure_ratio:.2f}\n"
            f"Deterministic reasons: {', '.join(reasons) if reasons else 'none'}"
        )
        llm = ask_ollama(
            base_url=self.settings.ollama_url,
            model=self.settings.ollama_model,
            prompt=prompt,
            timeout_seconds=self.settings.ollama_timeout_seconds,
        )
        return RiskResult(
            score=score,
            reasons=reasons if reasons else ["low_risk_baseline"],
            llm_notes=llm.text,
            model_used=llm.model_used,
        )
