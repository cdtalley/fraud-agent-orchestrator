"""Health and metrics stubs."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/metrics")
def metrics() -> dict[str, str]:
    """Prometheus-style metrics placeholder."""

    return {"note": "wire OpenTelemetry + prometheus_client in production"}
