"""SQLAlchemy models: cases, append-only audit rows, idempotency."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, Boolean, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from fraud_agent_orchestrator.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


# JSON type: JSONB on Postgres, JSON elsewhere
def _json_type():
    return JSON().with_variant(JSONB(), "postgresql")


class CaseRecord(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(512), unique=True, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    transaction_id: Mapped[str | None] = mapped_column(String(256), nullable=True, index=True)

    alert_json: Mapped[dict[str, Any]] = mapped_column(_json_type(), default=dict)
    triage_json: Mapped[dict[str, Any] | None] = mapped_column(_json_type(), nullable=True)
    evidence_signature: Mapped[str | None] = mapped_column(String(512), nullable=True)
    lineage_json: Mapped[dict[str, Any] | None] = mapped_column(_json_type(), nullable=True)
    opa_json: Mapped[dict[str, Any] | None] = mapped_column(_json_type(), nullable=True)

    actor_sub: Mapped[str | None] = mapped_column(String(256), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    hitl_pending: Mapped[bool] = mapped_column(Boolean, default=False)
    hitl_resolution: Mapped[dict[str, Any] | None] = mapped_column(_json_type(), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    audit_rows: Mapped[list[AuditLedgerRow]] = relationship(
        "AuditLedgerRow",
        back_populates="case",
    )


class AuditLedgerRow(Base):
    """Append-only audit storage (mirrors hash chain events)."""

    __tablename__ = "audit_ledger"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("cases.id", ondelete="CASCADE"), index=True
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    step: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(_json_type(), default=dict)
    prev_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    event_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    case: Mapped[CaseRecord] = relationship("CaseRecord", back_populates="audit_rows")


class DriftCheckpoint(Base):
    """Drift monitor hook: store periodic aggregates (stub for v1)."""

    __tablename__ = "drift_checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(_json_type(), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
