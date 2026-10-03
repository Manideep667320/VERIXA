# SOP-089: Sensor Calibration and Validation Procedures

**Document ID:** SOP-089
**Version:** 1
**Category:** Standard Operating Procedure
**Effective Date:** 2024-08-01
**Last Reviewed:** 2025-04-10
**Owner:** Quality Assurance Engineering
**Applies To:** Field technicians, calibration specialists

---

## 1. Purpose

Define the calibration procedures for temperature, pressure, and flow sensors installed in IndustraCool equipment. Proper calibration ensures accurate error code generation and prevents false alarms (e.g., false E-401 thermal runaway alerts on PX-100 units).

## 2. Calibration Schedule

| Sensor Type | Model Series | Calibration Interval | Tolerance |
|-------------|-------------|----------------------|-----------|
| Temperature | PX-100, PX-150 | Every 6 months | ±0.5°C |
| Pressure | PX-100 | Every 12 months | ±2 PSI |
| Flow Rate | PX-100, PY-200 | Every 6 months | ±5% |
| Vibration | PY-200 | Every 12 months | ±0.1g |

## 3. Calibration Procedure

### 3.1 Temperature Sensor Calibration (PX-100)

1. Power down the unit and allow it to reach ambient temperature (minimum 2 hours).
2. Connect the NIST-traceable reference thermometer to the calibration port.
3. Record readings at three reference points: 20°C, 50°C, 80°C.
4. If deviation exceeds ±0.5°C at any point, replace the sensor (part: SENSOR-TEMP-4X).
5. Update the calibration log in the Asset Management System with the new calibration date and next-due date.

### 3.2 Flow Rate Sensor Calibration (PX-100 / PY-200)

1. Connect the calibration flow meter to the coolant loop test port.
2. Run the pump at 25%, 50%, 75%, and 100% capacity.
3. Compare readings at each level; deviation > ±5% requires sensor replacement.
4. After replacement, re-run the calibration cycle to confirm.

## 4. False Alarm Investigation

If a customer reports an E-401 and on-site inspection finds no actual overheating:
- Check the calibration date of the temperature sensor array.
- If overdue for calibration, perform field calibration before any other action.
- Document as "False Alarm — Calibration Drift" and update the incident record.

## 5. Documentation

- All calibration results must be recorded in the Calibration Management Database.
- Certificates of calibration must be filed with the customer's asset record.
- Non-conforming sensors must be tagged and returned to the lab for failure analysis.
