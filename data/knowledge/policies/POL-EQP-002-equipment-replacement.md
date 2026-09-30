# POL-EQP-002: Equipment Replacement Authorization Policy

**Document ID:** POL-EQP-002
**Version:** 1
**Category:** Corporate Policy
**Effective Date:** 2024-03-01
**Last Reviewed:** 2025-05-20
**Owner:** Finance & Operations
**Approved By:** CFO

---

## 1. Purpose

Define the authorization thresholds and approval workflow for equipment replacement decisions, ensuring proper financial controls and accountability.

## 2. Authorization Thresholds

| Replacement Cost | Authorization Required | Approver |
|-----------------|----------------------|----------|
| ≤ $1,000 | Automated (no human approval) | System |
| $1,001 – $5,000 | Support Manager approval | Level L1 Manager |
| $5,001 – $25,000 | **Regional Director approval required** | Level L3 Director |
| $25,001 – $100,000 | VP Operations approval | Level L4 VP |
| > $100,000 | Executive Committee approval | C-Suite |

## 3. Critical Rule: $5,000 Approval Threshold

**Any equipment replacement, repair, or service action with a total cost exceeding $5,000 MUST receive explicit human approval before execution.** This is a non-negotiable financial control.

The automated agent system:
- **MUST** pause and request human approval for any action exceeding $5,000.
- **MUST NOT** split costs across multiple tickets to circumvent this threshold.
- **MUST** present the full cost breakdown, justification, and alternative options to the approver.

## 4. Approval Workflow

1. **Cost Estimation**: The agent calculates the total replacement cost including parts, labor, and shipping.
2. **Threshold Check**: Compare against the authorization table above.
3. **If below threshold**: Execute automatically, log the decision in the audit trail.
4. **If above threshold**:
   a. Generate an Approval Request with: cost breakdown, justification, evidence references, and alternative options.
   b. Route to the appropriate approver.
   c. **Halt all related actions** until approval is received.
   d. Upon approval: execute and log. Upon rejection: notify customer of alternative options.

## 5. Emergency Override

In genuine safety emergencies (risk of injury or property damage), a Level L2 Operations Manager may authorize up to $25,000 without Director approval, provided:
- The emergency is documented with photographic evidence.
- A retroactive approval request is submitted within 24 hours.
- The Safety Officer is notified immediately.

## 6. Cost Estimation Rules

- Use the current parts catalog pricing (updated quarterly).
- Include estimated labor hours at the technician's rate.
- Add 15% contingency for unexpected complications.
- Include shipping costs for non-stock parts.
- Document all assumptions in the cost estimate.

## 7. Audit Requirements

Every equipment replacement decision must be recorded with:
- Original customer request
- Evidence and diagnosis
- Cost estimate with breakdown
- Approval status and approver identity
- Execution confirmation
