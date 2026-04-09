"""Security and auditability helpers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _stable_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def hash_user_id(raw_user_id: str) -> str:
    return hashlib.sha256(raw_user_id.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class AuditEvent:
    timestamp_utc: str
    step: str
    payload: dict[str, Any]
    prev_hash: str
    event_hash: str


@dataclass(slots=True)
class AuditTrail:
    """Tamper-evident event list using hash chaining."""

    seed_hash: str = "GENESIS"
    events: list[AuditEvent] = field(default_factory=list)

    def append(self, step: str, payload: dict[str, Any]) -> AuditEvent:
        timestamp = datetime.now(tz=timezone.utc).isoformat()
        prev_hash = self.events[-1].event_hash if self.events else self.seed_hash
        canonical_payload = _stable_json(payload)
        to_hash = f"{timestamp}|{step}|{canonical_payload}|{prev_hash}"
        event_hash = hashlib.sha256(to_hash.encode("utf-8")).hexdigest()
        event = AuditEvent(
            timestamp_utc=timestamp,
            step=step,
            payload=payload,
            prev_hash=prev_hash,
            event_hash=event_hash,
        )
        self.events.append(event)
        return event

    def verify(self) -> bool:
        prev_hash = self.seed_hash
        for event in self.events:
            canonical_payload = _stable_json(event.payload)
            to_hash = (
                f"{event.timestamp_utc}|{event.step}|{canonical_payload}|{prev_hash}"
            )
            expected = hashlib.sha256(to_hash.encode("utf-8")).hexdigest()
            if event.event_hash != expected or event.prev_hash != prev_hash:
                return False
            prev_hash = event.event_hash
        return True
