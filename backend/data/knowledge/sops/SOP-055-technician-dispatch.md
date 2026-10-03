# SOP-055: Technician Dispatch and Scheduling Protocol

**Document ID:** SOP-055
**Version:** 1
**Category:** Standard Operating Procedure
**Effective Date:** 2024-03-01
**Last Reviewed:** 2025-05-20
**Owner:** Field Operations
**Applies To:** Dispatch coordinators and automated dispatch systems

---

## 1. Purpose

Define the rules and procedures for dispatching field service technicians to customer sites, including technician selection criteria, scheduling constraints, and SLA compliance requirements.

## 2. Dispatch Triggers

A technician dispatch is initiated when:
- A service ticket with severity CRITICAL or HIGH is created.
- A MEDIUM severity ticket has been open for more than 24 hours without remote resolution.
- A customer explicitly requests on-site service (subject to contract terms).
- SOP-042 or SOP-018 mandates auto-dispatch based on error code.

## 3. Technician Selection Criteria

Select the technician based on the following priority order:

1. **Certification Match**: Technician must hold certification for the specific equipment model (e.g., PX-100 Certified, PY-200 Certified).
2. **Proximity**: Nearest available technician to the customer site (based on GPS / assigned region).
3. **Availability**: Technician must have an open slot in the scheduling system.
4. **Workload Balance**: Prefer technicians with fewer active tickets to prevent burnout.

## 4. SLA Windows

| Severity | Max Response Time | Max Resolution Time |
|----------|-------------------|---------------------|
| CRITICAL | 1 hour | 4 hours |
| HIGH | 4 hours | 8 hours |
| MEDIUM | 8 hours | 24 hours |
| LOW | 24 hours | 72 hours |

## 5. Scheduling Rules

- No technician may be assigned more than 3 CRITICAL tickets simultaneously.
- Travel time must be factored into ETA calculations.
- If no certified technician is available within the SLA window, escalate to the Regional Operations Manager.
- Weekend and holiday dispatch requires Operations Manager approval for non-CRITICAL tickets.

## 6. Dispatch Notification

Upon dispatch:
1. Send the technician a mobile notification with: ticket ID, customer address, equipment model, error code, and SLA deadline.
2. Send the customer an SMS/email with: technician name, ETA, and contact number.
3. Update the ticket status to "DISPATCHED".

## 7. Post-Dispatch Follow-Up

- Technician must check in upon arrival (update status to "ON_SITE").
- If the technician cannot resolve within the SLA, escalate and reassign.
