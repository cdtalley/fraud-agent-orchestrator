"""Policy enforcement agent."""

from __future__ import annotations

from fraud_agent_orchestrator.config import Settings
from fraud_agent_orchestrator.models import Decision, PolicyResult, RiskResult, TransactionAlert


class PolicyAgent:
    policy_version = "2026.04"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(self, alert: TransactionAlert, risk: RiskResult) -> PolicyResult:
        violations: list[str] = []
        decision: Decision

        if alert.amount >= 10000:
            violations.append("manual_review_required_high_notional")
        if alert.failed_auth_attempts_24h >= 5:
            violations.append("credential_abuse_signal")
        if alert.country in {"KP", "IR"}:
            violations.append("restricted_geography")

        if "restricted_geography" in violations:
            decision = "escalate"
        elif risk.score >= self.settings.escalate_threshold:
            decision = "escalate"
        elif risk.score >= self.settings.review_threshold or violations:
            decision = "review"
        else:
            decision = "approve"

        return PolicyResult(
            decision=decision,
            violations=violations,
            policy_version=self.policy_version,
        )
