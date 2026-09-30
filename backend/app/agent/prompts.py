"""LLM prompt templates — one per agent responsibility."""

# Each prompt is a function that returns the formatted prompt string.
# This keeps prompts co-located, versionable, and testable.

SYSTEM_PROMPT = """You are an enterprise AI agent for customer/field-service incident resolution.
You retrieve evidence, reason over it, and propose structured actions.
You NEVER fabricate evidence, policies, or permissions.
You ALWAYS cite evidence IDs when making decisions.
If evidence is insufficient or conflicting, you escalate — you do NOT guess."""


def intent_extraction_prompt(request: str) -> str:
    return f"""Analyze the following employee request and extract structured information.

REQUEST: {request}

Extract:
- request_type: the type of request (incident_report, replacement_request, refund_request, general_inquiry)
- entities: dict with keys like customer_id, product_id, severity, etc.
- desired_outcome: what the employee wants to happen
- urgency: LOW, MEDIUM, HIGH, CRITICAL

Respond ONLY with valid JSON."""


def reasoning_prompt(request: str, evidence_texts: list[str]) -> str:
    evidence_block = "\n\n".join(f"[Evidence {i+1}]: {e}" for i, e in enumerate(evidence_texts))
    return f"""Given the following request and retrieved evidence, provide structured reasoning.

REQUEST: {request}

EVIDENCE:
{evidence_block}

Analyze:
1. Summarize relevant facts from the evidence
2. Identify any contradictions or gaps
3. Determine confidence level (0.0 to 1.0)
4. Propose specific actions with evidence IDs
5. Assess severity (LOW, MEDIUM, HIGH, CRITICAL)

Respond ONLY with valid JSON."""


def action_planning_prompt(request: str, reasoning: str, entities: dict) -> str:
    return f"""Based on the reasoning below, generate structured action contracts.

REQUEST: {request}
REASONING: {reasoning}
ENTITIES: {entities}

For each action, provide:
- action_type: one of [create_service_ticket, assign_technician, lookup_customer, send_notification]
- arguments: dict of required parameters
- reason: why this action is needed
- evidence_ids: list of evidence IDs supporting this action

Respond ONLY with a JSON array of action objects."""


def final_response_prompt(request: str, actions_summary: str, status: str) -> str:
    return f"""Generate a clear, professional response for the employee.

ORIGINAL REQUEST: {request}
ACTIONS TAKEN: {actions_summary}
STATUS: {status}

Explain:
1. What was found
2. What was decided
3. What happened (or what is pending)
4. What remains (if anything)

Keep it concise and professional. Do NOT expose internal reasoning chains."""
