"""Report agent for investigator-friendly output."""

from __future__ import annotations

from fraud_agent_orchestrator.models import FinalReport, PolicyResult, RiskResult, TransactionAlert


class ReportAgent:
    def run(
        self,
        alert: TransactionAlert,
        risk: RiskResult,
        policy: PolicyResult,
    ) -> FinalReport:
        reasons = risk.reasons
        summary = (
            f"Decision={policy.decision}; risk={risk.score:.2f}; "
            f"signals={', '.join(reasons)}; "
            f"policy_violations={', '.join(policy.violations) if policy.violations else 'none'}; "
            f"model={risk.model_used}; notes={risk.llm_notes}"
        )
        return FinalReport(
            transaction_id=alert.transaction_id,
            decision=policy.decision,
            risk_score=risk.score,
            reasons=reasons,
            policy_violations=policy.violations,
            investigator_summary=summary,
        )
