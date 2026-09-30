# SOP-018: Equipment Failure Diagnostic and Triage

**Document ID:** SOP-018
**Version:** 1
**Category:** Standard Operating Procedure
**Effective Date:** 2023-09-01
**Last Reviewed:** 2025-03-15
**Owner:** Technical Support Division
**Applies To:** Level-2 support agents and field engineers

---

## 1. Purpose

Establish a standardized diagnostic and triage process for equipment failure reports across all IndustraCool product lines, ensuring accurate categorization, appropriate severity assignment, and efficient resolution routing.

## 2. Failure Categories

| Category | Description | Default Severity | Response SLA |
|----------|-------------|------------------|--------------|
| Mechanical | Moving parts failure (compressor, fan, pump) | HIGH | 4 hours |
| Electrical | Power supply, control board, sensor faults | HIGH | 4 hours |
| Thermal | Overheating, undercooling, thermal cycling | CRITICAL | 1 hour |
| Software | Firmware bugs, configuration errors | MEDIUM | 8 hours |
| Connectivity | Network, IoT sensor communication loss | LOW | 24 hours |

## 3. Diagnostic Workflow

### Step 1: Initial Assessment
- Collect the equipment model, serial number, and error code from the customer.
- Verify warranty status in the Asset Management System.
- Check the incident history for recurring patterns.

### Step 2: Remote Diagnostics
- If IoT telemetry is available, pull the last 24 hours of sensor data.
- Identify anomalous readings (temperature, vibration, power draw).
- Cross-reference with known failure signatures in the Knowledge Base.

### Step 3: Severity Assignment
- Use the error code severity table (see SOP-042 for thermal codes, SOP-055 for mechanical codes).
- Override to CRITICAL if: customer reports safety hazard, or equipment is in a production-critical environment.

### Step 4: Routing
- **CRITICAL/HIGH**: Create ticket + auto-dispatch technician.
- **MEDIUM**: Create ticket, schedule next-day service window.
- **LOW**: Create ticket, add to weekly batch queue.

## 4. Parts Pre-Staging

For CRITICAL and HIGH failures on PX-100 and PY-200 units, pre-stage the following common replacement parts:
- Compressor assembly (PX-100-COMP-A1)
- Thermal sensor array (SENSOR-TEMP-4X)
- Control board (CB-MAIN-V3)
- Coolant pump (PUMP-CL-200)

## 5. Customer Communication

- Send automated acknowledgment within 10 minutes of ticket creation.
- Provide status updates at 1-hour intervals for CRITICAL tickets.
- Obtain customer sign-off before closing the ticket.
