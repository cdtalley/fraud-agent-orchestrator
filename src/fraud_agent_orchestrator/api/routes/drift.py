"""Drift monitoring hook."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from fraud_agent_orchestrator.api.deps import RoleChecker, get_actor, get_db
from fraud_agent_orchestrator.contracts.schemas import ActorContext
from fraud_agent_orchestrator.governance.drift import record_drift_sample, recent_drift_rows

router = APIRouter(tags=["governance"])


@router.post("/internal/drift-check")
async def drift_check(
    body: dict[str, Any],
    _: Annotated[ActorContext, Depends(RoleChecker("admin", "auditor"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    await record_drift_sample(session, label=str(body.get("label", "manual")), case_sample=body)
    return {"status": "recorded"}


@router.get("/internal/drift-recent")
async def drift_recent(
    _: Annotated[ActorContext, Depends(RoleChecker("admin", "auditor", "analyst"))],
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
) -> list[dict[str, Any]]:
    rows = await recent_drift_rows(session, limit=limit)
    return [
        {
            "id": str(r.id),
            "label": r.label,
            "metrics": r.metrics_json,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
