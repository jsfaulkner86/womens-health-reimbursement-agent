# Women's Health Reimbursement Intelligence Agent

> **The Faulkner Group** — Boutique advisory infrastructure for women's healthtech companies.

A LangGraph-powered agentic AI system that converts fragmented payer flat files, CMS policy documents, and coverage data into investor-grade reimbursement pathway reports — in hours, not 18 months.

---

## Problem

Every women's healthtech company rebuilds the same reimbursement research from scratch:
- Manually downloading payer policy PDFs
- Interpreting CMS LCDs/NCDs without structured tooling
- Producing ad-hoc spreadsheets that don't satisfy investor due diligence

This system collapses that work into a shared, continuously refreshed intelligence layer.

---

## What It Builds

| Mode | Input | Output |
|---|---|---|
| `feasibility` | Service description + target CPT codes | Reimbursement Feasibility Brief (PDF) |
| `performance` | Claims flat files (EDI 835/837, CSV) | Reimbursement Performance + Scale Report (PDF) |

Both modes terminate in an **investor-grade artifact** designed for pre-fundraise due diligence.

---

## Architecture
EngagementRequest
↓
[mode router]
├── feasibility → CPT Landscape Agent → Policy Coverage Agent
│ → Gap & Risk Classifier → Narrative Generator → PDF
└── performance → Ingestion Agent → Payer Benchmarking Agent
→ Coverage Gap Analyzer → Scale Narrative → PDF

### Agents

| Agent | File | Role |
|---|---|---|
| CPT Landscape Agent | `agents/cpt_landscape.py` | Maps service description → CPT/HCPCS codes |
| Policy Coverage Agent | `agents/policy_coverage.py` | RAG over payer policies, LCDs/NCDs, state mandates |
| Gap & Risk Classifier | `agents/gap_classifier.py` | Scores reimbursement risk; quantifies uncompensated volume |
| Narrative Generator | `agents/narrative_generator.py` | Structured GPT-4o output → investor brief sections |
| Ingestion Agent | `agents/ingestion.py` | Normalizes EDI 835/837, CSV, PDF flat files |
| Payer Benchmarking Agent | `agents/payer_benchmark.py` | Denial rates, allowed amount variance, days-to-adjudication |
| Orchestrator | `agents/orchestrator.py` | LangGraph StateGraph; routes, sequences, manages HITL interrupts |

---

## Phase 1 Scope (Feasibility Mode)

Phase 1 ships the full feasibility pipeline — no claims data dependency.
Target: pre-seed/seed companies preparing investor materials.

Phase 2 adds flat-file ingestion and performance mode for Series A companies.

---

## Stack

- **Orchestration**: LangGraph (stateful, HITL interrupt before report delivery)
- **LLM**: GPT-4o (synthesis), o3 (pathway reasoning)
- **Embeddings**: `text-embedding-3-large`
- **Vector DB**: Qdrant
- **Relational DB**: PostgreSQL (Supabase)
- **Backend**: FastAPI (async)
- **Report Rendering**: Jinja2 → WeasyPrint → PDF
- **Observability**: LangSmith
- **Auth**: OAuth2 + RBAC (founder | analyst | investor-readonly)

---

## Setup

### Prerequisites
- Python 3.11+
- Docker + Docker Compose
- Qdrant running locally or cloud endpoint
- PostgreSQL (or Supabase project)

### Install

```bash
git clone https://github.com/<your-org>/womens-health-reimbursement-agent.git
cd womens-health-reimbursement-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys

docker-compose up -d          # spins up Qdrant + Postgres
python scripts/seed_corpus.py # ingests initial policy corpus
uvicorn api.main:app --reload

pytest tests/ -v

