"""Model / policy lineage metadata."""

from __future__ import annotations

from fraud_agent_orchestrator.contracts.schemas import LineageRecord


def build_lineage(*, policy_version: str = "2026.04") -> dict[str, str]:
    rec = LineageRecord(policy_version=policy_version)
    return rec.model_dump()
