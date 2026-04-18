"""Start fraud triage workflow for a case."""

from __future__ import annotations

import uuid
from typing import Any

from temporalio.client import Client

from fraud_agent_orchestrator.contracts.schemas import TriageWorkflowInput
from fraud_agent_orchestrator.settings.env import get_settings
from fraud_agent_orchestrator.temporal_layer.workflow import FraudTriageWorkflow


async def start_fraud_workflow(
    *,
    case_id: uuid.UUID,
    alert: dict[str, Any],
    actor_sub: str,
    actor_roles: list[str],
    request_id: str | None,
    tenant_id: str | None,
    idempotency_key: str | None,
) -> str:
    settings = get_settings()
    client = await Client.connect(
        settings.temporal_target,
        namespace=settings.temporal_namespace,
    )
    workflow_id = f"fraud-case-{case_id}"
    wf_input = TriageWorkflowInput(
        case_id=str(case_id),
        workflow_id=workflow_id,
        alert=alert,
        actor_sub=actor_sub,
        actor_roles=actor_roles,
        request_id=request_id,
        tenant_id=tenant_id,
        idempotency_key=idempotency_key,
        hitl_timeout_seconds=settings.hitl_timeout_seconds,
    )
    await client.start_workflow(
        FraudTriageWorkflow.run,
        wf_input.model_dump(),
        id=workflow_id,
        task_queue=settings.temporal_task_queue,
    )
    return workflow_id


async def signal_supervisor(
    *,
    case_id: uuid.UUID,
    payload: dict[str, Any],
) -> None:
    settings = get_settings()
    client = await Client.connect(
        settings.temporal_target,
        namespace=settings.temporal_namespace,
    )
    handle = client.get_workflow_handle(f"fraud-case-{case_id}")
    await handle.signal(FraudTriageWorkflow.supervisor_decision, payload)
