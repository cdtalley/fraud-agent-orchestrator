"""FastAPI application: enterprise fraud orchestrator API."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from fraud_agent_orchestrator.api.limits import limiter
from fraud_agent_orchestrator.api.routes import cases, drift, health
from fraud_agent_orchestrator.db.session import init_db
from fraud_agent_orchestrator.settings.env import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Fraud Agent Orchestrator",
        description="Multi-agent fraud triage: Temporal, OPA, RBAC, audit.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    _origins = os.environ.get("FRAUD_API_CORS_ORIGINS") or settings.fraud_api_cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in _origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(cases.router, prefix="/api/v1")
    app.include_router(drift.router, prefix="/api/v1")
    app.include_router(health.router)

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        import uuid

        rid = request.headers.get("x-request-id") or str(uuid.uuid4())
        response = await call_next(request)
        response.headers["x-request-id"] = rid
        return response

    return app


app = create_app()


def run() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "fraud_agent_orchestrator.api.main:app",
        host=settings.fraud_api_host,
        port=settings.fraud_api_port,
        reload=False,
    )
