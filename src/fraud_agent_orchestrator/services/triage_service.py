"""Core triage: orchestrator + OPA + lineage + evidence signature."""

from __future__ import annotations

from typing import Any

from fraud_agent_orchestrator.config import DEFAULT_SETTINGS, Settings
from fraud_agent_orchestrator.governance.evidence import sign_evidence_envelope
from fraud_agent_orchestrator.governance.lineage import build_lineage
from fraud_agent_orchestrator.governance.opa import evaluate_opa_sync
from fraud_agent_orchestrator.settings.env import AppSettings, get_settings
from fraud_agent_orchestrator.workflows.orchestrator import FraudOrchestrator


def execute_triage(
    raw_alert: dict[str, Any],
    *,
    scoring_settings: Settings | None = None,
    app_settings: AppSettings | None = None,
) -> dict[str, Any]:
    app_settings = app_settings or get_settings()
    scoring_settings = scoring_settings or DEFAULT_SETTINGS

    orch = FraudOrchestrator(scoring_settings)
    base = orch.run_one(raw_alert)

    opa_input = {
        "alert": raw_alert,
        "result": base["result"],
        "audit_verified": base["audit_verified"],
    }
    opa = evaluate_opa_sync(base_url=app_settings.opa_url, input_doc=opa_input)

    result = dict(base["result"])
    violations = list(result.get("policy_violations") or [])
    if not opa.allow:
        result["decision"] = "escalate"
        violations = violations + [f"opa:{r}" for r in opa.deny_reasons]
        result["policy_violations"] = violations

    base["result"] = result

    lineage = build_lineage(policy_version="2026.04")
    opa_dump = opa.model_dump()

    evidence_signature = sign_evidence_envelope(
        result=result,
        audit_events=base["audit_events"],
        lineage=lineage,
        opa=opa_dump,
        secret=app_settings.evidence_hmac_secret,
    )

    needs_hitl = (
        app_settings.hitl_on_escalate and result.get("decision") == "escalate"
    )
    hitl_reason = "escalate_requires_supervisor" if needs_hitl else None

    return {
        **base,
        "lineage": lineage,
        "opa": opa_dump,
        "evidence_signature": evidence_signature,
        "needs_hitl": needs_hitl,
        "hitl_reason": hitl_reason,
    }
