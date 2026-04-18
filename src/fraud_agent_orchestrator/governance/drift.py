"""Drift monitoring hooks (aggregate checkpoints)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fraud_agent_orchestrator.db.models import DriftCheckpoint


async def record_drift_sample(
    session: AsyncSession,
    *,
    label: str,
    case_sample: dict[str, Any],
) -> None:
    """Store a lightweight checkpoint for interview/demo (extend with real stats)."""

    row = DriftCheckpoint(
        label=label,
        metrics_json={
            "transaction_id": case_sample.get("transaction_id"),
            "risk_score": (case_sample.get("triage") or {})
            .get("result", {})
            .get("risk_score"),
            "decision": (case_sample.get("triage") or {})
            .get("result", {})
            .get("decision"),
        },
    )
    session.add(row)
    await session.commit()


async def recent_drift_rows(session: AsyncSession, limit: int = 50) -> list[DriftCheckpoint]:
    q = select(DriftCheckpoint).order_by(DriftCheckpoint.created_at.desc()).limit(limit)
    r = await session.execute(q)
    return list(r.scalars().all())
