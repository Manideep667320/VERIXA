# MAN-PX100: PX-100 Industrial Chiller — Technical Manual

**Document ID:** MAN-PX100
**Product:** PX-100 Industrial Chiller
**Version:** 3.2
**Effective Date:** 2024-02-01
**Published:** 2024-02-01
**Manufacturer:** IndustraCool Systems Inc.

---

## 1. Product Overview

The PX-100 Industrial Chiller is a high-capacity cooling unit designed for manufacturing facilities, data centers, and industrial process cooling. It provides precise temperature control from 5°C to 25°C with a cooling capacity of 50kW.

### 1.1 Key Specifications

| Parameter | Value |
|-----------|-------|
| Model | PX-100 |
| Cooling Capacity | 50 kW |
| Operating Range | 5°C – 25°C |
| Power Supply | 380–480V, 3-phase, 50/60 Hz |
| Refrigerant | R-410A |
| Coolant | Propylene glycol solution (30%) |
| Weight | 850 kg |
| Dimensions | 1800 × 900 × 1200 mm |
| Noise Level | ≤72 dB(A) |
| Warranty | 24 months from installation date |

### 1.2 Model Variants

- **PX-100-S**: Standard configuration
- **PX-100-H**: High-ambient variant (rated to 50°C ambient)
- **PX-100-R**: Redundant compressor configuration

## 2. Installation Requirements

### 2.1 Site Preparation
- Minimum clearance: 600mm on all sides for airflow.
- Foundation must support static load of 1,200 kg (unit + coolant).
- Dedicated 3-phase power circuit with properly rated breaker.

### 2.2 Coolant System
- Fill the coolant reservoir with propylene glycol solution (30% concentration).
- Minimum coolant volume: 200 liters.
- Coolant loop must be flushed before initial fill.

## 3. Error Codes

### 3.1 Thermal Errors (E-4xx Series)

| Code | Description | Cause | Action |
|------|-------------|-------|--------|
| **E-401** | **Thermal runaway — internal temperature exceeds 95°C** | Compressor failure, coolant loss, blocked condenser | **Emergency shutdown required. See SOP-042.** |
| E-402 | Coolant flow below minimum | Pump failure, air lock, low coolant level | Check pump and coolant level |
| E-403 | Ambient temperature exceeds rating | Installation environment too hot | Verify site HVAC |
| E-404 | Compressor cycling > 12 times/hour | Refrigerant charge low or control valve fault | Schedule service |
| E-405 | Evaporator freeze-up | Low coolant flow or set point too low | Defrost cycle, check settings |

### 3.2 Electrical Errors (E-5xx Series)

| Code | Description | Cause | Action |
|------|-------------|-------|--------|
| E-501 | Phase loss detected | Power supply issue | Check electrical supply |
| E-502 | Control board communication fault | Internal bus error | Power cycle, if persistent replace CB-MAIN-V3 |
| E-503 | Sensor array fault | Damaged or miscalibrated sensor | Replace SENSOR-TEMP-4X per SOP-089 |

## 4. Maintenance Schedule

| Task | Interval | Technician Level |
|------|----------|------------------|
| Visual inspection | Monthly | Level 1 |
| Coolant quality test | Quarterly | Level 1 |
| Filter replacement | Quarterly | Level 1 |
| Sensor calibration | 6 months | Level 2 (see SOP-089) |
| Compressor inspection | Annually | Level 3 |
| Full system overhaul | 3 years | Level 3 |

## 5. Troubleshooting Guide

### 5.1 Unit Not Cooling

1. Verify power supply — check for E-501.
2. Check coolant level and flow — look for E-402.
3. Inspect condenser coils for blockage.
4. Verify thermostat set point.

### 5.2 Error E-401 Thermal Runaway

**This is a CRITICAL error. Follow SOP-042 immediately.**

1. Press the emergency stop button (red, rear panel).
2. Do NOT attempt to restart the unit.
3. Contact support immediately — a service ticket will be auto-created.
4. A certified PX-100 technician will be dispatched within the SLA window.

### 5.3 Excessive Noise or Vibration

1. Check mounting bolts and vibration dampeners.
2. Inspect compressor bearings (may indicate E-404 pending).
3. If vibration exceeds 0.5g, shut down and request service.

## 6. Warranty Terms

The PX-100 is covered under IndustraCool's standard 24-month warranty from date of installation. Warranty covers:
- All manufacturing defects in materials and workmanship.
- Compressor failure under normal operating conditions.
- Control board and sensor failures.

**Warranty exclusions:**
- Damage from improper installation or operation outside rated conditions.
- Cosmetic damage.
- Consumable items (filters, coolant).

See **POL-WTY-001** for full warranty policy terms.

## 7. Parts Reference

| Part Number | Description | Lead Time |
|-------------|-------------|-----------|
| PX-100-COMP-A1 | Compressor assembly | 5 business days |
| SENSOR-TEMP-4X | Temperature sensor array | 2 business days |
| CB-MAIN-V3 | Main control board | 3 business days |
| PUMP-CL-200 | Coolant pump | 2 business days |
| FILTER-AIR-PX | Air filter (pack of 4) | In stock |
