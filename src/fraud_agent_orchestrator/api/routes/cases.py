"""Case ingest, list, detail, HITL signal, evidence export."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from fraud_agent_orchestrator.api.deps import RoleChecker, get_actor, get_db
from fraud_agent_orchestrator.api.limits import limiter
from fraud_agent_orchestrator.settings.env import get_settings
from fraud_agent_orchestrator.contracts.schemas import (
    ActorContext,
    CaseCreateRequest,
    CaseDetailResponse,
    CaseSummary,
    SupervisorApprovalPayload,
)
from fraud_agent_orchestrator.db.models import CaseRecord
from fraud_agent_orchestrator.db.repository import (
    create_case,
    get_case,
    get_case_by_idempotency,
    list_cases,
)
from fraud_agent_orchestrator.db.session import async_session_factory
from fraud_agent_orchestrator.services.triage_service import execute_triage
from fraud_agent_orchestrator.temporal_layer.client import (
    signal_supervisor,
    start_fraud_workflow,
)

router = APIRouter(tags=["cases"])


def _summary(c: CaseRecord) -> CaseSummary:
    triage = c.triage_json or {}
    res = triage.get("result") or {}
    decision = res.get("decision")
    risk = res.get("risk_score")
    return CaseSummary(
        id=c.id,
        status=c.status,  # type: ignore[arg-type]
        transaction_id=c.transaction_id,
        workflow_id=c.workflow_id,
        decision=decision,
        risk_score=float(risk) if risk is not None else None,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


def _rl() -> str:
    return f"{get_settings().rate_limit_per_minute}/minute"


@router.post("/cases")
@limiter.limit(_rl())
async def create_case_endpoint(
    request: Request,
    body: CaseCreateRequest,
    _: Annotated[ActorContext, Depends(RoleChecker("analyst", "admin", "supervisor"))],
    actor: Annotated[ActorContext, Depends(get_actor)],
    idempotency_key: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    settings = get_settings()
    alert = body.model_alert()

    async with async_session_factory() as session:
        if idempotency_key:
            existing = await get_case_by_idempotency(session, idempotency_key)
            if existing:
                return {"case_id": str(existing.id), "deduplicated": True}

        case = await create_case(
            session,
            alert=alert,
            actor_sub=actor.sub,
            request_id=actor.request_id,
            tenant_id=actor.tenant_id,
            idempotency_key=idempotency_key,
        )
        case_id = case.id

    if settings.temporal_enabled:
        try:
            wf_id = await start_fraud_workflow(
                case_id=case_id,
                alert=alert,
                actor_sub=actor.sub,
                actor_roles=actor.roles,
                request_id=actor.request_id,
                tenant_id=actor.tenant_id,
                idempotency_key=idempotency_key,
            )
            async with async_session_factory() as session:
                row = await get_case(session, case_id)
                if row:
                    row.workflow_id = wf_id
                    row.status = "running"
                    await session.commit()
            return {"case_id": str(case_id), "workflow_id": wf_id, "status": "running"}
        except Exception as e:
            triage = execute_triage(alert)
            async with async_session_factory() as session:
                row = await get_case(session, case_id)
                if row:
                    row.triage_json = triage
                    row.evidence_signature = triage.get("evidence_signature")
                    row.lineage_json = triage.get("lineage")
                    row.opa_json = triage.get("opa")
                    row.status = "completed"
                    row.workflow_id = None
                    await session.commit()
            return {
                "case_id": str(case_id),
                "status": "completed",
                "fallback": "temporal_unavailable",
                "detail": str(e),
                "triage": triage,
            }

    triage = execute_triage(alert)
    async with async_session_factory() as session:
        row = await get_case(session, case_id)
        if row:
            row.triage_json = triage
            row.evidence_signature = triage.get("evidence_signature")
            row.lineage_json = triage.get("lineage")
            row.opa_json = triage.get("opa")
            row.status = "completed"
            await session.commit()
    return {"case_id": str(case_id), "status": "completed", "triage": triage}


@router.get("/cases", response_model=list[CaseSummary])
async def list_cases_endpoint(
    _: Annotated[ActorContext, Depends(RoleChecker("analyst", "admin", "supervisor", "auditor"))],
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
) -> list[CaseSummary]:
    rows = await list_cases(session, limit=min(limit, 200))
    return [_summary(c) for c in rows]


@router.get("/cases/{case_id}", response_model=CaseDetailResponse)
async def get_case_endpoint(
    case_id: uuid.UUID,
    _: Annotated[ActorContext, Depends(RoleChecker("analyst", "admin", "supervisor", "auditor"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CaseDetailResponse:
    row = await get_case(session, case_id)
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    triage = row.triage_json
    return CaseDetailResponse(
        id=row.id,
        status=row.status,  # type: ignore[arg-type]
        workflow_id=row.workflow_id,
        transaction_id=row.transaction_id,
        alert=row.alert_json,
        triage=triage,
        evidence_signature=row.evidence_signature,
        lineage=row.lineage_json,
        opa=row.opa_json,
        error_message=row.error_message,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/cases/{case_id}/evidence")
async def evidence_pack(
    case_id: uuid.UUID,
    _: Annotated[ActorContext, Depends(RoleChecker("analyst", "admin", "supervisor", "auditor"))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    row = await get_case(session, case_id)
    if not row or not row.triage_json:
        raise HTTPException(status_code=404, detail="Case or triage not found")
    return {
        "case_id": str(case_id),
        "evidence_signature": row.evidence_signature,
        "lineage": row.lineage_json,
        "opa": row.opa_json,
        "triage": row.triage_json,
        "audit_events": (row.triage_json or {}).get("audit_events", []),
    }


@router.post("/cases/{case_id}/signal/supervisor")
async def supervisor_signal(
    case_id: uuid.UUID,
    body: SupervisorApprovalPayload,
    _: Annotated[ActorContext, Depends(RoleChecker("supervisor", "admin"))],
) -> dict[str, str]:
    await signal_supervisor(
        case_id=case_id,
        payload=body.model_dump(),
    )
    return {"status": "signal_sent"}


@router.post("/triage")
@limiter.limit(_rl())
async def triage_sync(
    request: Request,
    alert: dict[str, Any],
    _: Annotated[ActorContext, Depends(RoleChecker("analyst", "admin", "supervisor"))],
) -> dict[str, Any]:
    """Synchronous triage (no DB); backward compatible with early UI."""

    try:
        return execute_triage(alert)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
