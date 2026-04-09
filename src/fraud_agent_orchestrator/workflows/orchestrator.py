"""Deterministic fraud workflow orchestrator with audit trail."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fraud_agent_orchestrator.agents import (
    FeatureAgent,
    IntakeAgent,
    PolicyAgent,
    ReportAgent,
    RiskScoringAgent,
)
from fraud_agent_orchestrator.config import DEFAULT_SETTINGS, Settings
from fraud_agent_orchestrator.models import FinalReport
from fraud_agent_orchestrator.security import AuditTrail, hash_user_id


class FraudOrchestrator:
    def __init__(self, settings: Settings = DEFAULT_SETTINGS) -> None:
        self.settings = settings
        self.intake = IntakeAgent()
        self.feature = FeatureAgent(settings=settings)
        self.risk = RiskScoringAgent(settings=settings)
        self.policy = PolicyAgent(settings=settings)
        self.report = ReportAgent()

    def _safe_audit_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        safe = payload.copy()
        if "user_id" in safe:
            safe["user_id_sha256"] = hash_user_id(str(safe["user_id"]))
            safe.pop("user_id", None)
        as_text = str(safe)
        if len(as_text) > self.settings.max_audit_payload_chars:
            safe = {"payload_preview": as_text[: self.settings.max_audit_payload_chars]}
        return safe

    def run_one(self, raw_alert: dict[str, Any]) -> dict[str, Any]:
        trail = AuditTrail()
        trail.append("received_alert", self._safe_audit_payload(raw_alert))

        alert = self.intake.run(raw_alert)
        trail.append(
            "intake_complete",
            self._safe_audit_payload(asdict(alert)),
        )

        features = self.feature.run(alert)
        trail.append("features_computed", asdict(features))

        risk = self.risk.run(alert, features)
        trail.append(
            "risk_scored",
            {
                "score": risk.score,
                "reasons": risk.reasons,
                "model_used": risk.model_used,
            },
        )

        policy = self.policy.run(alert, risk)
        trail.append("policy_enforced", asdict(policy))

        final: FinalReport = self.report.run(alert, risk, policy)
        trail.append("report_created", asdict(final))

        return {
            "result": asdict(final),
            "audit_verified": trail.verify(),
            "audit_events": [asdict(event) for event in trail.events],
        }

    def run_batch(self, alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.run_one(alert) for alert in alerts]
