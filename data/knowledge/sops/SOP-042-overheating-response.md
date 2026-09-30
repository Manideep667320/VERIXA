# SOP-042: Overheating Equipment Response Procedure

**Document ID:** SOP-042
**Version:** 1
**Category:** Standard Operating Procedure
**Effective Date:** 2024-01-15
**Last Reviewed:** 2025-06-01
**Owner:** Operations Safety Division
**Applies To:** All field service engineers and support agents

---

## 1. Purpose

This procedure defines the mandatory response steps when a customer reports equipment overheating, including diagnostic error codes E-401 (thermal runaway), E-402 (coolant flow failure), and E-403 (ambient temperature exceedance). It covers the PX-100 Industrial Chiller and related cooling infrastructure.

## 2. Scope

Applies to all overheating incidents involving IndustraCool product lines, specifically:
- **PX-100 Industrial Chiller** — error codes E-400 through E-410
- **PX-150 Precision Cooler** — error codes E-500 through E-510

## 3. Error Code Reference

| Error Code | Description | Severity | Auto-Dispatch |
|------------|-------------|----------|---------------|
| E-401 | Thermal runaway — internal temperature exceeds 95°C | CRITICAL | Yes |
| E-402 | Coolant flow rate below minimum threshold | HIGH | Yes |
| E-403 | Ambient temperature exceeds rated operating range | MEDIUM | No |
| E-404 | Compressor cycling anomaly detected | MEDIUM | No |

## 4. Immediate Response Steps

### 4.1 Error E-401 — Thermal Runaway (CRITICAL)

1. **Acknowledge** the alert within 5 minutes of receipt.
2. **Instruct the customer** to power down the PX-100 unit immediately using the emergency stop (red button, rear panel).
3. **Create a service ticket** with severity CRITICAL and category "Overheating — E-401".
4. **Auto-dispatch** the nearest available field technician within the customer's service region.
5. **Notify the customer** with the technician's name, ETA, and ticket reference number.
6. **Escalate to Engineering** if the unit has triggered E-401 more than twice in the past 30 days.

### 4.2 Error E-402 — Coolant Flow Failure (HIGH)

1. Verify coolant reservoir level with the customer remotely.
2. If reservoir is adequate, create a service ticket with severity HIGH.
3. Dispatch a technician within 4 business hours.

### 4.3 Error E-403 — Ambient Temperature (MEDIUM)

1. Advise the customer to check facility HVAC and ambient conditions.
2. Log the incident; no dispatch required unless recurrent (3+ times in 7 days).

## 5. Warranty Considerations

- **Fact:** warranty.px100_months = 18 months
- This v1 quick-reference value is retained for audit history; confirm current coverage against the effective corporate warranty policy before advising a customer.
- All overheating repairs on units under active warranty are **covered at no cost** to the customer.
- If the unit is out of warranty, provide a cost estimate **before** dispatching.
- Refer to **POL-WTY-001** for warranty term details and coverage limits.

## 6. Escalation Matrix

| Condition | Escalation Target |
|-----------|-------------------|
| E-401 recurring (2+ in 30 days) | Engineering Lead |
| Customer reports physical damage or smoke | Safety Officer + Regional Manager |
| No technician available within SLA window | Operations Manager |

## 7. Documentation Requirements

After resolution, the technician must complete:
- Field service report with root cause analysis
- Parts replaced (if any) with serial numbers
- Updated asset condition in the service management system
