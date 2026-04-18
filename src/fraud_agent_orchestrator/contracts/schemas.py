"""Pydantic v2 models for alerts, cases, workflow I/O, and governance metadata."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

Decision = Literal["approve", "review", "escalate"]
CaseStatus = Literal["pending", "running", "awaiting_hitl", "completed", "failed"]
Role = Literal["analyst", "supervisor", "admin", "auditor"]


class TransactionAlertPayload(BaseModel):
    """Inbound alert (matches CLI / sample JSON)."""

    transaction_id: str
    user_id: str
    timestamp: str
    amount: float
    currency: str
    merchant_category: str
    country: str
    card_present: bool
    auth_attempts_24h: int
    failed_auth_attempts_24h: int
    prior_transactions_1h: int
    user_home_country: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("amount")
    @classmethod
    def non_negative_amount(cls, v: float) -> float:
        if v < 0:
            raise ValueError("amount must be non-negative")
        return v


class ActorContext(BaseModel):
    """Who triggered the action (audit / RBAC)."""

    sub: str = "anonymous"
    roles: list[str] = Field(default_factory=list)
    email: str | None = None
    request_id: str | None = None
    tenant_id: str | None = None


class CaseCreateRequest(BaseModel):
    """POST /v1/cases body."""

    alert: dict[str, Any]

    def model_alert(self) -> dict[str, Any]:
        return self.alert


class TriageWorkflowInput(BaseModel):
    """Temporal workflow input (JSON-serializable)."""

    case_id: str
    workflow_id: str | None = None
    alert: dict[str, Any]
    actor_sub: str
    actor_roles: list[str]
    request_id: str | None = None
    tenant_id: str | None = None
    idempotency_key: str | None = None
    hitl_timeout_seconds: int = 120


class LineageRecord(BaseModel):
    """Model and policy lineage for governance."""

    feature_schema_version: str = "2026.04"
    policy_version: str = "2026.04"
    opa_policy_package: str = "fraud"
    orchestrator_version: str = "1.0.0"
    prompt_template_hash: str = Field(
        default="sha256:placeholder",
        description="Hash of the risk prompt template used.",
    )


class OPAResult(BaseModel):
    """OPA evaluation summary."""

    allow: bool = True
    deny_reasons: list[str] = Field(default_factory=list)
    trace: dict[str, Any] = Field(default_factory=dict)


class TriagePipelineResult(BaseModel):
    """Full triage output including governance extensions."""

    result: dict[str, Any]
    audit_verified: bool
    audit_events: list[dict[str, Any]]
    lineage: LineageRecord
    opa: OPAResult
    evidence_signature: str
    needs_hitl: bool = False
    hitl_reason: str | None = None


class CaseSummary(BaseModel):
    id: UUID
    status: CaseStatus
    transaction_id: str | None
    workflow_id: str | None
    decision: Decision | None = None
    risk_score: float | None = None
    created_at: datetime
    updated_at: datetime


class CaseDetailResponse(BaseModel):
    id: UUID
    status: CaseStatus
    workflow_id: str | None
    transaction_id: str | None
    alert: dict[str, Any]
    triage: dict[str, Any] | None = None
    evidence_signature: str | None = None
    lineage: dict[str, Any] | None = None
    opa: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class SupervisorApprovalPayload(BaseModel):
    """Signal body for HITL."""

    approved: bool
    note: str = ""
    actor_sub: str
