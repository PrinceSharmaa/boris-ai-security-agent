# BORIS — AI Security Operations Assistant

**Chat-driven security investigations · LangGraph orchestration · Retrieval-augmented generation · Human review**

![BORIS end-to-end architecture](docs/boris-architecture.png)

BORIS is a local-first educational security assistant built with **Streamlit, FastAPI, LangGraph, Ollama, ChromaDB, Sentence Transformers, and SQLite**. It can retrieve synthetic security events, correlate related alerts, apply explainable demonstration P1–P4 scoring, retrieve investigation runbooks, and draft ServiceNow-ready notes for manual copying. High-priority cases can be routed to an advisory human review queue.

> **Scope:** The included event feed is simulated. MDE, SentinelOne, SIEM, and ServiceNow are *not* live integrations. Incident numbers can only be resolved when backed by an available local record or a future authorized connector. No external ticket submission or automated remediation is performed. The architecture diagram depicts the intended end-to-end workflow, including potential external data sources.

## Requirements
- Python 3.11+
- Ollama installed and running
- About 8GB+ RAM recommended for the default 8B model (more may be needed depending on quantization and OS)
- Network access for the initial model and embedding-model downloads

## Quick start (two terminals)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # Windows: copy .env.example .env
ollama pull llama3.1:8b
ollama serve  # omit if Ollama is already running
```

Set `BORIS_API_KEY` to a random value in `.env`. In terminal 1:

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

In terminal 2 (activate the venv first):

```bash
streamlit run frontend/app.py
```

Open http://localhost:8501. FastAPI docs: http://localhost:8000/docs.

**Note:** Streamlit reads environment variables, not `.env` automatically. Export `BORIS_API_KEY` in both terminals if you changed it from the default, e.g. `export BORIS_API_KEY=your-key` (PowerShell: `$env:BORIS_API_KEY='your-key'`).

## Demo
Upload `data/raw/example_malware_runbook.md` through the Knowledge Base tab. Ask: "According to the malware investigation runbook, when must we escalate?"

## Tests
```bash
pytest -q
python -m compileall -q backend frontend
```

## Docker (optional)
Install Ollama on the host and pull the model first. Then run `docker compose up --build`. The initial embedding model may download on first start. The compose setup uses `host.docker.internal` to reach Ollama; on some platforms additional host networking configuration may be needed.

## Current scope and limitations
- Implemented: chat, input validation, simple intent classification, LangGraph execution, local Ollama inference, upload and extraction for text-based PDF/DOCX/TXT/MD/CSV, chunking, embeddings, ChromaDB similarity retrieval, lightweight lexical/semantic fusion, basic citation index checking, document list and deletion, API key protection.
- **Not implemented yet:** robust cross-encoder reranking, scanned PDF OCR, PNG/JPG vision ingestion, durable conversation memory, streaming, per-document RBAC, planner and specialized agents, incident scoring, model routing, human approval, strong prompt-injection defense, groundedness verification, file malware scanning, and operational audit logging.
- This is an educational local MVP. Do not upload confidential organizational documents or expose the API to a network without security hardening. Uploaded files are not malware-scanned. Retrieval is not tenant-isolated.
- Generated responses and citations must be verified by a human analyst before operational use. The system does not execute remediation.

## Phase 2 extension — synthetic security event feed (SQLite)

This extension **does not connect to live MDE, SentinelOne, or SIEM**. It generates clearly labeled synthetic events that persist in the free, embedded SQLite database `data/telemetry/boris_events.sqlite3`. No cloud account, subscription, or credentials are required. Docker Compose persists this file through its existing data volume.

In Streamlit, use **Seed demo feed**, **Generate 10 new alerts**, and the severity filter in the Simulated Live Security Feed section. Then ask the chat: **"Summarize the synthetic critical alerts and suggest relevant runbook investigation steps"**. The LangGraph workflow supplies recent synthetic events alongside RAG document context. The feed is queried per request (not pushed automatically), so refresh the UI to see new events. The event records are demonstrations, not confirmed threats.

Protected API endpoints:
- `POST /api/demo/seed`: insert 30 deterministic synthetic events only if the database is empty
- `POST /api/demo/generate` with `{"count": 10}`: append new synthetic events
- `GET /api/events?limit=50&severity=high`: filter events
- `GET /api/events/summary`: counts by source and severity
- `GET /api/events/{event_id}`: one event by ID

Example API calls (replace the key with your configured value):

```bash
curl -X POST http://localhost:8000/api/demo/seed -H 'X-API-Key: change-this-for-local-use'
curl http://localhost:8000/api/events/summary -H 'X-API-Key: change-this-for-local-use'
```

This feed is **poll-on-request**, not a real streaming collector. Event routing uses basic keyword matching, and only the latest 20 synthetic events are sent to the LLM for event questions. Do not treat this as complete incident correlation, live vendor integration, or enterprise-grade security. Future work can add vendor API adapters, incremental synchronization, access control, and alert-to-runbook correlation.

## Phase 3 increment: local incident correlation and explainable triage

The synthetic SQLite feed is now connected to a **deterministic demo priority engine** and a **24-hour host/category correlation view**. These are illustrative heuristics and are **not** an approved enterprise incident policy or proof that grouped alerts are causally related.

- `GET /api/incidents/correlations` — group events by hostname and category, with priority and explicit uncertainty.
- `GET /api/incidents/{event_id}/score` — transparent 0–100 score and P1–P4 demo priority; P1/P2 require human review.
- `POST /api/tickets/{event_id}/draft` — draft text for **manual** ServiceNow entry; no external submission.
- The LangGraph chat response now receives synthetic events, scores, and correlation hypotheses along with RAG evidence.
- The Streamlit interface shows correlation groups and offers score/ticket-draft actions by event ID.

**Not yet implemented:** real vendor integrations, autonomous feed polling, LangGraph interrupt/resume approval workflows, LLM-based model routing, robust evidence entailment checking, user-level RBAC, or production-grade security controls. The LLM must be running separately for chat generation.

## Phase 4 extension — agent routing and human review

This release adds deterministic specialized agent routing (knowledge, playbook, incident, ticket, general), explicit task plans, and configurable Ollama fast/reasoning model selection. It also persists **advisory** approval requests for synthetic P1/P2 events in `data/telemetry/approvals.sqlite3`. The Streamlit approval dashboard allows a reviewer to approve/reject each request. Decisions are audited with reviewer, timestamp, and reason; no remediation or external ticket submission occurs.

Optional `.env` settings: `OLLAMA_FAST_MODEL` and `OLLAMA_REASONING_MODEL`. If unset, both use `OLLAMA_MODEL`. Pull any configured model through Ollama before use.

API: `GET /api/approvals?status=pending`, `POST /api/approvals/{approval_id}/decision` with `{ "decision": "approved", "reviewer": "analyst", "reason": "reviewed" }`.

**Limitations:** Agents are specialized routing paths, not separate LLM-powered subgraphs. Planning is rule-based. The approval gate records durable requests but does not use LangGraph interrupt/resume. Output validation checks citation indices, not full claim-level groundedness. API-key authentication is single-key, not role-based; reviewer names are self-declared and must not be treated as authenticated identities. Use synthetic data only. Full local Ollama integration is not verified by unit tests.

## Phase 5 — chat-driven incident orchestration (2026-11-21)

This package supersedes Phase 4 and includes Phases 1–5. **Chat is the primary interface.**
The synthetic event feed, correlations and approval records are now in the optional **Security Monitoring (Optional)** tab; merely opening the UI does not trigger incident analysis.

Chat requests follow `input_guard → intent_router → execute_planned_tools → generate → output_guard → approval_gate`.
A deterministic planner chooses bounded tools based on query intent; this is **not** an unconstrained autonomous ReAct agent. The chat response includes `plan`, `tool_trace`, `event_filters`, `triage`, `correlations`, `ticket_drafts` and `approval_requests` for inspection in the UI.

The security-event tool supports severity and relative time-window filtering (e.g. `critical alerts from last 24 hours`). The scoring tool uses the existing demo-only policy. Correlation only groups events returned by the query, rather than all events. Draft ServiceNow notes are generated only when asked. P1/P2 results create advisory human-review records, not automatic remediation or real ticket submission.

### macOS quick start

```bash
cd ~/Documents/boris-local
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env  # skip if .env already exists
ollama pull llama3.1:8b
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

In a second terminal:

```bash
cd ~/Documents/boris-local
source .venv/bin/activate
export BORIS_API_KEY=change-this-for-local-use
python -m streamlit run frontend/app.py
```

Seed demo data in the optional Security Monitoring tab, or through `POST /api/demo/generate` (with the API key). The bundled SQLite events can become stale; generate fresh events before testing time filters.

Try: `Correlate critical alerts from the last 24 hours, find the relevant malware runbook, calculate priorities, and draft ServiceNow work notes.`

**Limits:** No vendor API connections, autonomous remediation, robust authorization, LangGraph interrupt/resume, verified LLM groundedness scoring, or production security hardening. This is an educational local simulation. Full end-to-end Ollama integration requires running on your Mac. Avoid using confidential corporate data.

## Final UI refresh — BORIS (blue/white Streamlit workspace)

The Streamlit application has a bright blue-and-white visual design and is branded **BORIS** (without “Local” in the UI). The original FastAPI/LangGraph backend and all previous phases are retained.

- **AI Assistant:** chat-first interface with quick-action prompts, optional compact responses, expandable tool/evidence traces, conversation reset, and at-a-glance synthetic alert counts.
- **Security Overview:** severity filter, metrics, refresh, demo seeding, and an optional toggle to expose detailed correlation and per-event ticket actions.
- **Knowledge Hub:** upload/index runbooks and manage indexed documents.
- **Human Review:** review advisory P1/P2 requests with reviewer and reason.
- **Settings:** backend health and model details.
- **Sidebar toggles:** agent trace, monitoring details, compact responses. These are UI/session controls; they do not change the underlying graph or model configuration.

Launch with `python -m streamlit run frontend/app.py` from the project directory after starting FastAPI. Streamlit's optional Google Fonts CSS requires an internet connection for that font; the UI remains functional offline with system fonts.

**Incident lookup limitation:** `INC0012345` is an example ServiceNow incident number, but this project has **no ServiceNow connector** and does not resolve real `INC...` identifiers. Existing synthetic events are keyed by UUID. A request containing a nonexistent ticket number must not be represented as a successfully retrieved incident. Draft notes are for manual copy into ServiceNow only.
