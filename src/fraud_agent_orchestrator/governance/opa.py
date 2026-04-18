"""OPA policy-as-code client (HTTP)."""

from __future__ import annotations

import json
from typing import Any

import httpx

from fraud_agent_orchestrator.contracts.schemas import OPAResult


async def evaluate_opa(
    *,
    base_url: str | None,
    input_doc: dict[str, Any],
    policy_path: str = "v1/data/fraud/result",
    timeout: float = 2.0,
) -> OPAResult:
    if not base_url:
        return OPAResult(allow=True, deny_reasons=[], trace={"skipped": "opa_disabled"})

    url = f"{base_url.rstrip('/')}/{policy_path.lstrip('/')}"
    body = {"input": input_doc}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, json=body)
            r.raise_for_status()
            data = r.json()
    except (httpx.HTTPError, json.JSONDecodeError, OSError):
        return OPAResult(
            allow=True,
            deny_reasons=[],
            trace={"error": "opa_unreachable", "fallback": "allow"},
        )

    # OPA data document shape: {"result": {"allow": bool, "deny_reasons": [...]}}
    inner = data.get("result") if isinstance(data.get("result"), dict) else data
    allow = bool(inner.get("allow", True))
    reasons = list(inner.get("deny_reasons", []) or [])
    if not allow and not reasons:
        reasons = ["opa_deny"]
    return OPAResult(allow=allow, deny_reasons=reasons, trace={"raw": inner})


def evaluate_opa_sync(
    *,
    base_url: str | None,
    input_doc: dict[str, Any],
    policy_path: str = "v1/data/fraud/result",
    timeout: float = 2.0,
) -> OPAResult:
    """Sync variant for Temporal activities (no asyncio in sync activity)."""

    if not base_url:
        return OPAResult(allow=True, deny_reasons=[], trace={"skipped": "opa_disabled"})

    url = f"{base_url.rstrip('/')}/{policy_path.lstrip('/')}"
    body = {"input": input_doc}
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(url, json=body)
            r.raise_for_status()
            data = r.json()
    except (httpx.HTTPError, json.JSONDecodeError, OSError):
        return OPAResult(
            allow=True,
            deny_reasons=[],
            trace={"error": "opa_unreachable", "fallback": "allow"},
        )

    inner = data.get("result") if isinstance(data.get("result"), dict) else data
    allow = bool(inner.get("allow", True))
    reasons = list(inner.get("deny_reasons", []) or [])
    if not allow and not reasons:
        reasons = ["opa_deny"]
    return OPAResult(allow=allow, deny_reasons=reasons, trace={"raw": inner})
