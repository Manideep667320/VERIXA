# Evidence-to-Action Enterprise AI Agent
## Executive Presentation & Technical Overview Guide

> **Core Value Proposition:**  
> Traditional enterprise RAG tells an employee what the company *knows*.  
> **Evidence-to-Action** determines what the company is *allowed to do*, acts autonomously when safe, enforces human approval when high-risk, verifies real-world execution, and guarantees an immutable, tamper-evident audit trail.

---

## 1. Executive Summary & Problem Statement

### The Enterprise Problem with Generative AI & Autonomous Agents
Modern enterprises face two major roadblocks when adopting LLM agents:
1. **The "Chatbot Trap" (Read-Only RAG):** Traditional enterprise search and RAG platforms answer questions with text citations, but they cannot take real actions in enterprise tools (Jira, ServiceNow, ERP, CRMs).
2. **The "Uncontrolled Agent Trap" (Wild Autonomy):** Naive autonomous agents that call tools directly via LLM function calling introduce unacceptable enterprise liabilities:
   - **Hallucinated Execution:** The LLM claims it performed an action when the API actually failed or timed out.
   - **Policy Violations:** The agent performs high-consequence actions (e.g. replacing a $15,000 industrial chiller or issuing refunds) without managerial oversight.
   - **Lack of Accountability:** When an incident occurs, enterprises cannot prove *why* the AI acted, *what policy* authorized it, or *which evidence* was cited.

### The Solution: Evidence-to-Action
Evidence-to-Action solves this with a strict architectural boundary:
> **"The LLM proposes; deterministic application code authorizes and executes."**

The system operates across a clear 3-way decision matrix:
1. **EXECUTE:** When enterprise evidence is strong, policies permit the action, and risk is low/medium.
2. **APPROVAL REQUIRED:** When the action is technically valid, but corporate policy mandates human sign-off (high financial cost, major asset replacement, or high operational risk).
3. **ESCALATE / REFUSE:** When evidence is missing, contradictory, or below the 70% confidence threshold. The agent **never hallucinates** actions under uncertainty.

---

## 2. High-Level System Architecture

```text
                               ┌────────────────────────────────────────────────────────┐
                               │               Natural Language Request                 │
                               │  "Customer Acme Corp: Product PX-100 overheating..."   │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │
                                                          ▼
                               ┌────────────────────────────────────────────────────────┐
                               │           Stage 1: Intent & Entity Extraction          │
                               │           LLM extracts issue, product, & urgency       │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │
                                                          ▼
                               ┌────────────────────────────────────────────────────────┐
                               │        Stage 2: Enterprise Knowledge Retrieval         │
                               │     ChromaDB Vector Store (SOPs, Manuals, Policies)     │
                               │         + Contradiction & Conflict Detection           │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │
                                                          ▼
                               ┌────────────────────────────────────────────────────────┐
                               │          Stage 3: Evidence-Backed Reasoning            │
                               │    Computes confidence score (Threshold: >= 70%)       │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │
                                                          ▼
                               ┌────────────────────────────────────────────────────────┐
                               │          Stage 4: Structured Action Planning           │
                               │  Proposes typed ActionContract with cited Evidence IDs  │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │
                                                          ▼
                               ┌────────────────────────────────────────────────────────┐
                               │      Stage 5 & 6: Deterministic Policy Engine          │
                               │        Versioned YAML Rules & Risk Classification       │
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
        │           Stage 7A: Post-Action Verification                │                         │
        │      Independently queries tool API to confirm real state   │                         │
        └──────────────────────────────┬──────────────────────────────┘                         │
                                       │                                                        │
                                       ▼                                                        ▼
        ┌───────────────────────────────────────────────────────────────────────────────────────────────┐
        │                         Stage 7B: Cryptographic SHA-256 Audit Trail                           │
        │            Immutable hash-chained ledger storing request, policy, decision & proof            │
        └───────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Features & How They Work

### 1. Grounded Knowledge Retrieval & Contradiction Detection
- **What it does:** Searches enterprise standard operating procedures (SOPs), product service manuals, corporate warranties, and past incident histories.
- **How it works:** Markdown files are embedded and indexed into ChromaDB. During query execution, a semantic search retrieves the top-K chunks.
- **Contradiction Guard:** The engine automatically analyzes retrieved documents for contradictory specifications (e.g. conflicting thermal thresholds between legacy and current manuals) and flags warnings that force human escalation.

### 2. Deterministic, Versioned Policy Engine
- **What it does:** Ensures corporate rules cannot be bypassed or "jailbroken" by prompt injection or model hallucination.
- **How it works:** Policies are stored in immutable YAML files (`rules.yaml`, `versions/policy-v*.yaml`). The engine evaluates:
  - **Action Risk Level:** `LOW` (ticket lookup), `MEDIUM` (technician dispatch), `HIGH` (equipment replacement, refunds).
  - **Financial Thresholds:** Any action with estimated cost > $5,000 automatically triggers an approval requirement.
  - **Permission Check:** Any action not explicitly allowed in the active policy version is rejected.

### 3. Multi-Channel Human-in-the-Loop Approvals
- **What it does:** Pauses high-risk operations and waits for human authorization before executing any changes.
- **How it works:** 
  - Generates a cryptographically signed approval token.
  - Dispatches approval requests with full evidence context via **Slack Interactive Buttons**, **Single-Use Email Links**, or the **Frontend Approval Center**.
  - Automatically handles timeouts and role-based approver escalation (e.g. routing to `service_manager` or `risk_director`).

### 4. Real Enterprise Connectors & Mock Fallbacks
- **What it does:** Connects seamlessly to existing IT service management systems.
- **How it works:** 
  - **Jira Cloud Sandbox:** Creates real Jira issues, assigns components, and updates issue transitions.
  - **Mock In-Memory Store:** Zero-dependency, offline-ready sandbox that replicates Jira behavior for local development and demos.

### 5. Post-Action State Verification
- **What it does:** Solves "hallucinated success" by verifying that an action actually took effect in reality.
- **How it works:** After an API reports success, a separate verification routine queries the external tool independently (e.g. queries the ticket store to verify ticket ID exists and status is `CREATED`). If the verification fails, the run is flagged as `VERIFICATION_FAILED` and escalated.

### 6. Tamper-Evident SHA-256 Cryptographic Audit Chain
- **What it does:** Provides enterprise compliance and forensic auditability.
- **How it works:** Each event is hashed with the previous record's hash, forming an append-only cryptographic chain in SQLite. Any tampering or retroactive modification invalidates the verification hash chain, which can be validated with one click from the UI or CLI.

### 7. Policy Simulator & Offline Replay
- **What it does:** Enables policy managers to test "what-if" rule changes against historical runs before deploying them live.
- **How it works:** Replays hundreds of historical agent runs against a proposed policy candidate and displays a diff: *"If we lower the approval threshold from $5,000 to $3,000, 14 previously autonomous runs will now require manager approval."*

### 8. Operational Insights & ROI Analytics
- **What it does:** Quantifies business value for executive stakeholders.
- **How it works:** Calculates automation rates, hours saved per incident (default: 15 minutes/case), manual labor costs avoided, and MTTR (mean time to resolution) improvements.

---

## 4. Technology Stack

| Layer | Technologies Used | Rationale |
| :--- | :--- | :--- |
| **Backend Framework** | **Python 3.13**, **FastAPI**, **Uvicorn** | High performance, native async support, automated OpenAPI docs. |
| **Data Validation** | **Pydantic v2**, **Pydantic Settings** | Strict schema validation at all boundaries; no raw dicts passed between components. |
| **LLM Orchestration** | **Google Gemini 2.0 Flash**, **OpenRouter** | Fast inference, structured JSON output mode, multi-provider fallback. |
| **Vector Database** | **ChromaDB** (Persistent Local Store) | Zero-external-dependency embedded vector database with metadata filtering. |
| **Relational Storage** | **SQLite (WAL Mode)** | Zero-maintenance, file-based ACID storage for run states, approvals, and audit events. |
| **External Integrations**| **Jira Cloud REST API**, **Slack Webhooks**, **SMTP** | Production-ready enterprise connectors with graceful mock fallbacks. |
| **Frontend Framework** | **React 19**, **TypeScript**, **Vite** | Modern, type-safe, ultra-responsive single-page cockpit. |
| **Styling & UI** | **Tailwind CSS v4**, **Lucide Icons**, **Framer Motion** | Dark-mode design system with visual status badges, steppers, and glassmorphism. |
| **Quality & Testing** | **Pytest**, **Pytest-Asyncio** | 68 automated unit, integration, and policy regression tests. |

---

## 5. The 3 Demo Scenarios (Presentation Walk-Through)

These three deterministic scenarios demonstrate every dimension of the system to judges or stakeholders:

---

### Scenario A: Autonomous Execution (Low/Medium Risk)
> **Pitch:** *"When evidence is unequivocal, the customer is under warranty, and policy permits, the agent resolves the ticket in seconds without human fatigue."*

* **User Prompt:**  
  `"Customer Acme Corp reports Product PX-100 overheating with error code E-401. Handle it."`
* **Behind the Scenes:**
  1. **Intent:** Identifies product `PX-100`, symptom `overheating`, error code `E-401`.
  2. **Evidence Retrieved:**
     - `SOP-042`: Specifies that thermal error `E-401` requires a field service inspection.
     - `MAN-PX100`: Confirms thermal shutoff threshold at 85°C.
     - `POL-WTY-001`: Confirms Acme Corp's warranty is active.
  3. **Confidence:** `0.94` (High confidence, zero contradictions).
  4. **Policy Evaluation:** `create_service_ticket` (LOW risk) and `assign_technician` (MEDIUM risk) are allowed.
  5. **Autonomy Decision:** **`EXECUTE`**.
  6. **Action & Verification:** Creates Service Ticket `TICK-001`, assigns certified HVAC technician `TECH-002`, and verifies state.
* **Presentation Highlight:** Show the live execution stepper moving through all 7 stages to `Completed` in under 2 seconds.

---

### Scenario B: Human Approval Gate (High Risk / High Cost)
> **Pitch:** *"The AI never makes high-stakes financial or hardware replacement commitments on its own. It prepares the work, then steps aside for human authorization."*

* **User Prompt:**  
  `"Compressor shattered on Machine PX-100 at Beta Industries. Replace the unit."`
* **Behind the Scenes:**
  1. **Intent:** Request to replace major capital equipment.
  2. **Evidence Retrieved:**
     - `POL-EQP-002`: Section 3 mandates manager approval for any equipment replacement exceeding $5,000.
     - Asset database flags replacement cost at $8,500.
  3. **Confidence:** `0.91`.
  4. **Policy Evaluation:** Action `replace_product` is classified as `HIGH` risk and exceeds financial threshold.
  5. **Autonomy Decision:** **`APPROVAL_REQUIRED`**.
  6. **Human Gate:** Agent pauses execution, generates an approval request, and routes it to the `service_manager`.
  7. **Approval Interaction:** Presenter clicks **"Approve Action"** in the UI (or demonstrates Slack/Email link).
  8. **Execution:** Action executes and completes with verified audit trail.
* **Presentation Highlight:** Show how the system halts, presents the human gate with cited policies, and only proceeds upon valid authorization.

---

### Scenario C: Safe Refusal / Escalation (Ambiguous / Insufficient Evidence)
> **Pitch:** *"A great AI knows when it does NOT know. Unlike typical chatbots that hallucinate plausible answers, Evidence-to-Action escalates safely when evidence is weak."*

* **User Prompt:**  
  `"Product PY-200 is making a strange humming noise. Can we run firmware reset?"`
* **Behind the Scenes:**
  1. **Intent:** Firmware reset request for `PY-200`.
  2. **Evidence Retrieved:**
     - Product manual for `PY-200` has ambiguous troubleshooting steps.
     - No SOP matches humming vibration symptoms for firmware reset.
  3. **Confidence Score:** `0.52` (Falls below the mandatory `0.70` threshold).
  4. **Policy Evaluation:** Fails evidence sufficiency gate.
  5. **Autonomy Decision:** **`ESCALATE`**.
  6. **Action Taken:** **Zero tool mutations executed**. The agent safely refuses autonomous action, explains the missing evidence gap, and logs a referral ticket for engineering review.
* **Presentation Highlight:** Emphasize enterprise safety—showing that preventing wrong actions is just as vital as automating right ones.

---

## 6. Presentation Slide-by-Slide Outline (5-Minute Pitch)

| Slide / Time | Topic | Key Talking Points | What to Show on Screen |
| :---: | :--- | :--- | :--- |
| **0:00 - 0:45** | **The Problem** | Enterprises want AI to *do things*, not just chat. But wild tool calling causes hallucinations and liability. | Problem slide / architecture failure of naive RAG. |
| **0:45 - 1:30** | **Our Innovation** | *"The LLM proposes; deterministic code authorizes."* 3-tier autonomy: Execute, Approve, Escalate. | High-Level Architecture Diagram. |
| **1:30 - 2:30** | **Live Demo 1: Autonomous** | Scenario A: Overheating under warranty. Agent retrieves evidence, checks policy, acts, verifies in 2 seconds. | **Agent Workspace (`/agent`)**: Show live stepper and cited SOP cards. |
| **2:30 - 3:30** | **Live Demo 2: Approval Gate** | Scenario B: $8,500 replacement. Policy intercepts the action, pauses, routes to manager. Human clicks Approve. | **Approval Center (`/approvals`)**: Click approve, show action finish. |
| **3:30 - 4:15** | **Compliance & Governance** | Cryptographic SHA-256 audit hash chain, Policy Simulator, and ROI Insights. | **Audit Page (`/audit`)** and **Insights Page (`/insights`)**. |
| **4:15 - 5:00** | **Q&A & Conclusion** | Production ready: Jira Cloud, Slack, Pydantic, 68 tests passing. Safe, verifiable enterprise AI. | Landing Page or Summary Slide. |

---

## 7. Key Talking Points for Judges & Stakeholders

1. **"Is this just LangChain / standard RAG?"**  
   *Answer:* "No. Standard RAG produces text answers. Evidence-to-Action is an **action execution and governance engine**. The LLM never touches tools directly; deterministic policy engines validate schemas, enforce dollar thresholds, verify external state, and sign an immutable audit chain."

2. **"How do you prevent prompt injection or jailbreaks?"**  
   *Answer:* "Even if a user tricks the LLM into proposing a malicious action, our policy engine is written in deterministic Python and versioned YAML outside the LLM context. If the action violates policy or exceeds risk thresholds, the code rejects or halts it regardless of what the LLM says."

3. **"How do you know the tool action actually worked?"**  
   *Answer:* "We implement post-action verification. We never trust the API return code alone; our verifier queries the tool's independent state to confirm the ticket or resource exists with the expected status."

4. **"Can enterprises customize policies without redeploying code?"**  
   *Answer:* "Yes. Policies are versioned in YAML. Using our Policy Center, administrators can update thresholds, test them in our offline simulator against historical runs, and deploy them with instant version tracking."

---

## 8. Quick Reference: Running the System

```bash
# Terminal 1 — Backend (FastAPI)
cd backend
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — Frontend (Vite + React)
cd frontend
npm run dev

# Run Full Test Suite
cd backend
.venv\Scripts\pytest
```

- **Web Dashboard:** [http://localhost:5173](http://localhost:5173)
- **Interactive API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)
