# INC-2024-0031: PX-100 Thermal Runaway — Acme Manufacturing

**Incident ID:** INC-2024-0031
**Date:** 2024-03-15
**Version:** 1
**Effective Date:** 2024-03-15
**Product:** PX-100 Industrial Chiller (S/N: PX1-20230845)
**Customer:** Acme Manufacturing Corp (CUST-001)
**Severity:** CRITICAL
**Error Code:** E-401
**Status:** RESOLVED

---

## Summary

Customer reported PX-100 unit displaying E-401 error with internal temperature reading of 102°C. Unit was under warranty (installed 2023-08-15). Emergency shutdown was performed by customer prior to contacting support.

## Root Cause

Coolant pump (PUMP-CL-200) bearing seized due to manufacturing defect, resulting in complete loss of coolant flow. Without cooling, the compressor reached thermal runaway within 22 minutes.

## Actions Taken

1. Service ticket TKT-20240315-001 created with CRITICAL severity.
2. Technician Mike Rodriguez (TECH-003) dispatched — arrived on-site in 47 minutes.
3. Coolant pump replaced (warranty, no cost to customer).
4. Temperature sensor array recalibrated per SOP-089.
5. Unit brought back online, monitored for 2 hours — stable at 18°C set point.

## Resolution

Pump replaced under warranty. No recurrence in 90-day follow-up. Engineering flagged batch PX1-2023-08xx for proactive pump inspection.

## Cost

- Parts: $850 (PUMP-CL-200) — warranty covered.
- Labor: 3.5 hours — warranty covered.
- Total customer charge: $0.00.

---

# INC-2024-0047: PX-100 False E-401 Alarm — TechnoFab Industries

**Incident ID:** INC-2024-0047
**Date:** 2024-04-22
**Version:** 1
**Effective Date:** 2024-04-22
**Product:** PX-100 Industrial Chiller (S/N: PX1-20220312)
**Customer:** TechnoFab Industries (CUST-003)
**Severity:** CRITICAL (downgraded to LOW after investigation)
**Error Code:** E-401
**Status:** RESOLVED

---

## Summary

Customer reported E-401 thermal runaway alert. On-site inspection found the unit operating normally at 20°C. Investigation revealed the temperature sensor was 8 months overdue for calibration.

## Root Cause

Temperature sensor drift caused false reading of 97°C when actual temperature was 20°C. Sensor was 8 months past calibration due date per SOP-089 schedule.

## Actions Taken

1. Emergency ticket created, technician Sarah Kim (TECH-001) dispatched.
2. On-site inspection: no actual overheating detected.
3. Sensor calibration performed — deviation of +77°C confirmed.
4. Sensor array replaced (SENSOR-TEMP-4X).
5. Calibration schedule updated in Asset Management System.

## Resolution

False alarm caused by calibration drift. Sensor replaced and recalibrated. Customer advised to adhere to 6-month calibration schedule.

## Cost

- Parts: $320 (SENSOR-TEMP-4X) — warranty expired, customer charged.
- Labor: 2 hours — $400 (out of warranty).
- Total customer charge: $720.00.

---

# INC-2024-0063: PY-200 Compressor Failure — Downtown Office Tower

**Incident ID:** INC-2024-0063
**Date:** 2024-05-10
**Version:** 1
**Effective Date:** 2024-05-10
**Product:** PY-200 Commercial HVAC (S/N: PY2-20230156)
**Customer:** Metro Commercial Properties (CUST-005)
**Severity:** HIGH
**Error Code:** H-101
**Status:** RESOLVED

---

## Summary

PY-200 unit in 14-story office tower lobby reporting H-101 compressor overload error. Building occupants complaining of temperature reaching 31°C during summer peak.

## Root Cause

Condenser coil clogged with construction dust from ongoing renovation work on adjacent floor. Restricted airflow caused compressor to overheat and trigger protective shutdown.

## Actions Taken

1. Service ticket created with HIGH severity.
2. Technician James Park (TECH-004) dispatched within 3 hours.
3. Condenser coil cleaned on-site.
4. Temporary supplemental cooling arranged for affected floors.
5. Customer advised to install temporary dust barriers during construction.

## Resolution

Condenser cleaning resolved the issue. Customer installed construction barriers. No compressor damage detected.

## Cost

- Parts: None required.
- Labor: 2 hours — warranty covered (installed 2023-01-20).
- Total customer charge: $0.00.

---

# INC-2024-0078: PX-100 Equipment Replacement Request — Precision Dynamics

**Incident ID:** INC-2024-0078
**Date:** 2024-06-03
**Version:** 1
**Effective Date:** 2024-06-03
**Product:** PX-100 Industrial Chiller (S/N: PX1-20210622)
**Customer:** Precision Dynamics LLC (CUST-004)
**Severity:** HIGH
**Error Code:** E-401 (recurring)
**Status:** RESOLVED — EQUIPMENT REPLACED

---

## Summary

PX-100 unit experienced third E-401 thermal runaway event in 45 days. Customer requested full equipment replacement. Unit was out of warranty (installed 2021-06-22, warranty expired 2023-06-22).

## Root Cause

Compressor assembly degradation causing intermittent thermal runaway. Root cause: bearing wear in compressor exceeded acceptable tolerance after 3 years of heavy-duty use (24/7 operation in foundry environment).

## Actions Taken

1. Per SOP-071, recurring E-401 (3+ in 60 days) escalated to Regional Director.
2. Cost estimate prepared: full PX-100-S replacement = **$12,500** (unit) + **$2,200** (installation) = **$14,700 total**.
3. **Approval requested from Regional Director** per POL-EQP-002 ($14,700 > $5,000 threshold).
4. Approval granted by Director Patricia Wells on 2024-06-05.
5. New PX-100-S unit ordered and installed on 2024-06-12.
6. Old unit returned for failure analysis.

## Resolution

Full equipment replacement authorized and executed. New unit operational. Customer purchased Gold extended warranty.

## Cost

- Equipment: $12,500 (PX-100-S unit).
- Installation: $2,200.
- Total customer charge: $14,700.00 (out of warranty).
- **Approval required: YES (exceeded $5,000 threshold).**

---

# INC-2024-0091: PX-100 Coolant Leak — NorthStar Fabrication

**Incident ID:** INC-2024-0091
**Date:** 2024-06-28
**Version:** 1
**Effective Date:** 2024-06-28
**Product:** PX-100 Industrial Chiller (S/N: PX1-20240115)
**Customer:** NorthStar Fabrication (CUST-006)
**Severity:** HIGH
**Error Code:** E-402
**Status:** RESOLVED

---

## Summary

PX-100 displaying E-402 (coolant flow below minimum). Customer noticed coolant pooling under the unit. Unit under warranty (installed 2024-01-15).

## Root Cause

Coolant line fitting at the evaporator inlet had a manufacturing defect — hairline crack developed under thermal cycling stress.

## Actions Taken

1. Customer instructed to power down the unit per SOP-042 Section 4.2.
2. Technician Mike Rodriguez (TECH-003) dispatched within 2 hours.
3. Coolant line fitting replaced.
4. Coolant reservoir refilled and system purged of air.
5. Leak test performed — no further leaks detected.

## Resolution

Fitting replaced under warranty. Engineering notified of potential batch defect in fittings from supplier lot FIT-2024-01.

## Cost

- Parts: $180 (fitting) — warranty covered.
- Coolant: $95 (10L propylene glycol) — warranty covered.
- Labor: 2.5 hours — warranty covered.
- Total customer charge: $0.00.

---

# INC-2024-0105: Unknown Product Inquiry — GlobalTech Solutions

**Incident ID:** INC-2024-0105
**Date:** 2024-07-15
**Version:** 1
**Effective Date:** 2024-07-15
**Product:** Unknown — customer referred to "Product Y cooling system"
**Customer:** GlobalTech Solutions (CUST-007)
**Severity:** MEDIUM
**Error Code:** None provided
**Status:** ESCALATED TO HUMAN SUPPORT

---

## Summary

Customer contacted support requesting service for a "Product Y cooling system" experiencing intermittent shutdowns. No matching product found in IndustraCool's product catalog. Customer could not provide a model number or serial number.

## Investigation

1. Searched product database for "Product Y" — no matches found.
2. Searched knowledge base for related SOPs — no applicable SOPs identified.
3. Asked customer for additional details — customer stated it was purchased from a reseller.
4. Cross-referenced reseller database — no record of sale to this customer.

## Resolution

**Unable to identify product or locate applicable service procedures.** Case escalated to human support team for manual investigation. Possible scenarios:
- Third-party equipment not manufactured by IndustraCool.
- Rebranded/white-label product with different naming.
- Customer confusion with another vendor's product.

**Autonomous action was NOT taken** because no matching SOP, manual, or warranty record could be found, and evidence confidence was below the 0.70 threshold.

## Cost

- No service performed.
- Total customer charge: $0.00.

---

# INC-2024-0112: PY-200 Zone Control Failure — Sunrise Medical Center

**Incident ID:** INC-2024-0112
**Date:** 2024-07-29
**Version:** 1
**Effective Date:** 2024-07-29
**Product:** PY-200 Commercial HVAC (S/N: PY2-20230890)
**Customer:** Sunrise Medical Center (CUST-008)
**Severity:** HIGH
**Error Code:** H-104
**Status:** RESOLVED

---

## Summary

PY-200 zone control failure affecting 3 of 8 configured zones in the medical center. Patient rooms in affected zones reaching 28°C (above comfort threshold). Under warranty.

## Root Cause

Zone valve actuators (3 units) failed simultaneously due to a firmware bug in zone controller firmware v2.1.3 that caused actuators to receive conflicting open/close commands.

## Actions Taken

1. Service ticket created with HIGH severity (medical facility = priority environment).
2. Technician Carlos Mendez (TECH-005) dispatched immediately.
3. Firmware updated to v2.1.4 (patch released 2024-07-25).
4. All 8 zone valve actuators tested — 3 required physical replacement due to motor burnout.
5. Portable cooling units deployed for affected patient rooms during repair.

## Resolution

Firmware updated and damaged actuators replaced. All zones verified operational. IndustraCool issued a service advisory for firmware v2.1.3.

## Cost

- Parts: 3× PY-200-VALVE-Z1 at $180 each = $540 — warranty covered.
- Labor: 5 hours — warranty covered.
- Total customer charge: $0.00.

---

# INC-2024-0128: PX-100 Power Supply Failure — Quantum Labs

**Incident ID:** INC-2024-0128
**Date:** 2024-08-14
**Version:** 1
**Effective Date:** 2024-08-14
**Product:** PX-100 Industrial Chiller (S/N: PX1-20230290)
**Customer:** Quantum Research Labs (CUST-002)
**Severity:** HIGH
**Error Code:** E-501
**Status:** RESOLVED

---

## Summary

PX-100 displaying E-501 (phase loss detected). Customer reported power outage affected the facility, and the unit did not restart properly after power was restored.

## Root Cause

Power surge during restoration damaged the main control board (CB-MAIN-V3). Phase detection circuit on the board was permanently tripped.

## Actions Taken

1. Remote diagnostics confirmed E-501 — unit unable to start.
2. Technician Sarah Kim (TECH-001) dispatched with replacement control board.
3. Control board replaced on-site.
4. Customer advised to install surge protection (recommended in MAN-PX100, Section 2).
5. Warranty claim evaluated — **denied** because surge damage is excluded per POL-WTY-001 Section 3.2.

## Resolution

Control board replaced. Customer charged for parts and labor. Surge protector installed to prevent recurrence.

## Cost

- Parts: $1,200 (CB-MAIN-V3).
- Labor: 3 hours — $600.
- Total customer charge: $1,800.00 (warranty exclusion: power surge).

---

# INC-2024-0139: PX-100 Overheating — Warranty Repair — BioProcess Corp

**Incident ID:** INC-2024-0139
**Date:** 2024-09-02
**Version:** 1
**Effective Date:** 2024-09-02
**Product:** PX-100 Industrial Chiller (S/N: PX1-20240330)
**Customer:** BioProcess Corp (CUST-009)
**Severity:** CRITICAL
**Error Code:** E-401
**Status:** RESOLVED

---

## Summary

PX-100 E-401 thermal runaway during pharmaceutical manufacturing process. Temperature reached 98°C. Customer performed emergency shutdown. Product batch at risk — customer requested immediate resolution. Unit under warranty.

## Root Cause

Compressor assembly (PX-100-COMP-A1) internal valve failure causing loss of refrigerant circulation. Compressor manufactured in the same batch as INC-2024-0031 (batch PX1-2024-03xx).

## Actions Taken

1. CRITICAL ticket created, technician James Park (TECH-004) dispatched — on-site in 38 minutes.
2. Compressor replaced (pre-staged part per SOP-018 Section 4).
3. System recharged with R-410A refrigerant.
4. Unit tested and verified stable at set point for 4 hours.
5. Customer's QA team verified pharmaceutical batch was not compromised.

## Resolution

Compressor replaced under warranty. Engineering initiated proactive recall of batch PX1-2024-03xx compressors.

## Cost

- Parts: $2,800 (PX-100-COMP-A1) — warranty covered.
- Refrigerant: $150 — warranty covered.
- Labor: 4 hours — warranty covered.
- Total customer charge: $0.00.

---

# INC-2024-0152: PY-200 Refrigerant Leak — Evergreen Mall

**Incident ID:** INC-2024-0152
**Date:** 2024-09-18
**Version:** 1
**Effective Date:** 2024-09-18
**Product:** PY-200 Commercial HVAC (S/N: PY2-20240201)
**Customer:** Evergreen Commercial Group (CUST-010)
**Severity:** HIGH
**Error Code:** H-102
**Status:** RESOLVED

---

## Summary

PY-200 displaying H-102 (refrigerant pressure low). Mall management reported declining cooling performance over 2 weeks before error appeared. Under warranty.

## Root Cause

Refrigerant line brazed joint failure at the outdoor unit connection. Slow leak reduced refrigerant charge below operational threshold over approximately 14 days.

## Actions Taken

1. Service ticket created with HIGH severity.
2. Technician Carlos Mendez (TECH-005) dispatched next day.
3. Leak detected using electronic leak detector at outdoor unit brazed joint.
4. Joint re-brazed and pressure tested.
5. System evacuated and recharged with R-32 refrigerant.
6. 24-hour monitoring confirmed stable operation.

## Resolution

Brazed joint repaired, system recharged. No further leaks detected in 30-day follow-up.

## Cost

- Parts: Brazing materials $50 — warranty covered.
- Refrigerant: $280 (R-32, 3kg) — warranty covered.
- Labor: 4 hours — warranty covered.
- Total customer charge: $0.00.
