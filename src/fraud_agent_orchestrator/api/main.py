"""FastAPI app: triage endpoint for the futuristic web console."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from fraud_agent_orchestrator.workflows import FraudOrchestrator

app = FastAPI(
    title="Fraud Agent Orchestrator",
    description="Multi-agent fraud triage API",
    version="0.2.0",
)

_origins = os.environ.get(
    "FRAUD_API_CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_orchestrator = FraudOrchestrator()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/triage")
def triage(alert: dict[str, Any]) -> dict[str, Any]:
    try:
        return _orchestrator.run_one(alert)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


def run() -> None:
    import uvicorn

    host = os.environ.get("FRAUD_API_HOST", "127.0.0.1")
    port = int(os.environ.get("FRAUD_API_PORT", "8000"))
    uvicorn.run(
        "fraud_agent_orchestrator.api.main:app",
        host=host,
        port=port,
        reload=False,
    )
