# VERIXA: Evidence-to-Action Enterprise AI Agent

> **Policy-aware, risk-controlled, evidence-backed workflow automation for high-stakes customer and field-service incident resolution.**

🌐 **Live Application:** [https://verixa-omega.vercel.app/](https://verixa-omega.vercel.app/)  
📖 **API Documentation (Swagger):** `https://<backend-url>/docs`  
🩺 **Health Endpoint:** `https://<backend-url>/api/health`

---

## 🚀 Overview & Problem Statement

Modern enterprises face two major roadblocks when deploying AI agents for operations:

1. **The "Chatbot Trap" (Read-Only RAG):** Traditional enterprise search and RAG platforms answer questions with text citations, but cannot take real action in enterprise tools (Jira, ERP, CRM, field dispatch).
2. **The "Uncontrolled Agent Trap" (Wild Autonomy):** Naive autonomous agents that invoke tools directly via LLM function calling introduce severe liabilities:
   - **Hallucinated Execution:** The LLM claims it performed an action when the API actually failed or timed out.
   - **Policy Violations:** High-consequence operations (e.g. replacing an $8,500 industrial chiller) run without managerial sign-off.
   - **Lack of Accountability:** When an incident occurs, enterprises cannot prove *why* the AI acted, *what policy* authorized it, or *which evidence* was cited.

### 🛡️ The Core Philosophy
> **"The LLM proposes; deterministic application code authorizes and executes."**

VERIXA enforces a strict boundary between probabilistic AI reasoning and deterministic corporate governance. The LLM suggests actions based on retrieved enterprise evidence, but **never touches tools directly**. Hardcoded, versioned business rules validate every proposal against cost limits, customer warranties, and risk classifications before execution.

---

## ⚖️ The 3-Way Decision Matrix

Every incoming operational incident is evaluated through a strict three-tier autonomy gate:

| Decision | Conditions | Outcome |
|---|---|---|
| **EXECUTE** (Autonomous) | Evidence confidence $\ge 0.70$, zero contradictions, policy permits, Low/Medium operational risk (< $5,000). | Executes tools immediately (creates tickets, assigns technicians), verifies outcome, logs to audit ledger in < 2s. |
| **APPROVAL REQUIRED** (Human Gate) | Technically valid request, but classified as High Risk or financial threshold > $5,000 (e.g., equipment replacement). | Pauses execution, generates cryptographic approval tokens, and dispatches alerts via Slack, Email, or Web Dashboard. |
| **ESCALATE / REFUSE** (Safe Refusal) | Evidence confidence < $0.70$, missing SOP documentation, or contradictory engineering manuals detected. | **Zero tool mutations executed**. Safely refuses action, explains evidence gaps, and routes referral to human engineers. |

---

## 🏗️ System Architecture & 7-Stage Pipeline

```text
                           ┌────────────────────────────────────────────────────────┐
                           │               Natural Language Request                 │
                           │  "Customer Acme Corp: Product PX-100 overheating..."   │
                           └──────────────────────────┬─────────────────────────────┘
                                                      │
                                                      ▼
                           ┌────────────────────────────────────────────────────────┐
                           │          Stage 1: Intent & Entity Extraction           │
                           │         LLM extracts issue, product, & urgency         │
                           └──────────────────────────┬─────────────────────────────┘
                                                      │
                                                      ▼
                           ┌────────────────────────────────────────────────────────┐
                           │        Stage 2: Enterprise Knowledge Retrieval         │
                           │    ChromaDB Vector Store (SOPs, Manuals, Policies)     │
                           │        + Contradiction & Conflict Detection            │
                           └──────────────────────────┬─────────────────────────────┘
                                                      │
                                                      ▼
                           ┌────────────────────────────────────────────────────────┐
                           │          Stage 3: Evidence-Backed Reasoning            │
                           │    Composite Confidence Calculation (Threshold: 70%)   │
                           └──────────────────────────┬─────────────────────────────┘
                                                      │
                                                      ▼
                           ┌────────────────────────────────────────────────────────┐
                           │          Stage 4: Structured Action Planning           │
                           │ Proposes typed ActionContract with cited Evidence IDs  │
                           └──────────────────────────┬─────────────────────────────┘
                                                      │
                                                      ▼
                           ┌────────────────────────────────────────────────────────┐
                           │        Stage 5: Deterministic Policy Engine            │
                           │       Versioned YAML Rules & Risk Classification       │
                           └──────────────────────────┬─────────────────────────────┘
                                                      │
                ┌─────────────────────────────────────┼─────────────────────────────────────┐
                ▼                                     ▼                                     ▼
    ┌───────────────────────┐             ┌───────────────────────┐             ┌───────────────────────┐
    │        EXECUTE        │             │   APPROVAL REQUIRED   │             │   ESCALATE / REFUSE   │
    │ Low / Medium Risk     │             │ High Risk / > $5,000  │             │ Confidence < 70%      │
    │ Policy Permits        │             │ Pauses for Human Gate │             │ Conflicting Evidence  │
    └───────────┬───────────┘             └───────────┬───────────┘             └───────────┬───────────┘
                │                                     │ (Slack / Email / UI)                │
                │                                     ▼                                     │
                │                         ┌───────────────────────┐                         │
                │                         │ Human Approver Signs  │                         │
                │                         └───────────┬───────────┘                         │
                ▼                                     ▼                                     ▼
    ┌─────────────────────────────────────────────────────────────┐             ┌───────────────────────┐
    │             Enterprise Tools Execution Layer                │             │  Route to Human Team  │
    │    Jira Cloud / Mock Tickets, Field Tech Dispatcher, Email  │             │   No Tool Execution   │
    └──────────────────────────────┬──────────────────────────────┘             └───────────┬───────────┘
                                   │                                                        │
                                   ▼                                                        │
    ┌─────────────────────────────────────────────────────────────┐                         │
    │             Stage 6: Post-Action Verification               │                         │
    │    Independently queries tool API to confirm real state     │                         │
    └──────────────────────────────┬──────────────────────────────┘                         │
                                   │                                                        │
                                   ▼                                                        ▼
    ┌───────────────────────────────────────────────────────────────────────────────────────────────┐
    │                         Stage 7: Cryptographic SHA-256 Audit Trail                            │
    │             Immutable hash-chained ledger storing request, policy, decision & proof           │
    └───────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🌟 Key Capabilities

### 1. Grounded Knowledge Retrieval & Contradiction Detection
- **22 Curated Enterprise Documents (145 Chunks):** Covers SOPs, operating manuals, warranties, and historical incident logs indexed in **ChromaDB**.
- **Metadata Boosting:** Prioritizes active Service Bulletins and Policies over legacy manuals.
- **Contradiction Guard:** Cross-checks retrieved documents for conflicting operational thresholds (e.g. conflicting thermal limits between 2021 and 2024 revisions) and forces human escalation when discrepancies arise.

### 2. Deterministic, Versioned Policy Engine
- Policies are defined in version-controlled YAML files (`backend/app/policy/rules.yaml`).
- Enforces financial thresholds (e.g. actions exceeding $5,000 mandate manager sign-off).
- Evaluates risk levels: `LOW` (ticket lookup), `MEDIUM` (technician dispatch), `HIGH` (asset replacement, refunds).

### 3. Multi-Channel Human-in-the-Loop (HITL) Approvals
- **Interactive Slack Cards:** Approvers receive Slack Block Kit messages with evidence summaries and one-click approve/reject actions.
- **Single-Use HMAC Email Links:** Cryptographically signed approval links with automated expiration and replay protection.
- **Approval Center:** Web UI cockpit displaying pending actions, cited evidence diffs, and timeout countdowns.
- **Time-Bounded SLA Routing:** If an approver fails to respond within the SLA window (e.g., 15 minutes), the task automatically escalates to secondary roles (`operations_director`).

### 4. Independent Post-Action State Verification
- Solves the "phantom execution" problem by refusing to trust API status codes alone.
- After a tool reports success, an isolated verification engine independently queries the system of record (e.g. confirming Jira ticket existence and status `CREATED` or checking technician calendar allocation).
- If verification fails, compensatory transactions trigger automatically to roll back partial actions.

### 5. Tamper-Evident SHA-256 Cryptographic Audit Chain
- Every run, decision, evidence citation, and execution outcome is logged to an immutable SQLite ledger.
- Each event row computes:
  $$\text{row\_hash} = \text{SHA-256}(\text{prev\_hash} + \text{timestamp} + \text{run\_id} + \text{event\_type} + \text{payload})$$
- Any retroactive modification or tampering immediately breaks the cryptographic verification chain, verifiable via `GET /api/audit/verify`.

### 6. Policy Simulator & Shadow Mode
- **Offline Policy Simulator:** Replays historical agent runs against candidate policy revisions to simulate impact before going live (*"Lowering approval limits to $3,000 will pause 14 additional tickets while maintaining 0 safety violations"*).
- **Shadow Mode:** Operates silently on live tickets in `DRY_RUN` mode, comparing AI proposals against human actions to measure accuracy and build trust.

---

## 💻 Tech Stack

| Layer | Technologies | Role in System |
|---|---|---|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4, Framer Motion | High-performance enterprise dashboard & cockpit |
| **Backend** | Python 3.12, FastAPI, Uvicorn, Pydantic v2 | High-concurrency async REST API and validation |
| **LLM Inference** | Google Gemini (`gemini-flash-lite`), OpenRouter | Structured intent extraction & action planning |
| **Vector DB** | ChromaDB (`chromadb` PersistentClient) | Local embedded semantic vector search & embeddings |
| **Database** | SQLite (WAL Mode), `aiosqlite` | Operational state persistence & cryptographic audit log |
| **Integrations** | Jira Cloud REST API, Slack Webhooks, SMTP | Production enterprise tool connectors & mock fallbacks |
| **Testing** | Pytest, Pytest-Asyncio, Oxlint | 80+ automated unit, regression, and policy tests |
| **Deployment** | Vercel (Frontend), Render (Backend) | Cloud hosting with automated CI/CD and CORS regex |

---

## 📁 Repository Structure

```text
evidence-to-action/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── agent/            # Pipeline orchestrator, graph executor, shadow mode
│   │   ├── analytics/        # Audit-derived ROI & KPI calculations
│   │   ├── api/              # REST API route controllers
│   │   ├── approvals/        # Routing, escalation timers, Slack/Email notifiers
│   │   ├── audit/            # Cryptographic SHA-256 hash-chain logger
│   │   ├── chat/             # Tenant-scoped assistant & documentation QA
│   │   ├── connectors/       # Jira Cloud API & mock enterprise connectors
│   │   ├── core/             # Configuration, database initialization, settings
│   │   ├── feedback/         # Human review store & knowledge gap logging
│   │   ├── knowledge/        # Ingestion, ChromaDB retrieval, conflict detection
│   │   ├── llm/              # LLM provider abstraction (Gemini / OpenRouter)
│   │   ├── models/           # Pydantic v2 schemas and domain models
│   │   ├── policy/           # Deterministic YAML policy engine & simulator
│   │   ├── tools/            # Registered enterprise tools (Tickets, Techs, Refunds)
│   │   └── verification/     # Post-action state verification engine
│   ├── data/                 # Seed enterprise data (Knowledge, Customers, Techs)
│   ├── tests/                # Comprehensive test suite (80+ test cases)
│   ├── pyproject.toml        # Backend package definitions
│   └── requirements.txt      # Production dependencies for Render deployment
├── frontend/                 # React Single Page Application
│   ├── src/
│   │   ├── assets/           # UI media & brand logos
│   │   ├── components/       # UI components (Hero, Navbar, StatsFooter, Video)
│   │   ├── pages/            # Page layouts (LandingPage)
│   │   ├── services/         # Typed API client layer (api.ts)
│   │   ├── App.tsx           # Application entrypoint
│   │   ├── index.css         # Tailwind CSS v4 styling & design tokens
│   │   └── main.tsx          # DOM root mount
│   ├── package.json          # Frontend dependencies & scripts
│   ├── vercel.json           # Vercel deployment configuration
│   └── vite.config.ts        # Vite configuration & dev proxy
├── data/                     # Source enterprise documents (SOPs, Manuals, Policies)
├── docs/                     # Comprehensive architecture and presentation guides
├── scripts/                  # Seeding & data utility scripts
├── render.yaml               # Render Infrastructure-as-Code Blueprint
├── vercel.json               # Root Vercel SPA deployment configuration
└── README.md                 # Master documentation (this file)
```

---

## 🛠️ Quick Start & Local Development

### Prerequisites
- **Python:** 3.11 or 3.12
- **Node.js:** v18+ & `npm`
- **API Key:** Google Gemini API Key (or OpenRouter)

---

### 1. Backend Setup

```powershell
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file from template
Copy-Item .env.example .env

# Start FastAPI server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API Base: `http://127.0.0.1:8000`
- Swagger UI Docs: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/api/health`

---

### 2. Frontend Setup

In a new terminal window:

```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

- Web Cockpit: `http://localhost:5173`

---

### 3. Run Automated Tests

```powershell
cd backend
.venv\Scripts\python -m pytest -q
```

---

## 🌐 Cloud Deployment Guide

### Deploy Backend to Render

1. Create a new **Web Service** on [Render](https://render.com).
2. Connect this GitHub repository.
3. Configure settings:
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Build Command:** 
     ```bash
     pip install --upgrade pip && pip install -r requirements.txt && python -c "from app.knowledge.ingestion import ingest_all; ingest_all()"
     ```
   - **Start Command:** 
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
4. Add Environment Variables:
   - `PYTHON_VERSION`: `3.12.0`
   - `LLM_PROVIDER`: `gemini`
   - `GEMINI_API_KEY`: `your_gemini_api_key`
   - `FRONTEND_URL`: `https://*.vercel.app`
   - `DATABASE_URL`: `sqlite:///./data/evidence_to_action.db`
   - `CHROMA_PERSIST_DIR`: `./data/chroma_db`

---

### Deploy Frontend to Vercel

1. Import your GitHub repository into [Vercel](https://vercel.com).
2. Set **Root Directory** to `frontend`.
3. Framework Preset: `Vite`.
4. Add Environment Variable:
   - `VITE_API_URL`: `https://<your-render-app>.onrender.com`
5. Click **Deploy**.

---

## ⚙️ Environment Variables Reference

| Variable | Default Value | Description |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | Choice of LLM backend (`gemini` or `openrouter`) |
| `GEMINI_API_KEY` | `""` | Google Gemini API key |
| `GEMINI_MODEL` | `gemini-flash-lite-latest` | Model version for reasoning |
| `OPENROUTER_API_KEY`| `""` | OpenRouter API key (fallback provider) |
| `DATABASE_URL` | `sqlite:///./data/evidence_to_action.db` | SQLite operational database URI |
| `CHROMA_PERSIST_DIR`| `./data/chroma_db` | Persistent vector store directory |
| `FRONTEND_URL` | `http://localhost:5173` | Allowed CORS origins (supports comma-separated values & Vercel regex) |
| `CONNECTOR_PROVIDER`| `mock` | Ticket system connector (`mock` or `jira`) |
| `APPROVAL_NOTIFIER` | `mock` | Human-in-the-loop notification method (`mock`, `slack`, `email`) |
| `SLACK_BOT_TOKEN` | `""` | Bot user OAuth token for Slack approvals |
| `SLACK_APPROVAL_CHANNEL` | `""` | Channel ID for routing approval cards |

---

## 🔌 Core API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status check |
| `POST` | `/api/shadow/run` | Execute full multi-stage agent pipeline |
| `GET` | `/api/shadow/report` | Shadow evaluation report & match rate |
| `GET` | `/api/approvals/pending` | List pending human approval requests |
| `POST` | `/api/approvals/{id}/approve` | Human gate approval authorization |
| `POST` | `/api/approvals/{id}/reject` | Human gate rejection |
| `GET` | `/api/audit/{run_id}` | Retrieve full audit trail for specific run |
| `GET` | `/api/audit/verify` | Verify cryptographic SHA-256 hash chain integrity |
| `GET` | `/api/policy/versions` | List active and historical policy versions |
| `POST` | `/api/policy/simulate` | Offline policy replay simulator |
| `GET` | `/api/analytics/summary` | ROI, automation rate, and time saved KPIs |
| `POST` | `/api/chat/turn` | Conversational document & operational Q&A |

---

## 📄 License

Distributed under the Apache 2.0 License. See `LICENSE` for details.
