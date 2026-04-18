# Enterprise demo runbook

## One-liner goals

- Show **multi-agent triage** with **hash-chained audit**, **OPA**, **signed evidence**, **Temporal** (optional), **RBAC** API, and the **React console**.

## Stack (Docker)

```bash
docker compose up -d
```

Services: **Postgres** (5432), **Redis** (6379), **OPA** (8181). **Temporal** is expected via `temporal server start-dev` (CLI) on `localhost:7233`, or your own cluster.

## Environment (example)

```bash
# Async SQLAlchemy
set DATABASE_URL=postgresql+asyncpg://fraud:fraud@localhost:5432/fraud
set REDIS_URL=redis://localhost:6379/0
set OPA_URL=http://127.0.0.1:8181
set TEMPORAL_ADDRESS=localhost:7233
set EVIDENCE_HMAC_SECRET=replace-with-openssl-rand-hex-32
set AUTH_DISABLED=true
```

SQLite (no Docker) still works for API-only demos:

```bash
set DATABASE_URL=sqlite+aiosqlite:///./fraud_orchestrator.db
```

## Processes

Terminal A — API:

```bash
pip install -e ".[dev]"
fraud-api
```

Terminal B — Temporal worker (when Temporal is up):

```bash
fraud-temporal-worker
```

Terminal C — UI:

```bash
cd web && npm install && npm run dev
```

## Scripted API checks

Health:

```bash
curl -s http://127.0.0.1:8000/api/health
```

Sync triage (no DB):

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/triage -H "Content-Type: application/json" -d "{\"transaction_id\":\"t1\",\"user_id\":\"u\",\"timestamp\":\"2026-04-09T12:00:00Z\",\"amount\":10,\"currency\":\"USD\",\"merchant_category\":\"grocery\",\"country\":\"US\",\"card_present\":true,\"auth_attempts_24h\":1,\"failed_auth_attempts_24h\":0,\"prior_transactions_1h\":0}"
```

Case ingest (DB + Temporal or fallback):

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/cases -H "Content-Type: application/json" -d "{\"alert\":{...same fields...}}"
```

List cases:

```bash
curl -s http://127.0.0.1:8000/api/v1/cases
```

Evidence pack:

```bash
curl -s http://127.0.0.1:8000/api/v1/cases/<case_uuid>/evidence
```

Supervisor signal (Temporal workflow waiting for HITL):

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/cases/<case_uuid>/signal/supervisor -H "Content-Type: application/json" -d "{\"approved\":true,\"note\":\"ok\",\"actor_sub\":\"supervisor-1\"}"
```

## OPA

Bundle lives in `opa/policies/fraud.rego`. OPA container mounts `./opa/policies`. Deny rules add `opa:*` violations in Python merge when `allow` is false.

## Tests

```bash
pytest -q
```

## Interview narrative (2 minutes)

1. “Alerts hit **FastAPI** with **RBAC**; cases persist to **Postgres**.”
2. “**Temporal** runs **activities** for triage; **HITL** is a **signal** + persist activity.”
3. “**OPA** adds **policy-as-code**; Python policy still runs for baseline.”
4. “**Audit** is hash-chained; we **HMAC** an evidence envelope for exports.”
