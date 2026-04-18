"""Temporal activity: execute triage and persist case + audit ledger."""

from __future__ import annotations

import uuid
from typing import Any

from temporalio import activity

from fraud_agent_orchestrator.db.repository import (
    append_audit_rows,
    get_case,
    update_case_triage,
)
from fraud_agent_orchestrator.db.session import async_session_factory
from fraud_agent_orchestrator.services.triage_service import execute_triage


@activity.defn
async def run_triage_activity(payload: dict[str, Any]) -> dict[str, Any]:
    case_uuid = uuid.UUID(payload["case_id"])
    async with async_session_factory() as session:
        case = await get_case(session, case_uuid)
        if not case:
            raise RuntimeError(f"case not found: {case_uuid}")
        alert = dict(case.alert_json)
        case.status = "running"
        await session.commit()

    triage = execute_triage(alert)

    wf_id: str | None = payload.get("workflow_id")
    if wf_id == "":
        wf_id = None

    async with async_session_factory() as session:
        await append_audit_rows(session, case_uuid, triage["audit_events"])
        await update_case_triage(
            session,
            case_uuid,
            status="awaiting_hitl" if triage.get("needs_hitl") else "completed",
            workflow_id=wf_id,
            triage=triage,
            evidence_signature=triage.get("evidence_signature"),
            lineage_json=triage.get("lineage"),
            opa_json=triage.get("opa"),
            hitl_pending=bool(triage.get("needs_hitl")),
            error_message=None,
        )

    return triage
