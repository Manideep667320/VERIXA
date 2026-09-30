# Evidence-to-Action Enterprise AI Agent

## Production-Oriented 36-Hour Hackathon Implementation Plan

**Target development environment:** Antigravity\
**Primary coding model:** Claude Sonnet\
**Document purpose:** Provide a precise implementation blueprint that
Claude Sonnet can follow to begin development immediately.

------------------------------------------------------------------------

# 1. Executive Summary

## 1.1 Product

Build an **Evidence-to-Action Enterprise AI Agent** that converts an
employee's natural-language request into a safe, evidence-backed,
policy-controlled workflow.

The system must go beyond traditional RAG:

> **Request → Evidence → Reasoning → Policy Check → Action / Approval →
> Verification → Audit**

The agent should not have unrestricted autonomy.

It must decide between three outcomes:

1.  **Execute** --- when evidence, policy, permissions, and risk allow
    autonomous execution.
2.  **Request approval** --- when the action is valid but requires human
    authorization.
3.  **Escalate / refuse** --- when evidence is insufficient,
    conflicting, or the action is not permitted.

## 1.2 Recommended hackathon domain

Do not build a generic enterprise automation platform.

For the 36-hour implementation, use one focused domain:

> **Customer / Field-Service Incident Resolution**

Example:

> "A customer reported that Product X is overheating. Handle it."

The agent retrieves:

-   Product manual
-   Maintenance SOP
-   Warranty policy
-   Previous incidents
-   Customer information
-   Technician availability

It then determines severity and the permitted next action, creates or
proposes a service ticket, assigns a technician when allowed, requests
approval when required, notifies the customer, verifies the actions, and
produces an evidence-backed audit trail.

## 1.3 Core value proposition

> **An AI agent that does not just answer enterprise questions. It uses
> enterprise evidence and policies to determine what it is allowed to
> do, acts when safe, asks humans when necessary, and records why it
> acted.**

------------------------------------------------------------------------

# 2. Jury Assessment and Strategic Positioning

## 2.1 Current market reality

Enterprise agent platforms already provide combinations of:

-   Enterprise RAG
-   Agent reasoning
-   Tool calling
-   Workflow orchestration
-   Approvals
-   Governance
-   Enterprise integrations

Therefore, the project must **not** claim that "RAG + agents + APIs" is
itself novel.

The differentiation should be demonstrated through:

-   Evidence-backed decisions
-   Explicit action authorization
-   Risk-based autonomy
-   Human approval gates
-   Refusal when evidence is insufficient
-   Post-action verification
-   Transparent audit trails

## 2.2 What not to build

Do not attempt to build:

-   A replacement for ServiceNow
-   A replacement for Microsoft Copilot
-   A complete ERP/CRM
-   A generic enterprise operating system
-   Dozens of integrations
-   Six or more cooperating agents
-   Fully autonomous unrestricted API access
-   A large production identity and permissions platform

These are outside the 36-hour scope.

## 2.3 Project thesis

The system should prove:

> **Enterprise AI should not jump directly from retrieved knowledge to
> API execution. It needs an intermediate decision-control layer.**

The decision-control layer evaluates:

``` text
Evidence
+
Policy
+
Permission
+
Risk
+
Confidence
        ↓
Autonomy Decision
```

------------------------------------------------------------------------

# 3. Final Problem Statement

## 3.1 Professional version

Enterprise employees work with information distributed across SOPs,
manuals, policies, incident records, customer records, and operational
systems. Existing AI assistants can retrieve and summarize this
information, but converting that knowledge into reliable business
actions still requires manual interpretation, authorization, and system
updates.

Build an AI agent that understands an employee's request, retrieves and
cross-validates relevant enterprise evidence, reasons over that
evidence, determines the appropriate workflow, checks business policies,
permissions, risk, and confidence, and then either executes an
authorized action, routes the action for human approval, or escalates
when evidence is insufficient.

Every important decision and action must maintain an evidence-backed
audit trail, and executed actions must be verified for successful
completion.

## 3.2 Short version

> **Build an AI agent that converts enterprise requests into
> evidence-backed, policy-compliant workflows, executing low-risk
> actions automatically while routing risky or uncertain decisions for
> human approval.**

------------------------------------------------------------------------

# 4. Product Goals

## 4.1 Must-have goals

The MVP must:

-   Accept natural-language employee requests.
-   Retrieve relevant enterprise knowledge.
-   Combine evidence from multiple source types.
-   Generate a structured decision.
-   Identify a proposed workflow.
-   Evaluate policy and risk.
-   Decide whether to execute, request approval, or escalate.
-   Execute bounded actions through tools/APIs.
-   Verify action results.
-   Display evidence supporting the decision.
-   Maintain an audit trail.

## 4.2 Nice-to-have goals

If time permits:

-   Streaming agent activity.
-   Confidence visualization.
-   More enterprise source types.
-   Additional workflow templates.
-   Role-based login.
-   Editable policy rules.
-   Human approval dashboard.
-   Action replay/debugging.
-   Evaluation metrics dashboard.

## 4.3 Explicit non-goals

Do not implement:

-   Real financial transactions.
-   Real customer communications without sandbox/mock controls.
-   Destructive production operations.
-   Enterprise-grade SSO.
-   Full RBAC administration.
-   Large-scale distributed deployment.
-   Autonomous unrestricted shell access.
-   Arbitrary LLM-generated API calls.

------------------------------------------------------------------------

# 5. Core User Journey

## 5.1 Primary workflow

``` text
Employee Request
      ↓
Intent Extraction
      ↓
Entity Identification
      ↓
Evidence Retrieval
      ↓
Evidence Cross-Validation
      ↓
Agent Reasoning
      ↓
Action Plan
      ↓
Policy / Permission / Risk Check
      ↓
 ┌───────────────┬──────────────────┐
 │               │                  │
 ▼               ▼                  ▼
EXECUTE       APPROVAL           ESCALATE
 │               │                  │
 ▼               ▼                  ▼
Tool Call     Human Review      Ask/Stop
 │               │
 ▼               ▼
Verification ←───┘
      ↓
Audit Record
      ↓
Final Response
```

------------------------------------------------------------------------

# 6. Three Mandatory Demo Scenarios

The entire hackathon demo should revolve around these three cases.

## Scenario A --- Autonomous Low-Risk Action

### Input

> "Customer reports that Product X is overheating. The customer is under
> warranty. Create a service case and assign an available technician."

### Expected behavior

1.  Retrieve product information.
2.  Retrieve maintenance SOP.
3.  Retrieve warranty policy.
4.  Retrieve technician availability.
5.  Determine that the action is allowed.
6.  Create service ticket.
7.  Assign technician.
8.  Verify both operations.
9.  Record evidence and action results.

### Outcome

**EXECUTED**

------------------------------------------------------------------------

## Scenario B --- Human Approval Required

### Input

> "The customer's machine has a severe failure. Arrange a replacement
> unit."

### Expected behavior

1.  Retrieve failure SOP.
2.  Retrieve warranty/replacement policy.
3.  Determine replacement is permitted but requires manager approval.
4.  Generate action plan.
5.  Pause execution.
6.  Show approval request.
7.  Human approves.
8.  Execute replacement workflow.
9.  Verify.
10. Record audit trail.

### Outcome

**WAITING FOR APPROVAL → APPROVED → EXECUTED**

------------------------------------------------------------------------

## Scenario C --- Insufficient / Conflicting Evidence

### Input

> "The customer wants us to immediately replace Product Y because it is
> overheating."

### Expected behavior

1.  Retrieve available documents.
2.  Discover that Product Y's replacement conditions are unclear or
    conflicting.
3.  Do not invent a policy.
4.  Do not execute replacement.
5.  Explain missing/conflicting evidence.
6.  Escalate to a human.

### Outcome

**ESCALATED --- NO ACTION TAKEN**

This scenario is critical. It demonstrates bounded autonomy rather than
a chatbot that always tries to satisfy the user.

------------------------------------------------------------------------

# 7. Functional Architecture

``` text
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND                            │
│ Chat | Evidence | Decision | Approval | Audit           │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  FASTAPI BACKEND                         │
│                                                         │
│  Request API                                            │
│  Agent Orchestrator                                     │
│  Approval API                                           │
│  Audit API                                              │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              AGENT DECISION LAYER                       │
│                                                         │
│ Intent / Entity Extraction                              │
│ Retrieval                                               │
│ Reasoning                                               │
│ Workflow Planning                                       │
│ Policy Evaluation                                       │
│ Risk Evaluation                                         │
│ Autonomy Decision                                       │
└───────────────┬───────────────────────┬─────────────────┘
                │                       │
                ▼                       ▼
┌────────────────────────┐   ┌────────────────────────────┐
│ KNOWLEDGE LAYER        │   │ ACTION LAYER               │
│                        │   │                            │
│ Documents              │   │ Ticket Tool                │
│ SOPs                   │   │ Technician Tool            │
│ Manuals                │   │ Notification Tool          │
│ Policies               │   │ Approval Tool              │
│ Incidents              │   │ Customer Tool              │
└────────────┬───────────┘   └──────────────┬─────────────┘
             │                              │
             ▼                              ▼
       Vector Store                    Mock Enterprise APIs
             │                              │
             └──────────────┬───────────────┘
                            ▼
                     VERIFICATION
                            │
                            ▼
                       AUDIT STORE
```

------------------------------------------------------------------------

# 8. Recommended Technical Stack

Use technologies that the team can implement quickly and reliably.

## Frontend

-   React
-   TypeScript
-   Vite
-   Tailwind CSS
-   Optional component library if already familiar

## Backend

-   Python
-   FastAPI
-   Pydantic
-   Uvicorn

## Agent orchestration

Preferred:

-   LangGraph or a lightweight explicit state-machine implementation

Do not add an orchestration framework merely for branding. If a simple
deterministic state graph is faster and easier to debug, use it.

## LLM

Use the model/API available to the hackathon environment.

The application must abstract the LLM behind a provider interface:

``` text
LLMProvider
├── generate()
├── structured_output()
└── stream()
```

This allows the model to be changed without rewriting the application.

## Embeddings

Use a reliable embedding model available in the environment.

## Vector database

For the hackathon:

-   ChromaDB or FAISS

Choose one.

Do not build a custom vector database layer.

## Metadata / operational database

Use:

-   SQLite for maximum speed

or:

-   MongoDB if the team already has a working MongoDB stack.

Recommended for 36 hours:

> **SQLite for operational records + ChromaDB for vector retrieval**

## Mock enterprise systems

Expose them as internal FastAPI services/modules:

-   Customer Service
-   Service Ticket
-   Technician Assignment
-   Notification
-   Approval

They must behave like real APIs even if their data is local.

------------------------------------------------------------------------

# 9. Repository Structure

Recommended structure:

``` text
evidence-to-action/
│
├── README.md
├── .env.example
├── docker-compose.yml
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   ├── routes_agent.py
│   │   │   ├── routes_approval.py
│   │   │   ├── routes_audit.py
│   │   │   └── routes_health.py
│   │   │
│   │   ├── agent/
│   │   │   ├── state.py
│   │   │   ├── graph.py
│   │   │   ├── planner.py
│   │   │   ├── reasoning.py
│   │   │   └── decision.py
│   │   │
│   │   ├── knowledge/
│   │   │   ├── ingestion.py
│   │   │   ├── retrieval.py
│   │   │   ├── chunking.py
│   │   │   └── embeddings.py
│   │   │
│   │   ├── policy/
│   │   │   ├── engine.py
│   │   │   ├── rules.py
│   │   │   └── risk.py
│   │   │
│   │   ├── tools/
│   │   │   ├── tickets.py
│   │   │   ├── technicians.py
│   │   │   ├── customers.py
│   │   │   ├── notifications.py
│   │   │   └── approvals.py
│   │   │
│   │   ├── verification/
│   │   │   └── verifier.py
│   │   │
│   │   ├── audit/
│   │   │   └── logger.py
│   │   │
│   │   ├── models/
│   │   │   ├── request.py
│   │   │   ├── evidence.py
│   │   │   ├── decision.py
│   │   │   ├── action.py
│   │   │   ├── approval.py
│   │   │   └── audit.py
│   │   │
│   │   └── core/
│   │       ├── config.py
│   │       └── constants.py
│   │
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── types/
│   │   └── App.tsx
│   └── package.json
│
├── data/
│   ├── knowledge/
│   │   ├── manuals/
│   │   ├── sops/
│   │   ├── policies/
│   │   └── incidents/
│   │
│   ├── customers/
│   ├── technicians/
│   └── seed/
│
├── scripts/
│   ├── ingest.py
│   └── seed_data.py
│
└── docs/
    ├── architecture.md
    ├── api.md
    └── demo-script.md
```

------------------------------------------------------------------------

# 10. Core Agent State

The agent should use a structured state object.

``` python
class AgentState:
    request: str
    intent: str
    entities: dict

    evidence: list
    evidence_confidence: float

    proposed_actions: list

    policy_result: str
    risk_level: str
    permission_result: str

    autonomy_decision: str
    approval_required: bool

    execution_results: list
    verification_results: list

    final_response: str
    audit_id: str
```

Avoid allowing arbitrary LLM text to control execution.

------------------------------------------------------------------------

# 11. Action Contract

Every executable action must follow a strict schema.

Example:

``` json
{
  "action": "create_service_ticket",
  "arguments": {
    "customer_id": "CUS-102",
    "product_id": "PROD-X",
    "severity": "HIGH"
  },
  "reason": "Customer reported overheating",
  "evidence_ids": [
    "SOP-042",
    "MANUAL-X-7.3",
    "INC-1832"
  ],
  "risk_level": "LOW",
  "requires_approval": false
}
```

The LLM proposes the action.

The application decides whether the action can execute.

**Never let the LLM directly determine whether it has permission to
execute an arbitrary tool.**

------------------------------------------------------------------------

# 12. Policy Engine

Use deterministic rules wherever possible.

Example:

``` python
POLICIES = {
    "create_ticket": {
        "allowed": True,
        "max_risk": "HIGH"
    },
    "assign_technician": {
        "allowed": True,
        "max_risk": "MEDIUM"
    },
    "replace_product": {
        "allowed": True,
        "requires_approval": True
    },
    "issue_refund": {
        "allowed": True,
        "requires_approval_above": 50000
    }
}
```

The LLM can interpret context.

The policy engine makes the final authorization decision.

------------------------------------------------------------------------

# 13. Risk Model

Use three simple levels:

## LOW

Examples:

-   Search knowledge
-   Create draft
-   Create internal ticket
-   Retrieve customer information

Can generally execute automatically.

## MEDIUM

Examples:

-   Assign technician
-   Send customer communication
-   Change operational status

Execute only if policy permits.

## HIGH

Examples:

-   Product replacement
-   Large refund
-   Contract changes
-   Irreversible operations

Require human approval.

## UNKNOWN

If risk cannot be established:

> **Do not execute. Escalate.**

------------------------------------------------------------------------

# 14. Evidence Model

Every evidence item should contain:

``` json
{
  "id": "SOP-042",
  "source": "maintenance_sop.pdf",
  "section": "Overheating Procedure",
  "text": "...",
  "relevance_score": 0.91,
  "metadata": {
    "document_type": "SOP",
    "version": "3.2"
  }
}
```

The final decision must reference evidence IDs.

------------------------------------------------------------------------

# 15. Retrieval Strategy

Do not simply retrieve the top five chunks and pass them blindly to the
LLM.

Pipeline:

``` text
Query
 ↓
Intent / entity extraction
 ↓
Metadata filters
 ↓
Semantic retrieval
 ↓
Top-K results
 ↓
Optional reranking
 ↓
Evidence grouping
 ↓
LLM reasoning
```

Prioritize:

1.  Current policy
2.  Relevant SOP
3.  Product manual
4.  Recent incidents
5.  Customer information

Where possible, metadata should include:

-   document type
-   product
-   department
-   version
-   date
-   policy status

------------------------------------------------------------------------

# 16. Verification Layer

Every tool should return structured results.

Example:

``` json
{
  "success": true,
  "action_id": "ACT-1042",
  "ticket_id": "TKT-2048"
}
```

The verifier then checks the operational state.

Example:

``` text
create_ticket()
      ↓
ticket_id returned
      ↓
get_ticket(ticket_id)
      ↓
status == CREATED
      ↓
VERIFIED
```

This is a key differentiating feature.

------------------------------------------------------------------------

# 17. Audit Trail

Store:

``` text
Audit ID
Timestamp
User Request
Intent
Retrieved Evidence
Reasoning Summary
Risk Level
Policy Result
Proposed Actions
Approval
Executed Actions
Execution Results
Verification Results
Final Response
```

Do not store hidden chain-of-thought.

Store concise, user-facing **decision rationale** and evidence
references instead.

Example:

> "The replacement requires manager approval because the warranty policy
> requires approval for high-severity replacement requests."

That is sufficient.

------------------------------------------------------------------------

# 18. Frontend Requirements

Keep the interface simple.

## Screen 1 --- Agent

Left:

-   Chat/request input

Center:

-   Agent activity
-   Current status

Right:

-   Evidence
-   Decision
-   Risk
-   Policy
-   Actions

Example:

``` text
REQUEST
Customer reports overheating

EVIDENCE
✓ SOP-042
✓ Product Manual
✓ Incident #1832

DECISION
High severity

POLICY
Technician assignment allowed

ACTION
Create ticket
Assign technician

STATUS
✓ Completed
```

------------------------------------------------------------------------

# 19. Approval UI

When approval is required:

``` text
┌─────────────────────────────────────────┐
│ APPROVAL REQUIRED                       │
│                                         │
│ Action: Replace Product X               │
│ Risk: HIGH                              │
│                                         │
│ Reason: Warranty policy requires        │
│ manager approval.                       │
│                                         │
│ Evidence:                               │
│ • Warranty Policy 4.1                   │
│ • Incident #1832                        │
│                                         │
│ [ APPROVE ]       [ REJECT ]            │
└─────────────────────────────────────────┘
```

After approval:

``` text
Approval
   ↓
Action execution
   ↓
Verification
```

------------------------------------------------------------------------

# 20. Audit UI

Display a chronological timeline:

``` text
12:03 Request received
12:03 Evidence retrieved
12:04 Decision generated
12:04 Policy checked
12:04 Approval requested
12:06 Approval granted
12:06 Ticket created
12:06 Technician assigned
12:07 Customer notified
12:07 Actions verified
```

This should be visually clear during the demo.

------------------------------------------------------------------------

# 21. API Design

Minimum APIs:

``` text
POST /api/agent/run
GET  /api/agent/{id}

POST /api/approvals/{id}/approve
POST /api/approvals/{id}/reject

GET  /api/audit/{id}

POST /api/tools/tickets
GET  /api/tools/tickets/{id}

POST /api/tools/technicians/assign

POST /api/tools/notifications

GET  /api/health
```

Agent response example:

``` json
{
  "run_id": "RUN-001",
  "status": "approval_required",
  "decision": {
    "risk": "HIGH",
    "reason": "Replacement requires manager approval"
  },
  "evidence": [],
  "actions": [],
  "approval_id": "APR-001"
}
```

------------------------------------------------------------------------

# 22. Data Model

Minimum entities:

## Document

``` text
id
title
type
version
status
content
metadata
created_at
```

## Customer

``` text
id
name
product_ids
warranty_status
contact
```

## Incident

``` text
id
customer_id
product_id
description
severity
resolution
date
```

## Technician

``` text
id
name
skills
availability
location
```

## Action

``` text
id
type
arguments
status
risk
evidence_ids
approval_required
created_at
```

## Approval

``` text
id
action_id
reason
status
approved_by
timestamp
```

## Audit

``` text
id
run_id
events
created_at
```

------------------------------------------------------------------------

# 23. Agent Orchestration

Use an explicit graph.

Recommended nodes:

``` text
START
  ↓
UNDERSTAND_REQUEST
  ↓
RETRIEVE_EVIDENCE
  ↓
ASSESS_EVIDENCE
  ↓
PLAN_ACTION
  ↓
POLICY_CHECK
  ↓
RISK_CHECK
  ↓
AUTONOMY_DECISION
  ├── EXECUTE
  │     ↓
  │  VERIFY
  │     ↓
  │   AUDIT
  │
  ├── APPROVAL
  │     ↓
  │  WAIT
  │     ↓
  │  EXECUTE
  │     ↓
  │  VERIFY
  │     ↓
  │   AUDIT
  │
  └── ESCALATE
        ↓
      AUDIT
```

Avoid uncontrolled recursive agent loops.

Set maximum reasoning/tool iterations.

------------------------------------------------------------------------

# 24. Prompting Strategy

Use separate prompts for distinct responsibilities.

## Intent prompt

Extract:

-   request type
-   entities
-   desired outcome
-   urgency

Return structured JSON.

## Reasoning prompt

Given evidence:

-   summarize relevant facts
-   identify contradictions
-   determine confidence
-   propose actions
-   cite evidence IDs

## Action planning prompt

Return only structured action contracts.

## Final response prompt

Explain:

-   what was found
-   what was decided
-   what happened
-   what remains pending

Do not expose private chain-of-thought.

------------------------------------------------------------------------

# 25. Guardrails

Mandatory guardrails:

1.  No arbitrary tool calls.
2.  No arbitrary SQL generated by the LLM.
3.  No shell command execution.
4.  No destructive action without policy authorization.
5.  No high-risk action without approval.
6.  No action when evidence is insufficient.
7.  All actions require structured arguments.
8.  All actions produce execution results.
9.  Important actions must be verified.
10. Every run gets an audit ID.
11. Tool permissions are enforced outside the LLM.
12. LLM output must be schema validated.

------------------------------------------------------------------------

# 26. Seed Knowledge Base

Create a small but realistic dataset.

Recommended:

### 5 SOPs

Examples:

-   Overheating response SOP
-   Equipment failure SOP
-   Customer escalation SOP
-   Technician dispatch SOP
-   Product replacement SOP

### 5 policies

Examples:

-   Warranty policy
-   Replacement policy
-   Refund policy
-   Approval policy
-   Customer communication policy

### 10 historical incidents

Include:

-   similar incidents
-   different resolutions
-   severity
-   dates
-   products

### 10 customers

Include:

-   product
-   warranty
-   contact
-   service history

### 5 technicians

Include:

-   skill
-   location
-   availability

This is enough to produce realistic retrieval and decisions.

------------------------------------------------------------------------

# 27. 36-Hour Execution Plan

## Hours 0--3 --- Foundation

### Deliverables

-   Repository
-   Environment
-   Backend skeleton
-   Frontend skeleton
-   Database
-   Configuration
-   Basic health endpoint

### Claude Sonnet instruction

Build the project skeleton and verify that frontend, backend, and
database run independently.

------------------------------------------------------------------------

## Hours 3--7 --- Knowledge Layer

Implement:

-   document ingestion
-   chunking
-   embeddings
-   vector store
-   metadata
-   retrieval API

Load the seed documents.

### Acceptance test

Given:

> "What is the overheating procedure for Product X?"

The system retrieves the correct SOP/manual sections.

------------------------------------------------------------------------

## Hours 7--11 --- Agent Core

Implement:

-   request understanding
-   entity extraction
-   evidence retrieval
-   structured reasoning
-   action planning

### Acceptance test

Given the primary incident request, the agent produces a structured
action plan with evidence IDs.

------------------------------------------------------------------------

## Hours 11--15 --- Policy and Risk

Implement:

-   policy engine
-   risk classifier
-   permission checks
-   autonomy decision

### Acceptance test

Same action produces different behavior depending on policy/risk.

------------------------------------------------------------------------

## Hours 15--20 --- Tool Layer

Implement:

-   ticket creation
-   technician assignment
-   customer lookup
-   notification
-   approval

All as structured APIs.

### Acceptance test

Agent can execute a low-risk workflow end-to-end.

------------------------------------------------------------------------

## Hours 20--23 --- Verification + Audit

Implement:

-   execution verification
-   audit event logging
-   run IDs
-   evidence/action trace

### Acceptance test

Every action produces a verifiable audit record.

------------------------------------------------------------------------

## Hours 23--27 --- Frontend

Build:

-   chat
-   evidence panel
-   decision panel
-   action status
-   approval modal
-   audit timeline

Do not over-design.

The UI should make the agent's decision process understandable in
seconds.

------------------------------------------------------------------------

## Hours 27--30 --- Three Scenarios

Implement and test:

1.  Autonomous execution
2.  Approval required
3.  Insufficient evidence

Freeze core architecture after this point.

------------------------------------------------------------------------

## Hours 30--33 --- Testing + Failure Handling

Test:

-   invalid input
-   missing evidence
-   conflicting evidence
-   tool failure
-   approval rejection
-   duplicate requests
-   invalid action arguments
-   policy denial
-   verification failure

------------------------------------------------------------------------

## Hours 33--35 --- Demo Preparation

Prepare:

-   seeded database
-   stable scenarios
-   presentation
-   architecture diagram
-   3-minute demo
-   backup screenshots/video

------------------------------------------------------------------------

## Hours 35--36 --- Freeze

Do not add new features.

Only:

-   fix critical bugs
-   verify deployment
-   rehearse
-   ensure demo data is deterministic

------------------------------------------------------------------------

# 28. Definition of Done

The project is complete when all of the following work:

### Knowledge

-   [ ] Documents ingest successfully.
-   [ ] Retrieval returns relevant evidence.
-   [ ] Evidence contains source metadata.
-   [ ] Evidence can be displayed to the user.

### Agent

-   [ ] Natural-language request is understood.
-   [ ] Entities are extracted.
-   [ ] Evidence is evaluated.
-   [ ] Structured action plan is generated.

### Policy

-   [ ] Risk is assigned.
-   [ ] Policy is checked.
-   [ ] Unauthorized actions are blocked.
-   [ ] High-risk actions require approval.
-   [ ] Insufficient evidence causes escalation.

### Execution

-   [ ] Tools execute through structured APIs.
-   [ ] Tool arguments are schema validated.
-   [ ] Tool results are stored.
-   [ ] Execution failures are handled.

### Verification

-   [ ] Successful actions are verified.
-   [ ] Failed actions are reported.
-   [ ] Final state reflects actual tool state.

### Audit

-   [ ] Every run has an ID.
-   [ ] Evidence is recorded.
-   [ ] Decision rationale is recorded.
-   [ ] Actions are recorded.
-   [ ] Approvals are recorded.
-   [ ] Verification is recorded.

### UI

-   [ ] User can submit a request.
-   [ ] User can see evidence.
-   [ ] User can see decision.
-   [ ] User can approve/reject.
-   [ ] User can see action status.
-   [ ] User can inspect audit timeline.

------------------------------------------------------------------------

# 29. Evaluation Metrics

Do not claim enterprise production accuracy without testing.

Measure the prototype on:

## Retrieval accuracy

Percentage of test questions where relevant evidence appears in top-K.

## Decision accuracy

Percentage of scenarios where the correct action/approval/escalation
state is selected.

## Policy compliance

Percentage of prohibited actions successfully blocked.

## Evidence grounding

Percentage of decisions that reference valid supporting evidence.

## Action success

Percentage of permitted tool actions completed successfully.

## Verification accuracy

Percentage of executed actions where the system correctly identifies
success/failure.

## Escalation correctness

Percentage of insufficient-evidence cases correctly escalated.

Create at least 15--20 deterministic evaluation cases.

------------------------------------------------------------------------

# 30. Testing Matrix

  Test                      Expected
  ------------------------- -------------------
  Valid low-risk request    Execute
  Valid high-risk request   Approval
  Missing evidence          Escalate
  Conflicting policy        Escalate
  Unauthorized action       Block
  Tool failure              Report failure
  Verification failure      Mark failed
  Approval rejected         Stop
  Invalid tool arguments    Reject
  Duplicate execution       Prevent duplicate
  Unsupported request       Escalate
  Strong evidence           High confidence
  Weak evidence             Low confidence

------------------------------------------------------------------------

# 31. Security Model

Even in a hackathon, demonstrate the right architecture.

The key principle:

> **The LLM proposes; deterministic application code authorizes and
> executes.**

Do not let the model directly control:

-   database writes
-   arbitrary URLs
-   shell commands
-   credentials
-   unrestricted APIs

Tools should have explicit schemas and permissions.

Example:

``` text
LLM
 ↓
Action Proposal
 ↓
Schema Validation
 ↓
Policy Engine
 ↓
Permission Check
 ↓
Tool Execution
```

------------------------------------------------------------------------

# 32. Failure Handling

## Retrieval failure

Return:

> "I could not find sufficient enterprise evidence to safely determine
> the next action."

Do not hallucinate.

## Policy failure

Return:

> "The requested action is not permitted under the current policy."

## Tool failure

Return:

> "The action was approved but could not be completed. No successful
> execution is being claimed."

## Verification failure

Return:

> "The system submitted the action, but could not verify completion."

This distinction is important.

------------------------------------------------------------------------

# 33. Demo Script

## Opening --- 20 seconds

> "Traditional enterprise RAG can tell an employee what the company
> knows. Our system focuses on the next problem: what should actually be
> done, and is the AI allowed to do it?"

## Scenario 1 --- 60 seconds

Submit:

> "Customer reports Product X overheating. Handle it."

Show:

``` text
Evidence found
↓
Severity identified
↓
Policy checked
↓
Ticket created
↓
Technician assigned
↓
Verified
```

## Scenario 2 --- 45 seconds

Submit:

> "Replace the failed machine."

Show:

``` text
Evidence
↓
High-risk action
↓
Approval required
↓
Human approval
↓
Execution
```

## Scenario 3 --- 45 seconds

Submit an ambiguous request.

Show:

``` text
Evidence conflict
↓
Confidence insufficient
↓
No action
↓
Human escalation
```

## Closing --- 20 seconds

> "Our goal isn't to give an AI unrestricted access to enterprise
> systems. We give it evidence, bounded actions, policies, and
> verification. The result is an agent that can act when it should, ask
> when it must, and explain what it did."

------------------------------------------------------------------------

# 34. Antigravity Development Instructions for Claude Sonnet

Use the following as the initial implementation directive.

``` text
You are the senior implementation engineer for this project.

Build the Evidence-to-Action Enterprise AI Agent according to plan.md.

Primary objective:
Create a working 36-hour hackathon MVP for customer/field-service incident resolution.

Core flow:
Request
→ Intent
→ Evidence Retrieval
→ Evidence Assessment
→ Action Planning
→ Policy/Risk Check
→ Execute OR Approval OR Escalate
→ Verify
→ Audit

Important architectural rule:
The LLM must never directly authorize arbitrary actions.

The LLM may:
- interpret requests
- retrieve/interpret evidence
- propose actions
- explain decisions

Deterministic application code must:
- validate action schemas
- check policy
- check permissions
- enforce risk thresholds
- execute tools
- verify results
- write audit records

Implement in this order:

1. Repository and environment
2. FastAPI backend
3. Data models
4. Seed data
5. Knowledge ingestion
6. Retrieval
7. Agent state/graph
8. Policy engine
9. Risk engine
10. Action contracts
11. Mock enterprise tools
12. Approval workflow
13. Verification
14. Audit logging
15. Frontend
16. End-to-end tests
17. Demo scenarios

Before adding optional features, make the primary workflow work end-to-end.

Do not over-engineer.

Do not add multiple autonomous agents unless there is a demonstrated need.

Prefer deterministic services over unnecessary agent-to-agent communication.

Every important action must have:
- evidence IDs
- reason
- risk
- policy result
- approval requirement
- execution result
- verification result

Implement robust failure handling.

If evidence is insufficient or contradictory, the system must not invent an answer or action.

If an action requires approval, execution must stop until approval is received.

Create automated tests for:
- autonomous action
- approval-required action
- insufficient evidence
- policy denial
- tool failure
- verification failure

After each major implementation phase:
1. run tests
2. fix errors
3. update documentation
4. verify the application still runs

Do not build features outside the MVP until all core acceptance criteria in plan.md are passing.
```

------------------------------------------------------------------------

# 35. Development Priority

If time becomes limited, use this priority order:

### P0 --- Absolutely required

1.  RAG
2.  Agent reasoning
3.  Structured action plan
4.  Policy engine
5.  Risk decision
6.  Tool execution
7.  Approval flow
8.  Verification
9.  Audit trail
10. Three demo scenarios

### P1 --- Important

11. Good UI
12. Metadata filtering
13. Failure handling
14. Automated tests
15. Evaluation metrics

### P2 --- Only if time remains

16. Streaming
17. Multiple domains
18. Additional connectors
19. Advanced analytics
20. Multi-agent architecture

------------------------------------------------------------------------

# 36. Final Architecture Principle

The system must enforce this boundary:

``` text
                 ┌──────────────────┐
                 │       LLM        │
                 │                  │
                 │ Understand       │
                 │ Retrieve         │
                 │ Reason           │
                 │ Plan             │
                 └────────┬─────────┘
                          │
                    Action Proposal
                          │
                          ▼
                 ┌──────────────────┐
                 │ DETERMINISTIC    │
                 │ CONTROL LAYER    │
                 │                  │
                 │ Schema           │
                 │ Policy           │
                 │ Permission       │
                 │ Risk             │
                 │ Approval         │
                 └────────┬─────────┘
                          │
                     Authorized
                          │
                          ▼
                 ┌──────────────────┐
                 │ ACTION TOOLS     │
                 │                  │
                 │ Ticket           │
                 │ Technician       │
                 │ Notification     │
                 │ Customer         │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │   VERIFICATION   │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │   AUDIT TRAIL    │
                 └──────────────────┘
```

This separation is one of the most important technical decisions in the
entire project.

------------------------------------------------------------------------

# 37. Final Jury Verdict

## Problem

**Strong and relevant**, but only after narrowing it to a specific
operational workflow.

## Technical solution

**Strong**, provided the team implements bounded autonomy instead of
pretending the LLM itself is a secure workflow engine.

## Innovation

The innovation should be framed around:

> **Evidence-backed + policy-controlled + risk-aware + verifiable
> action**

---not generic RAG or generic agents.

## 36-hour feasibility

**Achievable as a focused prototype.**

Not achievable as a complete enterprise platform.

## Winning potential

The project has strong demo potential because it can visibly
demonstrate:

> **AI acts → AI asks for approval → AI refuses to act**

That gives the jury a concrete way to understand the difference between
a chatbot and an action-oriented enterprise agent.

## Final product statement

> **Evidence-to-Action is a policy-aware enterprise AI agent that turns
> organizational knowledge into accountable actions. It retrieves
> evidence, reasons over it, checks risk and authorization, executes
> only permitted workflows, asks humans when required, verifies
> outcomes, and maintains a complete audit trail.**

**Build one workflow extremely well. Do not build an enterprise platform
in 36 hours.**
