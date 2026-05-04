# Agentic AI Interview Guide (mapped to this repo)

Use this document to **study** for agentic / LLM-systems interviews and to **defend this repo** as a portfolio piece. Each section gives: **what interviewers probe**, **how this project demonstrates it**, **where in code**, and **what to say if they go deeper**.

---

## Table of contents

1. [How to use this repo as a study lab](#how-to-use-this-repo-as-a-study-lab)
2. [The “agentic” vocabulary interviewers expect](#the-agentic-vocabulary-interviewers-expect)
3. [Theme map: question → repo → drill](#theme-map-question--repo--drill)
4. [Multi-agent orchestration (your core story)](#multi-agent-orchestration-your-core-story)
5. [Determinism, replay, and workflow engines](#determinism-replay-and-workflow-engines)
6. [LLMs as augmenters vs decision owners](#llms-as-augmenters-vs-decision-owners)
7. [Tools, policies, and “constitution layers”](#tools-policies-and-constitution-layers)
8. [Safety, abuse, and adversarial thinking](#safety-abuse-and-adversarial-thinking)
9. [Observability, audit, and compliance narrative](#observability-audit-and-compliance-narrative)
10. [Evaluation and offline metrics (what’s missing + how you’d add it)](#evaluation-and-offline-metrics-whats-missing--how-youd-add-it)
11. [System design curveballs](#system-design-curveballs)
12. [30 / 60 / 90 second pitches](#30--60--90-second-pitches)
13. [Self-study checklist (do these before the interview)](#self-study-checklist-do-these-before-the-interview)

---

## How to use this repo as a study lab


| Time     | Activity                                                                                                        |
| -------- | --------------------------------------------------------------------------------------------------------------- |
| 15 min   | Read `README.md` “Enterprise platform” + run `pytest -q`.                                                       |
| 30 min   | Trace one alert: CLI → `FraudOrchestrator.run_one` → open each agent file in order.                             |
| 45 min   | Run API + UI: `fraud-api`, `npm run dev` in `web/`, hit sync triage + list cases.                               |
| 2 h      | Read Temporal workflow + activities; draw the diagram on paper without looking.                                 |
| Half day | Pick one “gap” below and implement a thin slice (e.g., pytest for policy invariants, or OTel span on `/cases`). |


Artifacts you can show: **hash-chained audit JSON**, **OPA merge**, **Temporal HITL signal path**, **signed evidence string**, **RBAC-gated routes**.

---

## The “agentic” vocabulary interviewers expect


| Term                             | Plain meaning                                              | In this repo                                                                           |
| -------------------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| **Agent**                        | A module with a narrow contract and side-effect boundary.  | `agents/intake.py`, `feature.py`, `risk_scoring.py`, `policy.py`, `report.py`.         |
| **Orchestrator**                 | Scheduler / graph that wires agents and owns shared state. | `workflows/orchestrator.py` (`FraudOrchestrator`).                                     |
| **Workflow / durable execution** | Retries, timeouts, human steps, replay-safe control flow.  | `temporal_layer/workflow.py`, `activities/triage.py`, `activities/hitl.py`.            |
| **Tool use**                     | Model calls structured functions/APIs.                     | Ollama HTTP client `ollama_client.py` (minimal “tool”); extend pattern for real tools. |
| **Policy / constitution**        | Hard constraints above model opinions.                     | `PolicyAgent` + OPA `opa/policies/fraud.rego` + merge in `services/triage_service.py`. |
| **Guardrails**                   | Input validation, RBAC, rate limits, PII handling.         | Pydantic contracts, `api/deps.py`, SlowAPI, hashed `user_id` in audit.                 |
| **Observability**                | Traces, logs, metrics, audit for incidents.                | Audit trail + DB ledger + `x-request-id` middleware; OTel is a natural next step.      |
| **Eval**                         | Offline metrics + error analysis.                          | Not fully built; section below tells you how to talk about it credibly.                |


---

## Theme map: question → repo → drill


| Interview angle                                        | Point at                                                                 | Drill                                                                    |
| ------------------------------------------------------ | ------------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| “How do you structure multi-agent systems?”            | `agents/`, `workflows/orchestrator.py`                                   | Add a sixth agent (e.g. `VelocityAgent`) behind a feature flag.          |
| “How do you prevent LLM hallucinations from shipping?” | `risk_scoring.py` + `policy.py` + OPA merge                              | Explain: numeric score is heuristic; LLM is narrative; policy can veto.  |
| “How do you do HITL?”                                  | `temporal_layer/workflow.py` signal + `api/routes/cases.py` signal route | Walk through escalate → wait → `persist_hitl_activity`.                  |
| “How do you prove compliance?”                         | `security.py` + `governance/evidence.py` + `audit_ledger`                | Tamper one event in JSON; show `verify()` fails.                         |
| “How do you scale ingestion?”                          | FastAPI + Temporal + idempotency header                                  | Explain dedupe on `Idempotency-Key` and workflow id `fraud-case-{uuid}`. |


---

## Multi-agent orchestration (your core story)

**What they want:** Clear separation of concerns, explicit handoffs, testable units, no “god class” unless justified.

**Your story:** Each agent is a **pure-ish** transformation: input type → output type. The orchestrator is the **only** place that sequences them and centralizes audit events.

**Code path:** `FraudOrchestrator.run_one` in `workflows/orchestrator.py` calls:

1. `IntakeAgent` — schema / sanity
2. `FeatureAgent` — derived signals
3. `RiskScoringAgent` — score + optional LLM notes
4. `PolicyAgent` — violations + decision thresholds
5. `ReportAgent` — human-readable summary

**Say this:** “I treat ‘agent’ as an **engineering boundary**, not a prompt. The graph is explicit so we can test, replay, and swap implementations.”

---

## Determinism, replay, and workflow engines

**What they want:** You understand **why** Temporal (or Step Functions / Cadence) exists: partial failure, retries, visibility, **deterministic workflow code**.

**Your story:** Side effects (DB writes, HTTP to OPA, Ollama) live in **activities**. The workflow decides **when** to wait for a supervisor and when to persist HITL.

**Code:** `temporal_layer/workflow.py`, `temporal_layer/worker.py`, `temporal_layer/client.py`.

**Deep question:** “What must not run inside the workflow sandbox?”

**Answer:** Non-deterministic or heavyweight work: clocks (except workflow APIs), random without seeding, DB, network, LLM. Those belong in **activities** (you already did that for triage persistence).

**Drill:** Sketch what breaks if you put `datetime.now()` inside workflow code vs activity.

---

## LLMs as augmenters vs decision owners

**What they want:** You won’t let an LLM silently move money or change risk without constraints.

**Your story:** The **risk score** is computed from **deterministic** features; the LLM adds **short narrative** (`RiskScoringAgent` + `ollama_client.py`). **Policy** and **OPA** can force **escalate** regardless of “model vibes.”

**Say this:** “LLM is **not** the source of truth for the score in this slice; it’s **bounded augmentation** with timeout and fallback.”

**Stretch answer (if they push):** “In production I’d separate **model gateway** (routing, caching, safety filters, JSON schema enforcement) from domain agents.”

---

## Tools, policies, and “constitution layers”

**What they want:** Multiple enforcement layers: app policy, rego/OPA, human approval, rate limits.

**Your story:**

- **Python policy** = fast business rules close to the domain.  
- **OPA** = versionable, explainable **policy-as-code** (`opa/policies/fraud.rego`) evaluated over structured input (`governance/opa.py`).  
- **Merge semantics** = explicit in `execute_triage`: OPA deny → escalate + annotate violations.

**Say this:** “I treat OPA as a **second opinion** with an auditable trace object, not a replacement for domain logic.”

---

## Safety, abuse, and adversarial thinking

**What they want:** Prompt injection awareness, authz, rate limits, PII minimization, escalation paths.

**Your story:**

- **RBAC** via `RoleChecker` + JWT when auth is on (`api/deps.py`, `api/auth.py`).  
- **Rate limits** on hot endpoints (`api/limits.py`).  
- **PII**: `user_id` hashed in audit payloads (`security.py`).  
- **Abuse / fraud domain**: velocity, geo mismatch, credential abuse signals in `FeatureAgent` / `PolicyAgent`.

**Say this:** “Agentic systems fail in production on **authorization** and **data leakage**, not on clever prompts—so I wired RBAC, audit, and minimization early.”

---

## Observability, audit, and compliance narrative

**What they want:** Incident response: what happened, who did it, can we trust the log?

**Your story:**

- **In-run chain:** each step hashes previous hash + canonical payload (`AuditTrail` in `security.py`).  
- **DB append-only** mirror (`audit_ledger` in `db/models.py`).  
- **Evidence HMAC** over result + tail hash + lineage + OPA (`governance/evidence.py`).  
- **Request correlation:** `x-request-id` middleware in `api/main.py`.

**Say this:** “We have **integrity** (hash chain + verify), **authenticity** of exports (HMAC), and **separation** between operator narrative and machine-checkable events.”

---

## Evaluation and offline metrics (what’s missing + how you’d add it)

Interviewers **will** ask about eval. Be honest: this repo is strong on **architecture** and **audit**; full **labeled eval harness** is the next slice.

**Credible answer:** “I’d freeze a **golden set** of alerts with expected decision buckets, run batch triage in CI, and track precision@k for ‘review’ vs ‘escalate’, plus calibration plots for risk score. For LLM augmentation I’d add **schema-constrained** outputs and compare **narrative consistency** offline.”

**Quick win to implement later:** `tests/golden/` + parametrized pytest over JSON fixtures keyed by `transaction_id`.

---

## System design curveballs


| Question                      | Strong answer skeleton                                                                                                                            |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| “What if OPA is down?”        | Fail-open vs fail-closed is a **product decision**; here OPA client returns allow with trace flag—**I’d make that configurable per environment**. |
| “What if Temporal is down?”   | API **falls back** to in-process triage and still returns a result—**degraded mode** is explicit.                                                 |
| “How do you shard workflows?” | Partition by **tenant** or **hash(alert_id)**; separate task queues; workflow id includes tenant prefix.                                          |
| “How do you version prompts?” | Store **prompt template hash** in lineage (field exists); bump on change; correlate incidents to template version.                                |


---

## 30 / 60 / 90 second pitches

**30s:** “Multi-agent fraud triage with deterministic risk, policy + OPA, hash-chained audit, HMAC evidence, Temporal for retries and supervisor HITL, FastAPI + RBAC, React console.”

**60s:** Add: “LLM is optional augmentation with timeout; if Temporal or Ollama is down we degrade gracefully; audit is verifiable and user ids are hashed in logs.”

**90s:** Add: “I’d extend with golden-set eval in CI, OpenTelemetry across API→Temporal→activities, and KMS-backed signing for evidence in regulated environments.”

---

## Self-study checklist (do these before the interview)

- Trace `**FraudOrchestrator.run_one`** line by line with one row from `data/sample_transactions.json`.  
- Explain **three** policy outcomes (`approve` / `review` / `escalate`) using **both** `PolicyAgent` and OPA.  
- Draw **Temporal** control flow including **signal** and **timeout** branches without the code open.  
- Walk `**POST /api/v1/cases`** vs `**POST /api/v1/triage**`—when you’d use each in production.  
- Reconcile **hash chain** vs **HMAC evidence**—different threats (tamper vs authenticity).  
- List **five** production upgrades you’d prioritize (auth hardening, OTel, eval harness, signed export bundle, case replay UI).  
- Prepare **one failure story**: what broke, how audit helped, what you changed.

---

## Related docs in this repo

- [README.md](../README.md) — runbooks, API table, enterprise section.  
- [DEMO.md](./DEMO.md) — docker + env + curl examples.

You now have a **study spine**: vocabulary → themes → code map → drills → honest gaps. Re-read sections 4–9 the night before the interview; they map to the majority of agentic AI staff questions.