# SOP-071: Critical Incident Escalation Procedures

**Document ID:** SOP-071
**Version:** 1
**Category:** Standard Operating Procedure
**Effective Date:** 2024-06-15
**Last Reviewed:** 2025-07-01
**Owner:** Risk & Compliance
**Applies To:** All support tiers, automated agent systems

---

## 1. Purpose

Define the mandatory escalation paths for critical incidents that exceed the authority or capability of front-line support agents and automated systems. This includes situations requiring human judgment, financial authorization, or safety intervention.

## 2. Escalation Triggers

### 2.1 Automatic Escalation (System-Initiated)
- Equipment replacement cost exceeds **$5,000** (requires manager approval per POL-EQP-002).
- Evidence confidence score is below **0.70** (insufficient basis for autonomous action).
- Conflicting evidence found across multiple knowledge sources.
- Customer has escalated the same issue 3+ times in 60 days.

### 2.2 Agent-Initiated Escalation
- The automated agent cannot identify a matching SOP for the reported issue.
- The customer reports a safety hazard (smoke, electrical sparks, chemical leak).
- The customer disputes a warranty determination.

## 3. Escalation Levels

| Level | Authority | Scope |
|-------|-----------|-------|
| L1 | Senior Support Agent | Override ticket severity, extend SLA |
| L2 | Operations Manager | Authorize dispatch outside SLA, approve overtime |
| L3 | Regional Director | Approve equipment replacement > $5,000, waive policy |
| L4 | VP Operations | Safety incidents, legal exposure, PR-sensitive cases |

## 4. Escalation Process

1. **Document**: Record all evidence gathered, actions taken, and reason for escalation.
2. **Route**: Transfer to the appropriate escalation level based on the trigger.
3. **Notify**: Send immediate notification to the escalation target via the priority channel.
4. **Hold**: Pause all automated actions until the escalation authority provides a decision.
5. **Resume**: Upon approval, resume the action plan with the authorized scope.

## 5. Autonomous Agent Boundaries

The automated agent system **must not**:
- Execute financial transactions above $5,000 without human approval.
- Override safety-related SOPs.
- Modify warranty terms or coverage.
- Make commitments that deviate from published policies.
- Take action when evidence confidence is below 0.70.

## 6. Timeout Policy

- If an escalation is not acknowledged within 30 minutes, re-notify and add the next level up.
- If no response within 2 hours for CRITICAL issues, the system must page the on-call VP.
