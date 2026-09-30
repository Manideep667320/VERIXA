# Evidence-to-Action Enterprise AI Agent

> Policy-aware, risk-controlled, evidence-backed workflow automation for customer/field-service incident resolution.

## Quick Start

### Backend

```bash
cd backend
uv venv
uv pip install -e ".[dev]"
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Health Check

```
GET http://localhost:8000/api/health
```

## Architecture

```
Request → Intent → Evidence → Reasoning → Action Plan
→ Policy/Risk Check → Execute | Approval | Escalate
→ Verify → Audit
```

The LLM proposes actions. Deterministic code authorizes and executes.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, Pydantic |
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| LLM | Google Gemini / OpenRouter |
| Vector DB | ChromaDB |
| Database | SQLite |
| Package Manager | uv + pip |

## Project Structure

```
evidence-to-action/
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── agent/    # Agent graph + prompts
│   │   ├── api/      # REST endpoints
│   │   ├── audit/    # Audit trail
│   │   ├── core/     # Config, constants, DB
│   │   ├── knowledge/# Ingestion + retrieval
│   │   ├── llm/      # LLM provider abstraction
│   │   ├── models/   # Pydantic schemas
│   │   ├── policy/   # Deterministic policy engine
│   │   ├── tools/    # Mock enterprise tools
│   │   └── verification/
│   └── tests/
├── frontend/         # React + Vite + Tailwind
├── data/             # Knowledge base + seed data
└── scripts/          # Seed and utility scripts
```
