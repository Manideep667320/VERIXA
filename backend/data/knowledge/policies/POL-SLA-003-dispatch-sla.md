# POL-SLA-003: Service Level Agreement and Dispatch Policy

**Document ID:** POL-SLA-003
**Version:** 1
**Category:** Corporate Policy
**Effective Date:** 2024-01-15
**Last Reviewed:** 2025-06-10
**Owner:** Customer Operations
**Approved By:** VP of Customer Success

---

## 1. Purpose

Define the service level commitments for customer support, technician dispatch, and issue resolution across all IndustraCool product lines and service tiers.

## 2. Service Tiers

| Tier | Name | Response SLA | Resolution SLA | Coverage |
|------|------|-------------|----------------|----------|
| 1 | Standard | 4 hours | 24 hours | Business hours (8AM–6PM, Mon–Fri) |
| 2 | Premium | 2 hours | 8 hours | Extended hours (7AM–10PM, Mon–Sat) |
| 3 | Enterprise | 1 hour | 4 hours | 24/7/365 |

## 3. SLA by Severity

| Severity | First Response | Technician Dispatch | Resolution Target |
|----------|---------------|--------------------|--------------------|
| CRITICAL | 15 minutes | Within 1 hour | 4 hours |
| HIGH | 30 minutes | Within 4 hours | 8 hours |
| MEDIUM | 2 hours | Within 8 hours | 24 hours |
| LOW | 4 hours | Next business day | 72 hours |

## 4. Dispatch Rules

- Dispatch is **automatic** for CRITICAL and HIGH severity tickets.
- MEDIUM severity tickets require dispatch only if remote resolution fails within 8 hours.
- LOW severity tickets are batched for weekly scheduled visits.
- **After-hours dispatch** (nights, weekends, holidays) for non-CRITICAL tickets requires Operations Manager approval.
- If no technician is available within the SLA window, escalate per SOP-071.

## 5. SLA Breach Consequences

- **First breach**: Internal review, no customer impact.
- **Second breach (same customer, 90 days)**: 10% service credit to customer.
- **Third breach (same customer, 90 days)**: Escalation to VP, formal remediation plan.
- **Chronic breaches (5+ in 12 months)**: Contract renegotiation, potential penalty clauses activated.

## 6. Measurement and Reporting

- SLA compliance is measured from ticket creation timestamp to first meaningful response / on-site arrival / resolution confirmation.
- Monthly SLA reports are published to the Customer Operations dashboard.
- Target: 95% SLA compliance across all severity levels.
