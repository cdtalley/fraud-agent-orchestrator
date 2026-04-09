# Fraud Agent Orchestrator: Multi-Agent Fraud Triage Showcase

`fraud-agent-orchestrator` is a local-first portfolio project demonstrating production-style multi-agent orchestration for fraud operations.

The goal is to show:

- explicit agent responsibilities
- deterministic orchestration and handoffs
- policy-aware decisioning
- local LLM augmentation via Ollama
- reproducible evaluation on sample transactions

## Why this project

Fraud workflows are a practical proving ground for agent systems:

- decisions are high-impact and time-sensitive
- policy and compliance constraints must be explicit
- human investigators need clear evidence and rationale
- false positives are expensive

This repo implements a compact but realistic architecture where multiple specialized agents collaborate to triage a transaction alert.

## Architecture

Agents:

- `IntakeAgent`: validates and normalizes incoming alert payloads
- `FeatureAgent`: computes derived risk features from transaction context
- `RiskScoringAgent`: combines deterministic heuristics with LLM reasoning
- `PolicyAgent`: enforces business policy and escalation constraints
- `ReportAgent`: produces an investigator-ready decision summary

Orchestrator:

- `FraudOrchestrator`: step-based workflow engine with typed shared state
- deterministic transitions and terminal decision states

## Local model strategy

- Primary: Ollama (`http://localhost:11434`)
- Default model: `llama3.1:8b`
- Safe fallback: deterministic template output when Ollama is unavailable

This keeps demos fully local while remaining robust in interviews.

## Quickstart

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .
python -m fraud_agent_orchestrator.cli run --input data\sample_transactions.json --pretty
```

## Futuristic web console (Vite + React + Three.js)

Terminal 1 — API (CORS allows `localhost:5173`):

```bash
pip install -e .
fraud-api
```

Or: `python -m uvicorn fraud_agent_orchestrator.api.main:app --host 127.0.0.1 --port 8000`

Terminal 2 — UI:

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:5173`. The dev server proxies `/api/*` to the Python backend.

**Production UI build:** `cd web && npm run build` — serve `web/dist` behind any static host; set `FRAUD_API_CORS_ORIGINS` on the API to match your UI origin, or put both behind one reverse proxy.

## Example output

Each transaction receives:

- risk score (`0.0-1.0`)
- decision (`approve`, `review`, `escalate`)
- policy violations and reasons
- concise investigator report

## Project layout

```text
fraud-agent-orchestrator/
  data/
    sample_transactions.json
  web/
    (Vite React console)
  src/
    fraud_agent_orchestrator/
      agents/
      api/
      workflows/
      cli.py
      config.py
      models.py
      ollama_client.py
```

## Next upgrades

- add async orchestration and parallel agent branches
- add replayable trace logs and experiment tracking
- add formal eval suite (precision@k, review load, escalation quality)
- add synthetic drift scenarios and policy change simulations
