"""Persist supervisor HITL resolution to case row."""

from __future__ import annotations

import uuid
from typing import Any

from temporalio import activity

from fraud_agent_orchestrator.db.models import CaseRecord
from fraud_agent_orchestrator.db.session import async_session_factory


@activity.defn
async def persist_hitl_activity(payload: dict[str, Any]) -> None:
    case_uuid = uuid.UUID(payload["case_id"])
    resolution = payload.get("resolution") or {}
    async with async_session_factory() as session:
        case = await session.get(CaseRecord, case_uuid)
        if not case:
            raise RuntimeError(f"case not found: {case_uuid}")
        case.hitl_resolution = resolution
        case.hitl_pending = False
        case.status = "completed"
        if case.triage_json:
            tj = dict(case.triage_json)
            tj["hitl_resolution"] = resolution
            case.triage_json = tj
        await session.commit()
