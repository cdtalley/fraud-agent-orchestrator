"""HMAC-SHA256 envelope over canonical result + audit tail."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


def sign_evidence_envelope(
    *,
    result: dict[str, Any],
    audit_events: list[dict[str, Any]],
    lineage: dict[str, Any],
    opa: dict[str, Any],
    secret: str,
) -> str:
    tail_hash = audit_events[-1]["event_hash"] if audit_events else ""
    payload = {
        "audit_tail_hash": tail_hash,
        "result": result,
        "lineage": lineage,
        "opa": opa,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    sig = hmac.new(
        secret.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"sha256-hmac:{sig}"
