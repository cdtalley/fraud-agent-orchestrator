"""Case and audit persistence."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fraud_agent_orchestrator.db.models import AuditLedgerRow, CaseRecord


async def get_case(session: AsyncSession, case_id: uuid.UUID) -> CaseRecord | None:
    r = await session.get(CaseRecord, case_id)
    return r


async def get_case_by_idempotency(session: AsyncSession, key: str) -> CaseRecord | None:
    q = select(CaseRecord).where(CaseRecord.idempotency_key == key)
    res = await session.execute(q)
    return res.scalar_one_or_none()


async def create_case(
    session: AsyncSession,
    *,
    alert: dict[str, Any],
    actor_sub: str | None,
    request_id: str | None,
    tenant_id: str | None,
    idempotency_key: str | None,
) -> CaseRecord:
    tid = str(alert.get("transaction_id", "")) or None
    case = CaseRecord(
        alert_json=alert,
        status="pending",
        transaction_id=tid,
        actor_sub=actor_sub,
        request_id=request_id,
        tenant_id=tenant_id,
        idempotency_key=idempotency_key,
    )
    session.add(case)
    await session.commit()
    await session.refresh(case)
    return case


async def update_case_triage(
    session: AsyncSession,
    case_id: uuid.UUID,
    *,
    status: str,
    workflow_id: str | None,
    triage: dict[str, Any],
    evidence_signature: str | None,
    lineage_json: dict[str, Any] | None,
    opa_json: dict[str, Any] | None,
    error_message: str | None = None,
    hitl_pending: bool = False,
) -> None:
    case = await session.get(CaseRecord, case_id)
    if not case:
        return
    case.status = status
    if workflow_id is not None:
        case.workflow_id = workflow_id
    case.triage_json = triage
    case.evidence_signature = evidence_signature
    case.lineage_json = lineage_json
    case.opa_json = opa_json
    case.error_message = error_message
    case.hitl_pending = hitl_pending
    await session.commit()


async def append_audit_rows(
    session: AsyncSession,
    case_id: uuid.UUID,
    events: list[dict[str, Any]],
) -> None:
    for i, ev in enumerate(events):
        row = AuditLedgerRow(
            case_id=case_id,
            seq=i,
            step=ev["step"],
            payload_json=ev.get("payload", {}),
            prev_hash=ev["prev_hash"],
            event_hash=ev["event_hash"],
        )
        session.add(row)
    await session.commit()


async def list_cases(session: AsyncSession, limit: int = 50) -> list[CaseRecord]:
    q = select(CaseRecord).order_by(CaseRecord.created_at.desc()).limit(limit)
    r = await session.execute(q)
    return list(r.scalars().all())
