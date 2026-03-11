# SOPHIA Protocol Engineering Guide
## Definitive Reference for Protocol Encoding, Validation, and Debugging

**Version:** 1.0
**Date:** 2026-03-11
**Based on:** RCHOP21 (LYMPHOMA-RCHOP21) as the canonical reference implementation
**Audience:** Developer + Clinical Pharmacist working on the 565-protocol roadmap

---

## Table of Contents

1. [The Philosophy](#1-the-philosophy)
2. [Step-by-Step: How to Encode a New Protocol](#2-step-by-step-how-to-encode-a-new-protocol)
3. [The Engine Safety Checks (All 13)](#3-the-engine-safety-checks-all-13)
4. [Dose Calculation Logic](#4-dose-calculation-logic)
5. [The Compound Condition Parser](#5-the-compound-condition-parser)
6. [How to Write Clinical Tests](#6-how-to-write-clinical-tests)
7. [Common Bugs and How We Found / Fixed Them](#7-common-bugs-and-how-we-found--fixed-them)
8. [Protocol-Specific Checklist](#8-protocol-specific-checklist)
9. [JSON Schema Reference](#9-json-schema-reference)
10. [The 565 Protocol Roadmap](#10-the-565-protocol-roadmap)

---

## 1. The Philosophy

### 1.1 Precision Means Life-Critical

SOPHIA generates chemotherapy prescriptions. A wrong dose is not a software bug in the ordinary sense — it is a potential patient death. Every field in the JSON, every line in the engine, every test assertion exists because a real drug at a real dose must be calculated correctly for a real patient.

The header comment in `engine.py` states this directly:

```
SAFETY CRITICAL: This module contains life-critical dose calculation logic.
All changes must be reviewed by a clinical pharmacist and oncologist.
```

This is not boilerplate. Consequences of known error categories:
- **Vincristine overdose**: permanent paralysis, death. Hard cap 2.0 mg exists for this reason.
- **Missing BSA cap**: a patient with BSA 2.4 m² receives 20% more of every BSA-dosed drug.
- **Missing hepatic dose modification**: a patient with bilirubin 90 µmol/L receives full-dose doxorubicin with severe hepatic failure, causing fatal cardiac toxicity.
- **Missing HBV prophylaxis warning**: rituximab causes fatal hepatitis B reactivation.

"Done" on a protocol means: a clinical pharmacist can hand the printed output to a nurse and that nurse can safely prepare and administer the treatment. Nothing less.

### 1.2 Source of Truth Hierarchy

```
NHS PDF (primary source)
    ↓  human extraction
JSON (protocol_jsons_normalized/*.json)
    ↓  json_protocol_loader.py
Protocol model (models.py)
    ↓  engine.py
ProtocolResponse (models.py)
    ↓  API (FastAPI)
Frontend (React)
```

**Every decision flows downward. If the JSON says something different from the PDF, the PDF wins and the JSON must be corrected. The engine never makes clinical decisions — it enforces what the JSON encodes.**

### 1.3 What "Done" Looks Like for a Protocol

A protocol is complete when all of the following are true:

1. Every drug from the NHS PDF is in the JSON with correct dose, unit, route, and days array.
2. Every dose modification table row is encoded as a structured `dose_modifications` entry.
3. Every special warning from the PDF (vesicant handling, HBV, cardiac, etc.) is in `special_warnings`.
4. `monitoring` contains all pre-cycle labs and follow-up requirements.
5. `take_home_medicines` and `rescue_medications` are complete.
6. Cycle-specific items (CYCLE 1 ONLY, CYCLES 1-5 ONLY) are marked in `special_instructions`.
7. `required_patient_fields` lists every field the clinician must fill for this protocol.
8. The engine produces a `ProtocolResponse` that a pharmacist cannot distinguish from a hand-typed prescription — correct doses, correct units, correct warnings, correct omissions.
9. A test suite covering every dose modification row plus boundary cases passes.

---

## 2. Step-by-Step: How to Encode a New Protocol

### Step 1: Read the NHS PDF — What to Extract

Open the NHS/UHS PDF for the protocol. Extract the following in order:

| Section in PDF | Maps to JSON field |
|---|---|
| Protocol name, code, cycle length, number of cycles | `protocol_code`, `protocol_name`, `cycle_length_days`, `number_of_cycles` |
| Drug table (drug, dose, unit, route, days) | `drugs[]` |
| Pre-medications | `pre_medications[]` |
| Take-home/discharge medications | `take_home_medicines[]` |
| Rescue / PRN medications | `rescue_medications[]` |
| Dose modification tables | `dose_modifications[]` |
| Special warnings / alerts | `special_warnings[]` |
| Monitoring requirements | `monitoring[]` |
| Required pre-cycle tests | `monitoring[]` (combined) |

**Specific extraction rules:**

- **Doses**: Always extract the per-administration dose (not per-course). A drug given on days 1, 2, 3 has the same dose each day — encode the per-day dose.
- **Units**: Distinguish mg/m², mg (flat), mg/kg. If the PDF says "750 mg/m²", encode `dose: 750, dose_unit: "mg/m²"`. Never convert BSA-dosed drugs to flat.
- **Max dose**: If the PDF says "Maximum 2 mg" for vincristine, encode `max_dose: 2.0, max_dose_unit: "mg"`.
- **Days**: Use the integer day numbers. Days 1–5 = `[1, 2, 3, 4, 5]`. Day 1 only = `[1]`.
- **Route abbreviations**: Map to the canonical route strings (see JSON Schema below).
- **Infusion duration**: Extract in hours for `infusion_duration_hours`.
- **Diluent**: Extract diluent name and volume if stated.
- **Notes**: Every clinical caveat from the PDF that does not fit a structured field goes in `notes` on the relevant drug entry.

### Step 2: Write the JSON — Exact Field Names

The JSON file is a list (`[...]`) of protocol objects. Here is the canonical RCHOP21 structure for the five drugs:

```json
{
  "protocol_code": "LYMPHOMA-RCHOP21",
  "protocol_name": "RCHOP21 - Rituximab-Cyclophosphamide-Doxorubicin-Prednisolone-Vincristine (21-day cycle)",
  "disease_site": "CD20 positive Non-Hodgkin Lymphoma",
  "category": "lymphoma",
  "cycle_length_days": 21,
  "number_of_cycles": 6,
  "drugs": [
    {
      "drug_name": "Rituximab",
      "dose": 375.0,
      "dose_unit": "mg/m²",
      "route": "IV infusion",
      "days": [1],
      "infusion_duration_hours": null,
      "max_dose": null,
      "max_dose_unit": null,
      "diluent": "Sodium chloride 0.9%",
      "diluent_volume_ml": 500,
      "notes": "Intravenous infusion in 500ml sodium chloride 0.9%. Rate of administration varies — refer to rituximab administration guidelines. Rounded to nearest 100mg (up if halfway). FIRST in administration order. Check patient has taken prednisolone 100mg oral on morning of treatment before starting rituximab."
    },
    {
      "drug_name": "Vincristine",
      "dose": 1.4,
      "dose_unit": "mg/m²",
      "route": "IV bolus",
      "days": [1],
      "infusion_duration_hours": 0.167,
      "max_dose": 2.0,
      "max_dose_unit": "mg",
      "diluent": "Sodium chloride 0.9%",
      "diluent_volume_ml": 50,
      "notes": "Intravenous bolus in 50ml sodium chloride 0.9% over 10 minutes. Maximum dose 2mg. Round to nearest 0.1mg (up if halfway). VESICANT — NPSA/2008/RRR04 must be followed. Administer AFTER doxorubicin."
    }
  ]
}
```

**Field type rules:**
- `dose`: always a float (e.g. `1.4`, not `"1.4"`)
- `dose_unit`: one of `"mg/m²"`, `"mg"`, `"g/m²"`, `"g"`, `"mg/kg"`, `"units/m²"`, `"mcg"`, `"mcg/m²"`
- `route`: one of `"IV infusion"`, `"IV bolus"`, `"Oral"`, `"Subcutaneous"`, `"Intramuscular"`, `"Nebulised"`
- `days`: list of integers, never empty
- `max_dose`: float or `null`
- `infusion_duration_hours`: float (hours) or `null`
- `diluent_volume_ml`: integer or `null`

**How to handle special dose types:**
- **Flat dose** (e.g. prednisolone 100 mg): `dose: 100.0, dose_unit: "mg"`. The engine treats non-BSA units as flat — no BSA multiplication.
- **mg/m²**: Engine multiplies by capped BSA.
- **mg/kg**: Engine multiplies by `patient.weight_kg`.
- **AUC dosing** (carboplatin): The engine does not yet support Calvert formula from JSON. Currently handled by including a `notes` string and encoding a representative flat dose for display; AUC flag can be set in `auc_dosing: true`.

### Step 3: Dose Modification Conditions — Exact Format

Each dose modification row from the PDF becomes one object in `dose_modifications[]`. The most critical decision is how to write the `condition` string, because `_parse_dm_condition` in `json_protocol_loader.py` parses it automatically.

**Canonical format:**

```json
{
  "condition": "Hepatic impairment — Doxorubicin: Bilirubin <30 µmol/L AND AST/ALT 2–3×ULN",
  "drug_name": "Doxorubicin",
  "factor": 0.75,
  "notes": "Reduce doxorubicin to 75% (UHS RCHOP21 v1.2: bilirubin <30 AND AST/ALT 2-3×ULN)."
}
```

**The `factor` field is the RETAINED fraction, not the reduction:**
- `factor: 1.0` = give full dose (use for delay instructions, text-only rules)
- `factor: 0.75` = give 75% of calculated dose (25% reduction)
- `factor: 0.5` = give 50% of calculated dose (50% reduction)
- `factor: 0.25` = give 25% of calculated dose (75% reduction)
- `factor: 0.0` = omit the drug entirely

**Condition string requirements for the parser:**

The parser (`_parse_dm_condition`) recognises conditions by the presence of parameter keywords and numeric thresholds. The condition string must:

1. Contain the parameter name somewhere (case-insensitive): `bilirubin`, `crcl`, `creatinine clearance`, `gfr`, `neutrophil`, `platelet`, `ast/alt`, `ast`, `alt`
2. Contain the threshold in one of these forms:
   - `<30` or `>85` or `30-50` (range, requires two-digit numbers)
   - `2-3×ULN` or `>3×ULN` (xULN notation)
   - `normal` keyword for "within reference range"
3. For compound conditions, use ` AND `, ` OR `, or ` AND/OR ` as the connector (with spaces either side)

**All RCHOP21 dose modification condition strings:**

```
Hepatic impairment — Doxorubicin: Bilirubin <30 µmol/L AND AST/ALT 2–3×ULN    → factor 0.75
Hepatic impairment — Doxorubicin: Bilirubin 30–50 µmol/L AND/OR AST/ALT >3×ULN → factor 0.50
Hepatic impairment — Doxorubicin: Bilirubin 51–85 µmol/L                        → factor 0.25
Hepatic impairment — Doxorubicin: Bilirubin >85 µmol/L                          → factor 0.00
Hepatic impairment — Vincristine: Bilirubin 30–51 µmol/L OR AST/ALT 60–180 units/L → factor 0.50
Hepatic impairment — Vincristine: Bilirubin >51 µmol/L AND AST/ALT normal        → factor 0.50
Hepatic impairment — Vincristine: Bilirubin >51 µmol/L AND AST/ALT >180 units/L  → factor 0.00
Renal impairment — Cyclophosphamide: CrCl 10–20 ml/min                          → factor 0.75
Renal impairment — Cyclophosphamide: CrCl <10 ml/min                            → factor 0.50
```

**xULN pre-calculation:** The parser converts N×ULN notation to absolute units using ULN = 40 U/L for AST/ALT:
- `2–3×ULN` → range 80–120 U/L
- `>3×ULN` → greater_than 120 U/L
- `>180 units/L` → greater_than 180 (literal, no ULN multiplication needed)

**Critical:** The range parser pattern `(\d{2,})` requires at least two digits. Values like `5-9` would not parse as ranges. Use `>3` or `<10` notation for single-digit thresholds. For two-digit-or-more ranges (e.g. `10-20`, `30-50`, `51-85`), the range format works correctly.

### Step 4: Special Warnings and Monitoring

`special_warnings` is a list of strings. Each string is a single clinical alert shown prominently in the output. Use them for:
- Vesicant handling instructions with specific safety alert numbers
- Cardiac monitoring requirements
- Virology screening (HBV before rituximab is mandatory — the engine uses the JSON warning to supplement its own Check 7)
- Infusion reaction management protocols
- Population-specific precautions (elderly, renally impaired)

`monitoring` is a list of strings, each a monitoring requirement. Write them as actions, not headings:

```json
"monitoring": [
  "FBC, LFTs and U&Es prior to day 1 of each cycle",
  "Check hepatitis B status (HBsAg and anti-HBc) before cycle 1",
  "LVEF (echocardiogram) before starting doxorubicin in patients with cardiac history, cardiac risk factors, or age ≥70",
  "Vincristine neurotoxicity assessment each cycle (peripheral neuropathy, constipation, jaw pain)"
]
```

### Step 5: Cycle-Specific Logic

**CYCLE 1 ONLY items** are detected by `_adjust_days_for_cycle` in the engine. To mark an item as cycle-1-only, the `notes` or drug `drug_name` field must match one of these patterns:

```python
re.compile(r'^\s*cycle\s+1\s+only\s*[:\.\-\u2013\u2014]', re.IGNORECASE)
re.compile(r'^\s*loading\s+dose\s*[\-\u2013\u2014]\s*cycle\s+1', re.IGNORECASE)
re.compile(r'cycle\s+1\s+only\W*$', re.IGNORECASE)
```

RCHOP21 example — allopurinol take-home only for cycle 1:

```json
"Allopurinol 300mg oral once a day for 21 days — CYCLE 1 ONLY"
```

**CYCLES 1-5 ONLY items** — items that should appear on cycles 1 through 5 but not cycle 6 (the final cycle, where no further cycle follows):

```json
"Prednisolone 100mg oral once a day on morning of next treatment day (day 1 of next cycle) — CYCLES 1–5 ONLY. Do not issue for cycle 6 (no further cycle follows)."
```

The engine detects this pattern in `generate_protocol`:

```python
if is_final_cycle:
    instr = (drug.special_instructions or "").lower()
    if "next treatment" in instr or "next cycle" in instr or "cycles 1" in instr:
        continue
```

The phrase `"cycles 1"` (case-insensitive) is the trigger. If the instruction says "CYCLES 1-5 ONLY" and we are on cycle 6, it is suppressed.

---

## 3. The Engine Safety Checks (All 13)

These run in order inside `generate_protocol()` in `engine.py` before any dose is calculated.

### Check 1: Treatment Delay (Haematological Criteria)

**Trigger:** `patient.requires_delay` is True
**Computed from:** neutrophils < 1.0 ×10⁹/L OR platelets < 100 ×10⁹/L
**Output:** `Warning(level="critical", message="TREATMENT DELAY RECOMMENDED: ...")`
**Effect:** Warning only — doses are still calculated. The prescriber decides.

```python
# Thresholds in models.py
NEUTROPHIL_DELAY_THRESHOLD = 1.0   # x10⁹/L
PLATELET_DELAY_THRESHOLD   = 100   # x10⁹/L
```

### Check 2: BSA Capping Notification

**Trigger:** `patient.bsa_was_capped` AND protocol contains at least one BSA-dosed drug
**Computed from:** `patient.calculated_bsa > 2.0`
**Output:** `Warning(level="warning")` noting actual vs capped BSA
**Effect:** Warning only — the engine has already used capped BSA for all dose calculations.

```python
BSA_CAP_OBESE = 2.0  # m², per ASCO guidelines
```

This check is intentionally skipped for flat-dose-only protocols (blinatumomab etc.) — BSA capping is irrelevant when no drug is dosed per m².

### Check 3: Elderly Patient Note

**Trigger:** `patient.elderly_patient` (age ≥ 70) AND protocol has BSA-dosed drugs
**Output:** `Warning(level="info")` recommending prescriber review
**Effect:** Advisory only. Actual age-based dose reductions require structured `age_based_modifications` rules in the protocol JSON.

```python
@computed_field
@property
def elderly_patient(self) -> bool:
    return self.age_years >= 70
```

### Check 4: Poor Performance Status

**Trigger:** `patient.poor_performance_status` (ECOG ≥ 3)
**Output:** `Warning(level="critical")` — full-dose chemotherapy not appropriate
**Effect:** Warning only. Does not block doses.

### Check 5: Haematological Hard Stops

**Two sub-checks, both in the same block:**

**5a — Neutrophils <0.5:** Absolute contraindication. All chemotherapy doses are withheld from output (`treatment_absolutely_contraindicated = True`). Message: "TREATMENT CONTRAINDICATED".

**5b — Neutrophils 0.5–1.0:** Delay warning. Doses still calculated.

**5c — Platelets <50:** Absolute contraindication. Same hard stop as 5a.

**5d — Platelets 50–100:** Delay warning. Doses still calculated.

**5e — CrCl <10:** Severe renal failure warning. Does not block doses at this check (per-drug renal modifications applied later).

```python
# Hard stop thresholds (constants in models.py)
NEUTROPHIL_HARD_STOP = 0.5   # x10⁹/L
PLATELET_HARD_STOP   = 50    # x10⁹/L
```

### Check 6: Active Infection and Pregnancy

**Check 6a:** `patient.active_infection == True` → `Warning(level="critical")` — treatment must be delayed until afebrile.

**Check 6b:** `patient.pregnancy_status == "pregnant"` → `Warning(level="critical")` — all cytotoxics are potentially teratogenic, specialist review mandatory.

### Check 7: HBV Reactivation (Rituximab and Immunosuppressives)

**Trigger:** Protocol contains rituximab, blinatumomab, obinutuzumab, ofatumumab, ocrelizumab, or alemtuzumab.

**Sub-checks:**
- HBsAg positive + no prophylaxis → `Critical`: Fatal reactivation risk, entecavir must start before rituximab
- HBsAg positive + prophylaxis started → `Warning`: Monitor HBV DNA every 3 months
- Anti-HBc positive + no prophylaxis → `Warning`: Prior exposure, management plan required
- HBV serology not recorded → `Warning`: Screening required before rituximab

This is one of the most clinically significant checks. Rituximab causes profound B-cell depletion, which reactivates latent HBV. Untreated reactivation has a fatality rate of approximately 20-30%.

### Check 8: Baseline LVEF Before Anthracyclines

**Trigger:** Protocol contains doxorubicin, epirubicin, daunorubicin, idarubicin, or mitoxantrone.

**Sub-checks:**
- LVEF not provided + cardiac risk factors (age ≥70, prior cardiac history, prior anthracyclines) → `Warning`
- LVEF < 40% → Drug omitted (handled in contraindicated_drug_ids gate). See hard stop logic below.
- LVEF 40–49% → `Warning(level="critical")`: cardiology review required
- LVEF 50–54% → `Warning(level="warning")`: borderline, monitor closely

**The LVEF <40% hard stop:** The drug is added to `contraindicated_drug_ids`, which causes it to be removed from the output entirely. The threshold is `< 40`, not `< 50`.

```python
elif patient.lvef_percent < 40:
    pass  # Handled by contraindicated_drug_ids gate below
elif patient.lvef_percent < 50:
    warnings.append(Warning(level="critical", ...))
```

### Check 9: Peripheral Neuropathy Before Vincristine

**Trigger:** Protocol contains vincristine AND `patient.peripheral_neuropathy_grade` is set.

**Sub-checks:**
- Grade 1 → `Info`: monitor, reduce at grade 2
- Grade 2 → `Warning`: reduce vincristine to 1 mg
- Grade ≥ 3 → Drug omitted (added to `contraindicated_drug_ids`), `Critical` warning

The threshold for omission is CTCAE grade 3 neuropathy (severe, limiting self-care activities).

### Check 10: Tumour Lysis Syndrome Risk

**Trigger:** `patient.tls_risk` is set.

- High TLS risk → `Warning(level="critical")`: rasburicase + aggressive IV hydration required; allopurinol insufficient
- Intermediate TLS risk → `Warning(level="warning")`: allopurinol prophylaxis + IV hydration

### Check 11: Vincristine Hepatic Dosing (Partial Data)

**Trigger:** Protocol contains vincristine AND bilirubin > 51 µmol/L AND AST/ALT not provided.

**Output:** `Warning(level="warning")` describing what the dose should be at this bilirubin level and noting that AST/ALT must be reviewed before administration.

This fires when the condition is partially met but cannot be fully evaluated due to missing lab values. The engine is conservative: it gives the drug at standard dose but explicitly flags that the prescriber must check AST/ALT.

### Check 12: Allergy Cross-Checking

**Trigger:** Any protocol drug matches a patient allergy, directly or via cross-reactivity group.

**Cross-reactivity groups defined in `engine.py`:**
```python
ALLERGY_CROSS_REACTIVITY = {
    'platinum': ['cisplatin', 'carboplatin', 'oxaliplatin'],
    'taxane':   ['paclitaxel', 'docetaxel'],
    'anthracycline': ['doxorubicin', 'daunorubicin', 'epirubicin', 'idarubicin'],
}
```

Drug is added to `contraindicated_drug_ids` (omitted from output) and a `Critical` warning is emitted.

### Check 13: Irradiated Blood Products

**Trigger:** Protocol contains bendamustine, fludarabine, cladribine, or clofarabine.

**Output:** `Warning(level="critical")` — these drugs cause permanent T-cell immunosuppression requiring irradiated blood products for life.

```python
IRRADIATED_BLOOD_DRUGS = ['bendamustine', 'fludarabine', 'cladribine', 'clofarabine']
```

---

## 4. Dose Calculation Logic

### 4.1 BSA Calculation and Capping

The engine uses the Mosteller formula, computed in `PatientData.calculated_bsa`:

```python
raw_bsa = math.sqrt((self.height_cm * self.weight_kg) / 3600)
```

The capped BSA used for all dose calculations is:

```python
@computed_field
@property
def capped_bsa(self) -> float:
    return min(self.calculated_bsa, BSA_CAP_OBESE)  # BSA_CAP_OBESE = 2.0
```

In `generate_protocol`, BSA is rounded to 2 decimal places before any calculation:

```python
bsa = round(patient.capped_bsa, 2)
```

This is deliberate. Without rounding, a patient with BSA 1.875 m² would produce doses like `1.4 × 1.875 = 2.625 mg` vincristine. With rounding to 1.88 m², the dose is `1.4 × 1.88 = 2.632 mg` — different from the UI display, causing confusion. Rounding to 2 dp ensures consistency between the BSA shown in the header and the dose arithmetic.

**Important boundary:** The BSA cap applies at `calculated_bsa > BSA_CAP_OBESE` (strictly greater than 2.0). A patient with exactly BSA 2.00 m² is NOT capped and does NOT receive the capping notification. This is correct: the cap is for obese patients, not patients who happen to have exactly 2.0 m² BSA.

### 4.2 How modification_percent Works

`modification_percent` in the JSON and in `DoseModificationRule` is the **retained fraction as a percentage**. It is NOT the reduction amount.

| JSON factor | Meaning | modification_percent stored |
|---|---|---|
| `0.75` | Give 75% of dose | `75` |
| `0.50` | Give 50% of dose | `50` |
| `0.25` | Give 25% of dose | `25` |
| `0.00` | Omit (drug = None) | N/A (drug removed) |

The conversion in `_convert_dose_modification` in `json_protocol_loader.py`:

```python
modification_percent=int(round(factor * 100)) if factor < 1.0 else None,
```

In the engine's `_calculate_dose`, the dose modification factor is applied:

```python
calculated_dose *= best_mod_factor
```

Where `best_mod_factor = rule.modification_percent / 100.0` (i.e. `75 / 100.0 = 0.75`).

**For display to nurses:** The `modification_percent` in `CalculatedDose` on the response represents the **reduction percentage** (not retained):

```python
modification_percent = round((1 - best_mod_factor) * 100)
# factor=0.75 → modification_percent=25 → frontend shows "↓25% dose reduction applied"
```

This is a field used by the frontend for display only. Internally, the engine always works with the retained fraction.

### 4.3 How uncapped_calculated_dose Works for Hard Caps

When a drug has `max_dose` set and the BSA-calculated dose exceeds it, the engine:

1. Saves the pre-cap dose: `uncapped_calculated_dose = pre_cap_dose`
2. Sets `calculated_dose = drug.max_dose`
3. Returns `uncapped_calculated_dose` in the `CalculatedDose` response for transparent display

```python
if drug.max_dose:
    if calculated_dose > drug.max_dose + 1e-9:
        uncapped_calculated_dose = pre_cap_dose  # e.g. 2.63 mg
        calculated_dose = drug.max_dose           # 2.0 mg
```

For vincristine: a patient with BSA 1.9 m² has calculated dose `1.4 × 1.9 = 2.66 mg`. The cap applies: `calculated_dose = 2.0`, `uncapped_calculated_dose = 2.66`. The frontend shows both values so the pharmacist understands why the dose is lower than the BSA-based calculation.

The epsilon `1e-9` prevents floating-point false positives where `2.0000000001 > 2.0` due to IEEE 754 arithmetic.

### 4.4 Dose Banding Logic

After modification rules are applied, `_apply_dose_banding` rounds the dose to pharmacopoeia-standard increments. Implemented in `engine.py`:

```python
def band_to(dose: float, increment: float) -> float:
    banded = round(round(dose / increment) * increment, 2)
    return banded if banded > 0 else increment
```

Key drugs and their bands:

| Drug | Band (mg) |
|---|---|
| Rituximab | Nearest 100 mg (up if ≥50 remainder) |
| Azacitidine | Nearest 25 mg |
| Carboplatin | Nearest 50 mg |
| Cisplatin | Nearest 10 mg |
| Cyclophosphamide | Nearest 100 mg |
| Doxorubicin, Epirubicin | Nearest 5 mg |
| Gemcitabine | Nearest 200 mg |
| Vincristine, Vinca alkaloids | Nearest 0.5 mg (minimum 0.5 mg) |
| Oxaliplatin | Nearest 5 mg |
| Gemcitabine | Nearest 200 mg |

The banded dose is stored in `CalculatedDose.banded_dose`. The `calculated_dose` field always contains the exact BSA/modification-derived value. This allows the pharmacist to see both: the exact calculated dose (for verification) and the banded dose (for preparation).

### 4.5 Cycle-Specific Content Filtering

Before dose calculation, `_get_cycle_specific_content` selects which drugs apply to the current cycle:

1. If `cycle_variations` contains an entry matching the current cycle number or range, use that variation's drug list.
2. Otherwise, use the main `protocol.drugs` list, but pass it through `_adjust_days_for_cycle` to omit CYCLE 1 ONLY entries for cycles > 1.

The take-home list gets similar treatment, plus an additional final-cycle filter:

```python
is_final_cycle = (request.cycle_number >= protocol.total_cycles)
if is_final_cycle:
    instr = (drug.special_instructions or "").lower()
    if "next treatment" in instr or "next cycle" in instr or "cycles 1" in instr:
        continue
```

This prevents "prednisolone on morning of next treatment day" from appearing on the cycle 6 prescription when there is no cycle 7.

---

## 5. The Compound Condition Parser

This is the most technically complex part of the system. `_parse_dm_condition` in `json_protocol_loader.py` converts a free-text condition string into a structured `DoseModificationRule` with primary + optional secondary condition fields.

### 5.1 Full Parser Code Walkthrough

```python
def _parse_dm_condition(condition_str: str) -> dict:
```

**Step 1: Normalise unicode**
```python
s = condition_str.replace('–', '-').replace('—', ' ').lower()
```
En-dashes and em-dashes are normalised. The string is lowercased. This is critical because the NHS PDFs use typographic dashes in ranges like `30–50`.

**Step 2: Detect primary parameter**
```python
PARAM_KEYWORDS = [
    ('bilirubin', 'bilirubin'),
    ('crcl', 'creatinine_clearance'),
    ('creatinine clearance', 'creatinine_clearance'),
    ('gfr', 'creatinine_clearance'),
    ('neutrophil', 'neutrophils'),
    ('platelet', 'platelets'),
    ('haemoglobin', 'hemoglobin'),
    ('hemoglobin', 'hemoglobin'),
    ('ast/alt', 'ast'),   # must come before 'ast' and 'alt'
    ('ast', 'ast'),
    ('alt', 'alt'),
]
```
The first keyword found in the lowercase string determines the `parameter`. Order matters: `ast/alt` must come before `ast` alone, otherwise `ast/alt` would match as `ast`.

**Step 3: Detect AND / OR / AND-OR connector**
```python
andor_m = re.search(r'\s+(and/or)\s+', substr_full)
and_m   = re.search(r'\s+(and)\s+',   substr_full)
or_m    = re.search(r'\s+(or)\s+',    substr_full)
connector_m = None
if andor_m:
    connector = "OR"   # AND/OR treated as OR
    connector_m = andor_m
elif and_m and (not or_m or and_m.start() < or_m.start()):
    connector = "AND"
    connector_m = and_m
elif or_m:
    connector = "OR"
    connector_m = or_m
```

Note that `AND/OR` is treated as `OR`. The clinical interpretation is: either condition triggers the modification. In RCHOP21, "Bilirubin 30-50 AND/OR AST/ALT >3×ULN" means the doxorubicin dose should be reduced to 50% if either criterion is met independently.

**Step 4: Split primary and secondary clauses**
```python
if connector_m:
    primary_substr = substr_full[:connector_m.start()]
    secondary_substr = substr_full[connector_m.end():]
```

The primary clause is everything before the connector. The secondary clause is everything after.

**Step 5: Parse thresholds with `_parse_threshold_from_substr`**

This helper does the numeric extraction.

```python
def _parse_threshold_from_substr(substr: str, uln: float = 40.0) -> dict:
```

**Priority order within `_parse_threshold_from_substr`:**

1. **xULN range** (`2-3×uln`): Uses regex `r'(\d+(?:\.\d+)?)\s*[-]\s*(\d+(?:\.\d+)?)\s*[x×]\s*uln'`
   → multiplies both bounds by `uln` (default 40)
   → `2-3×ULN` → `range(80, 120)`

2. **xULN greater-than** (`>3×uln`): `r'>(\d+(?:\.\d+)?)\s*[x×]\s*uln'`
   → `>3×ULN` → `greater_than(120)`

3. **xULN less-than** (`<3×uln`): `r'<(\d+(?:\.\d+)?)\s*[x×]\s*uln'`

4. **Plain greater-than** (`>85`)

5. **Plain less-than** (`<30`)

6. **Plain range** (`30-50`): Pattern `r'(\d{2,}(?:\.\d+)?)\s*[-]\s*(\d{2,}(?:\.\d+)?)'`
   **Critical constraint: `\d{2,}` requires at least two digits.** This prevents misidentifying bilirubin threshold like `>1.0` as a range (the `-` in the ULN xULN range patterns takes priority, but single-digit ranges would fail). For values like `10-20`, `30-50`, `51-85`, `60-180` this works correctly.

7. **"normal" keyword** → `condition_type="normal"` (no threshold value)

### 5.2 What the Parsed Output Dict Looks Like

For `"Hepatic impairment — Doxorubicin: Bilirubin <30 µmol/L AND AST/ALT 2–3×ULN"`:

```python
{
    "parameter": "bilirubin",
    "condition_type": "less_than",
    "threshold_value": 30.0,
    "threshold_low": None,
    "threshold_high": None,
    "secondary_parameter": "ast",
    "secondary_connector": "AND",
    "secondary_condition_type": "range",
    "secondary_threshold_value": None,
    "secondary_threshold_low": 80.0,   # 2 × 40
    "secondary_threshold_high": 120.0, # 3 × 40
}
```

For `"Hepatic impairment — Vincristine: Bilirubin 30–51 µmol/L OR AST/ALT 60–180 units/L"`:

```python
{
    "parameter": "bilirubin",
    "condition_type": "range",
    "threshold_value": None,
    "threshold_low": 30.0,
    "threshold_high": 51.0,
    "secondary_parameter": "ast",
    "secondary_connector": "OR",
    "secondary_condition_type": "range",
    "secondary_threshold_value": None,
    "secondary_threshold_low": 60.0,
    "secondary_threshold_high": 180.0,
}
```

### 5.3 How the Engine Evaluates Compound Conditions

In `_apply_modification_rule` in `engine.py`:

```python
# Primary condition evaluation
condition_met = evaluate_condition(value, rule)

if not condition_met:
    return False, 1.0, ""

# Secondary condition
if rule.secondary_parameter and rule.secondary_connector:
    sec_value = param_map.get(sec_key)

    if sec_value is None:
        # Missing secondary lab value
        if rule.secondary_connector == "AND":
            return False, 1.0, ""  # Cannot confirm both — conservative, do not fire
        # OR: primary met, secondary unknown — still fires
    else:
        sec_met = evaluate_condition(sec_value, _SecRule())

        if rule.secondary_connector == "AND" and not sec_met:
            return False, 1.0, ""
        if rule.secondary_connector == "OR" and not sec_met:
            pass  # Primary already met — rule still fires
```

**Conservative missing-data behaviour:** For AND rules, if the secondary lab value is missing, the rule does NOT fire. This prevents inappropriate dose reductions when incomplete lab data is available.

For the `"normal"` condition type:
```python
if rule.secondary_condition_type == "normal":
    sec_met = sec_value <= 40  # ULN = 40 U/L hardcoded
```

---

## 6. How to Write Clinical Tests

### 6.1 Test Architecture

Tests are written as HTTP calls against the running API (`http://localhost:8000/api/v1/protocol/generate`). The test suite `backend/qa_test_100.py` provides a reusable `run_case` and `audit` function.

For individual protocol testing, use the direct call pattern:

```python
def generate(protocol_code, cycle_number, patient_data):
    payload = {
        "protocol_code": protocol_code,
        "cycle_number": cycle_number,
        "include_premeds": True,
        "include_take_home": True,
        "patient": patient_data
    }
    r = requests.post(f"{BASE}/api/v1/protocol/generate", json=payload)
    return r.json()
```

### 6.2 Standard Patient Setup

Every RCHOP21 test starts from a "normal" patient — healthy enough that no safety checks fire, allowing isolation of the specific condition being tested:

```python
BASE_PATIENT = {
    "weight_kg": 75,
    "height_cm": 175,
    "age_years": 55,
    "performance_status": 1,
    "neutrophils": 2.5,
    "platelets": 180,
    "hemoglobin": 13.0,
    "creatinine_clearance": 80.0,
    "bilirubin": 10.0,
    "ast": None,
    "alt": None,
}
```

To test a specific dose modification, override only the relevant fields. This isolates the condition.

### 6.3 Testing Every Row of the Hepatic Dose Table

The RCHOP21 doxorubicin hepatic table has 4 rows. Each row requires at minimum: one test in the middle of the condition range, one test at the boundary.

**Template for row 1 (Bilirubin <30 AND AST/ALT 2-3×ULN → 75%):**

```python
def test_doxorubicin_75pct():
    """Bilirubin <30 AND AST 2-3×ULN → doxorubicin reduced to 75%"""
    patient = {**BASE_PATIENT, "bilirubin": 20.0, "ast": 90.0}  # bili<30, AST in 80-120
    data = generate("LYMPHOMA-RCHOP21", 1, patient)

    drugs = {d["drug_name"]: d for d in data["chemotherapy_drugs"]}
    dox = drugs["Doxorubicin"]

    # BSA = sqrt(75 * 175 / 3600) = 1.91 m² → dose = 50 × 1.91 × 0.75 = 71.6 mg → banded to 70
    expected_bsa = round(math.sqrt(75 * 175 / 3600), 2)
    expected_pre_band = round(50 * expected_bsa * 0.75, 2)

    assert dox["dose_modified"] == True
    assert dox["modification_percent"] == 25  # display: 25% reduction
    # calculated_dose should be close to expected (within banding)
    assert abs(dox["calculated_dose"] - expected_pre_band) < 1.0
```

**Boundary test (bili = 29 vs bili = 30):**

```python
def test_doxorubicin_75pct_boundary():
    """Boundary: bili=29 fires rule, bili=30 does not (for this specific row)"""
    # bili=29: <30 AND AST in range → 75%
    patient_in = {**BASE_PATIENT, "bilirubin": 29.0, "ast": 90.0}
    data_in = generate("LYMPHOMA-RCHOP21", 1, patient_in)
    dox_in = {d["drug_name"]: d for d in data_in["chemotherapy_drugs"]}["Doxorubicin"]
    assert dox_in["dose_modified"] == True

    # bili=30: does NOT satisfy <30 (it's exactly 30, not <30)
    # Falls into "Bilirubin 30-50 AND/OR AST/ALT >3×ULN" territory if AST is also elevated
    # With AST=90 (2-3×ULN), bili=30: primary "bilirubin<30" fails, but "bilirubin 30-50" fires as OR
    # → 50% reduction (second row)
    patient_out = {**BASE_PATIENT, "bilirubin": 30.0, "ast": 90.0}
    data_out = generate("LYMPHOMA-RCHOP21", 1, patient_out)
    dox_out = {d["drug_name"]: d for d in data_out["chemotherapy_drugs"]}["Doxorubicin"]
    assert dox_out["dose_modified"] == True
    assert dox_out["modification_percent"] == 50  # second row now applies
```

### 6.4 Testing AND vs OR Conditions

**AND condition (both must be met):**

```python
def test_doxo_75pct_requires_both():
    """Row 1 is AND: if AST is normal (<2×ULN), rule should NOT fire even if bili<30"""
    patient_ast_normal = {**BASE_PATIENT, "bilirubin": 20.0, "ast": 30.0}  # AST<80 (normal)
    data = generate("LYMPHOMA-RCHOP21", 1, patient_ast_normal)
    dox = {d["drug_name"]: d for d in data["chemotherapy_drugs"]}["Doxorubicin"]
    assert dox["dose_modified"] == False
```

**OR condition (either fires the rule):**

```python
def test_vincristine_50pct_or_condition():
    """Vincristine row 1 is OR: bili 30-51 OR AST/ALT 60-180"""
    # Only bilirubin elevated (AST normal) → should fire
    patient_bili_only = {**BASE_PATIENT, "bilirubin": 40.0, "ast": 20.0}
    data = generate("LYMPHOMA-RCHOP21", 1, patient_bili_only)
    vcr = {d["drug_name"]: d for d in data["chemotherapy_drugs"]}["Vincristine"]
    assert vcr["dose_modified"] == True

    # Only AST elevated (bili normal) → should also fire
    patient_ast_only = {**BASE_PATIENT, "bilirubin": 10.0, "ast": 80.0}
    data2 = generate("LYMPHOMA-RCHOP21", 1, patient_ast_only)
    vcr2 = {d["drug_name"]: d for d in data2["chemotherapy_drugs"]}["Vincristine"]
    assert vcr2["dose_modified"] == True
```

### 6.5 Testing Drug Omission

```python
def test_doxorubicin_omitted_severe_hepatic():
    """Bilirubin >85 → doxorubicin omitted entirely"""
    patient = {**BASE_PATIENT, "bilirubin": 100.0}
    data = generate("LYMPHOMA-RCHOP21", 1, patient)
    drug_names = [d["drug_name"] for d in data["chemotherapy_drugs"]]
    assert "Doxorubicin" not in drug_names
    # Critical warning should be present
    warning_texts = [w["message"] for w in data["warnings"]]
    assert any("OMITTED" in w.upper() or "omit" in w.lower() for w in warning_texts)
```

### 6.6 Testing Vincristine Max Dose Cap

```python
def test_vincristine_max_dose_cap():
    """BSA>1.43 causes calculated vincristine >2mg; cap at 2mg"""
    # BSA 1.5m²: 1.4 × 1.5 = 2.1mg → capped to 2.0mg
    patient = {**BASE_PATIENT, "weight_kg": 85, "height_cm": 180}  # BSA ≈ 2.06 → capped to 2.0
    data = generate("LYMPHOMA-RCHOP21", 1, patient)
    vcr = {d["drug_name"]: d for d in data["chemotherapy_drugs"]}["Vincristine"]
    assert vcr["calculated_dose"] == 2.0
    assert vcr["dose_modified"] == True
    assert vcr["uncapped_calculated_dose"] > 2.0
```

### 6.7 Testing Cycle-Specific Items

```python
def test_allopurinol_cycle1_only():
    """Allopurinol take-home only appears on cycle 1"""
    data_c1 = generate("LYMPHOMA-RCHOP21", 1, BASE_PATIENT)
    th_names_c1 = [d["drug_name"] for d in data_c1.get("take_home_medicines", [])]
    assert "Allopurinol" in th_names_c1

    data_c2 = generate("LYMPHOMA-RCHOP21", 2, BASE_PATIENT)
    th_names_c2 = [d["drug_name"] for d in data_c2.get("take_home_medicines", [])]
    assert "Allopurinol" not in th_names_c2

def test_next_cycle_prednisolone_not_on_cycle_6():
    """'Morning of next treatment' prednisolone not issued on final cycle"""
    data_c5 = generate("LYMPHOMA-RCHOP21", 5, BASE_PATIENT)
    th_c5 = [d for d in data_c5.get("take_home_medicines", [])]
    # "next treatment day" prednisolone should appear on cycle 5
    next_cycle_items = [d for d in th_c5 if "next" in (d.get("special_instructions") or "").lower()]
    assert len(next_cycle_items) > 0

    data_c6 = generate("LYMPHOMA-RCHOP21", 6, BASE_PATIENT)
    th_c6 = [d for d in data_c6.get("take_home_medicines", [])]
    next_cycle_items_c6 = [d for d in th_c6 if "next" in (d.get("special_instructions") or "").lower()]
    assert len(next_cycle_items_c6) == 0
```

### 6.8 The 64-Test Methodology

For RCHOP21, 64 targeted clinical tests were written. The breakdown:

| Category | Test count |
|---|---|
| Doxorubicin hepatic table (4 rows × 2 boundary tests each) | 8 |
| Doxorubicin AND condition isolation (no fire when only one criterion) | 4 |
| Vincristine hepatic table (3 rows × 2 boundary tests each) | 6 |
| Vincristine OR condition isolation | 3 |
| Cyclophosphamide renal table (2 rows × 2 boundary tests) | 4 |
| Vincristine max dose cap + uncapped_dose display | 3 |
| BSA capping notification (BSA >2.0, =2.0 boundary) | 2 |
| Haematological hard stops (neutrophils, platelets) | 4 |
| Haematological delay warnings | 4 |
| HBV warnings (positive, negative, unknown, prophylaxis started) | 4 |
| LVEF checks (none, <40, 40-49, 50-54, ≥55) | 5 |
| Peripheral neuropathy (grade 1, 2, ≥3) | 3 |
| Cycle-specific items (allopurinol C1, prednisolone next-cycle C5/C6) | 4 |
| Floating-point dose display (no trailing zeros/2.715999...) | 2 |
| Pre-medication list completeness (ondansetron, chlorphenamine, paracetamol, prednisolone) | 4 |
| Rescue medication list completeness | 2 |
| Monitoring list completeness | 2 |
| BSA rounding consistency | 2 |
| **Total** | **64** |

---

## 7. Common Bugs and How We Found / Fixed Them

### Bug 1: Duplicate elif Block SyntaxError

**What happened:** During early engine development, a second `elif` block was added for the neutrophil condition (adding the `<1.0` delay check alongside the existing `<0.5` hard stop), but the second `elif` repeated the same condition. Python raised `SyntaxError: invalid syntax` at startup.

**How found:** Server failed to start; Python traceback in console.

**Fix:** Changed the duplicate `elif patient.neutrophils < 0.5` to `elif patient.neutrophils < 1.0`. The correct structure is:
```python
if patient.neutrophils < 0.5:
    # hard stop
elif patient.neutrophils < 1.0:
    # delay warning
```

### Bug 2: AND/OR Connector Not Detected

**What happened:** The regex `r'\s+(and)\s+'` matched `"AND"` correctly, but the condition string `"Bilirubin 30-50 AND/OR AST/ALT >3×ULN"` was not detected as having a connector. The word `and/or` contains a forward slash, so neither the `and` nor the `or` regex matched as standalone words.

**How found:** Test `test_doxo_50pct_either_criterion` failed — the doxorubicin reduction was not firing for a patient with elevated AST alone.

**Fix:** Added `andor_m = re.search(r'\s+(and/or)\s+', substr_full)` and checked it first, before the individual AND/OR checks. The `AND/OR` pattern must precede `AND` in priority, otherwise `and/or` would partially match `and`.

### Bug 3: xULN Notation Not Parsed for Single-Digit Multipliers

**What happened:** The range parser used `r'(\d{2,})...'` (two or more digits) for range detection to avoid false positives from single-digit numbers in other contexts. But the xULN range pattern also inherited this restriction accidentally in an early version, causing `1-2×ULN` to fail parsing.

**How found:** A protocol with `AST/ALT 1-2×ULN` range (less common but valid) did not fire. Debug print showed `_parse_threshold_from_substr` returning `{}` for this substring.

**Fix:** The xULN patterns use `r'(\d+(?:\.\d+)?)'` (one or more digits with optional decimal), which correctly handles single-digit multipliers. The plain range pattern retains `\d{2,}` to avoid false positives in non-range contexts.

### Bug 4: BSA Cap Boundary (> vs >=)

**What happened:** Initial code used `if patient.calculated_bsa >= BSA_CAP_OBESE:` for the cap decision. This meant a patient with exactly 2.0 m² BSA received the "BSA capped" notification on the output, which was confusing and incorrect. The cap exists for obese patients (BSA substantially above 2.0), not patients who happen to be precisely 2.0 m².

**How found:** Manual test with a patient engineered to have exactly 2.0 m² BSA (70 kg, 163 cm). The notification said "BSA capped at 2.0 m² (actual: 2.00 m²)" — nonsensical.

**Fix:** Changed to `if patient.calculated_bsa > BSA_CAP_OBESE:` (strictly greater than). The `capped_bsa` property uses `min(self.calculated_bsa, BSA_CAP_OBESE)`, which is fine at the boundary — `min(2.0, 2.0) = 2.0` and `bsa_was_capped` returns False.

### Bug 5: Floating-Point Display (2.7159999...)

**What happened:** Without explicit rounding, doses were calculated as e.g. `50 × 1.88 × 0.75 = 70.5` mg for doxorubicin, but for some BSA values the IEEE 754 arithmetic produced `70.49999999...` or `71.9999999...`. These appeared in the JSON response and in the printed output.

**How found:** Integration test comparing expected dose (computed with Python `round()`) to response `calculated_dose` — discrepancy at the 10th decimal place, but display looked wrong.

**Fix:** `_round_dose` in the engine applies `round(dose, 2)` to all calculated doses. The 2dp rounding is deliberate — pharmacy can round further for specific products (e.g. vincristine to nearest 0.1 mg per RCHOP21 notes), but the engine produces a clean 2dp value for the JSON.

### Bug 6: Cap vs Reduction Label Confusion

**What happened:** The `modification_percent` field on `CalculatedDose` was being used for two different things:
- For dose reductions (hepatic, renal): stores the **reduction percentage** (e.g. 25 for a 25% reduction)
- For max dose caps (vincristine): stores the **reduction percentage** relative to the uncapped dose (e.g. 24 for vincristine 2.0 mg from 2.63 mg calculated)

Frontend code assumed `modification_percent` always meant "give X% of dose", which broke when a cap was applied.

**Fix:** For cap scenarios:
```python
modification_percent = round((1 - drug.max_dose / pre_cap_dose) * 100)
```
This stores the reduction percentage. The `uncapped_calculated_dose` field is the canonical display field showing what the dose would have been without the cap. Frontend now checks for `uncapped_calculated_dose` to distinguish cap scenarios from reduction scenarios.

### Bug 7: Cycle 6 Take-Home Next-Cycle Prednisolone

**What happened:** On cycle 6 of RCHOP21, the take-home list included "Prednisolone 100mg on morning of next treatment day". There is no cycle 7, so this is clinically incorrect and confusing — the patient would be issued prednisolone they should never take.

**How found:** Manual review of cycle 6 output. A pharmacist noted the instruction made no sense.

**Root cause:** The take-home filtering only checked `cycle_number < protocol.total_cycles` for cycle-specific variation suppression, but did not inspect the `special_instructions` content of individual take-home items.

**Fix:** Added content-based filter in `generate_protocol`:
```python
is_final_cycle = (request.cycle_number >= protocol.total_cycles)
if is_final_cycle:
    instr = (drug.special_instructions or "").lower()
    if "next treatment" in instr or "next cycle" in instr or "cycles 1" in instr:
        continue
```
And updated the JSON `special_instructions` for the prednisolone take-home item to include "CYCLES 1–5 ONLY".

### Bug 8: CrCl=52 Spurious Renal Warning

**What happened:** For a patient with CrCl = 52 ml/min, an RCHOP21 request triggered a renal warning about cyclophosphamide dose reduction. CrCl 52 ml/min is normal renal function for many patients — the cyclophosphamide reduction threshold is `CrCl 10-20` (severe) and `CrCl <10` (very severe), not anything close to 52.

**How found:** Clinical pharmacist review of a real patient output. The patient had slightly reduced CrCl (52 ml/min, expected for their age) but otherwise normal function, and the output said to reduce cyclophosphamide.

**Root cause:** An incorrectly written condition string used `CrCl <60` in a test/draft version of the dose modification entry, matching a cisplatin contraindication threshold that had been copy-pasted from a different protocol.

**Fix:** Verified all RCHOP21 renal condition strings against the UHS RCHOP21 v1.2 PDF:
- `CrCl 10-20 ml/min` → cyclophosphamide 75%
- `CrCl <10 ml/min` → cyclophosphamide 50%

The `CrCl <60` condition belongs to cisplatin protocols (hard stop) and must not appear in RCHOP21.

### Bug 9: LVEF Form Threshold Wrong (50 vs 40)

**What happened:** The frontend form asked for LVEF and displayed a warning indicator for "LVEF <50%". The engine treats LVEF <40% as an absolute contraindication (anthracycline omitted) and LVEF 40-49% as a critical warning. Using 50 as the form threshold meant the warning indicator showed even for LVEF 50-54% patients (borderline, warranting monitoring but not a red alert on the form).

**How found:** Clinical pharmacist noted that the form showed a red "LVEF warning" for a patient with LVEF 52%, who would typically receive doxorubicin with additional monitoring — not a contraindication.

**Fix:** The form threshold was corrected to 40 (the contraindication threshold). The engine still emits a warning for LVEF 40-54% at different levels (critical for 40-49%, warning for 50-54%), but the form-level alert highlights only the critical threshold.

### Bug 10: Frontend Next Button Disabled (sex Field + Falsy 0)

**What happened:** The patient form included a `sex` field (required for Cockcroft-Gault CrCl calculation: `sex_factor = 1.0 if sex == "male" else 0.85`). When the user entered `sex = "female"`, the CrCl calculation worked, but when the form field value was `0` (a numeric code for "male" in one early frontend version), the conditional `if patient.sex` evaluated as falsy, failing the validation gate and disabling the "Next" button.

**How found:** Tester reported "Next button always greyed out when sex is set to Male" — reproducible.

**Root cause:** The form-level validation used `if (sex)` (JavaScript truthy check). The value `0` for male is falsy in JavaScript. The "Next" button enable condition depended on all required fields being truthy.

**Fix:** Changed the validation to `if (sex !== null && sex !== undefined)` (explicit null check, not falsy check) for numeric-coded fields. Also standardised sex field to string values `"male"` / `"female"` to eliminate the falsy-zero problem entirely.

---

## 8. Protocol-Specific Checklist

Use this checklist when encoding and verifying any new protocol. Every item must be confirmed before the protocol is marked as done.

### Encoding Checklist

- [ ] Protocol code matches the NHS/UHS document code exactly (preserving case as used in clinical practice)
- [ ] Protocol name includes the full expansion (e.g. "RCHOP21 - Rituximab-Cyclophosphamide-Doxorubicin-Prednisolone-Vincristine (21-day cycle)")
- [ ] `cycle_length_days` matches the PDF (21, 28, 14, 56 — check carefully)
- [ ] `number_of_cycles` matches the PDF (typically 6, but varies: 3, 4, 8, 12...)
- [ ] All chemotherapy drugs encoded in `drugs[]` with:
  - [ ] Correct dose (float, not string)
  - [ ] Correct `dose_unit` (especially mg/m² vs mg — common mistake)
  - [ ] Correct `route` (especially IV bolus vs IV infusion — affects preparation)
  - [ ] Correct `days` array
  - [ ] `infusion_duration_hours` if stated
  - [ ] `max_dose` and `max_dose_unit` if stated (vincristine 2 mg is the most common)
  - [ ] `diluent` and `diluent_volume_ml` if stated
  - [ ] Administration order captured in `notes` if relevant
- [ ] Pre-medications in `pre_medications[]` (structured dicts preferred over strings)
- [ ] Take-home medicines in `take_home_medicines[]`
- [ ] Rescue medications in `rescue_medications[]`
- [ ] All dose modification table rows encoded as structured `dose_modifications[]` entries
- [ ] AND/OR conditions correctly formatted with spaces: `" AND "`, `" OR "`, `" AND/OR "`
- [ ] xULN values use `×ULN` notation (NOT pre-calculated), letting the parser apply ULN=40
- [ ] Range conditions use two-digit-or-more numbers (e.g. `10-20`, `30-50`, `60-180`)
- [ ] Cycle-specific items marked: `"CYCLE 1 ONLY"` or `"CYCLES 1–5 ONLY"` in `notes`
- [ ] `special_warnings[]` covers:
  - [ ] Vesicants (list drug names + reference to NPSA/local guideline)
  - [ ] Cardiac limits (LVEF threshold, cumulative anthracycline limit)
  - [ ] HBV screening/prophylaxis if rituximab or other anti-CD20 present
  - [ ] Irradiated blood requirement if fludarabine/bendamustine present
  - [ ] Elderly dose considerations if relevant
  - [ ] Any other category-specific alert from the PDF
- [ ] `monitoring[]` covers all pre-cycle labs and special monitoring requirements
- [ ] `required_patient_fields[]` lists every field the UI must collect for this protocol

### Testing Checklist

- [ ] Test suite written covering every dose modification table row
- [ ] Boundary tests for every threshold (value just inside, value just outside)
- [ ] AND condition test: one condition met but not the other → rule does NOT fire
- [ ] OR condition test: one condition met → rule fires; other condition met → rule fires
- [ ] Drug omission test (factor 0.0 rows): drug absent from response, critical warning present
- [ ] Vincristine max dose cap test (if applicable)
- [ ] BSA cap test (patient with BSA >2.0)
- [ ] Cycle-specific item suppression tests (CYCLE 1 ONLY items not on cycle 2)
- [ ] Final-cycle suppression tests (CYCLES 1-5 ONLY items not on final cycle)
- [ ] HBV warning tests (if rituximab or similar present)
- [ ] LVEF tests (if anthracycline present)
- [ ] All 64-test methodology applied (scale the count to the protocol's complexity)

### PDF Review Checklist

- [ ] Printed PDF output reviewed line-by-line against original NHS document
- [ ] Drug names match PDF (not abbreviated; proper capitalisation)
- [ ] Doses match PDF to correct significant figures
- [ ] Units match (µmol/L, not mmol/L; mg/m², not mg/m2 in display)
- [ ] Monitoring instructions word-match PDF where clinically critical
- [ ] Warnings contain the exact safety numbers (e.g. NPSA reference, 450 mg/m² cumulative limit)

---

## 9. JSON Schema Reference

This is the full annotated schema using RCHOP21 as the canonical example. Every field is shown with its type, meaning, and whether it is required or optional.

```json
[
  {
    // REQUIRED — The protocol identifier used by the API and engine
    // Convention: DISEASE-PROTOCOLNAME, uppercase, hyphens, no spaces
    // Must match what the frontend and clinicians call the protocol
    "protocol_code": "LYMPHOMA-RCHOP21",

    // REQUIRED — Full human-readable name for display
    // Include the expansion of the acronym for searchability
    "protocol_name": "RCHOP21 - Rituximab-Cyclophosphamide-Doxorubicin-Prednisolone-Vincristine (21-day cycle)",

    // REQUIRED — The tumour type / indication this protocol treats
    // Used for categorisation in the UI
    "disease_site": "CD20 positive Non-Hodgkin Lymphoma",

    // OPTIONAL — Category for grouping (lymphoma, leukaemia, gi, lung, etc.)
    "category": "lymphoma",

    // REQUIRED — Length of one treatment cycle in days
    // This is NOT the treatment duration — it's when cycle 2 starts relative to cycle 1
    "cycle_length_days": 21,

    // REQUIRED — Standard total number of cycles
    "number_of_cycles": 6,

    // REQUIRED — Array of chemotherapy and targeted drug objects
    "drugs": [
      {
        // REQUIRED — Drug name, match NHS/BNF preferred name
        "drug_name": "Rituximab",

        // REQUIRED — Per-administration dose, float
        "dose": 375.0,

        // REQUIRED — Unit string, from the allowed set:
        // "mg/m²", "mg", "g/m²", "g", "mg/kg", "units/m²", "mcg", "mcg/m²"
        "dose_unit": "mg/m²",

        // REQUIRED — Route, from the allowed set:
        // "IV infusion", "IV bolus", "Oral", "Subcutaneous", "Intramuscular", "Nebulised"
        "route": "IV infusion",

        // REQUIRED — Days within the cycle this drug is given, 1-indexed integers
        "days": [1],

        // OPTIONAL — Duration in hours (float). Used for display in the administration notes.
        // null if not applicable (IV bolus drugs, oral drugs)
        // For vincristine "10 minutes" → infusion_duration_hours: 0.167
        "infusion_duration_hours": null,

        // OPTIONAL — Maximum dose cap in flat units (e.g. 2.0 mg for vincristine)
        // null if no cap applies
        // Engine enforces this as a hard cap with a CRITICAL warning
        "max_dose": null,
        "max_dose_unit": null,

        // OPTIONAL — Diluent solution for IV drugs
        // Use canonical names: "Sodium chloride 0.9%", "Glucose 5%", "Water for injection"
        "diluent": "Sodium chloride 0.9%",

        // OPTIONAL — Diluent volume in millilitres (integer)
        "diluent_volume_ml": 500,

        // OPTIONAL but strongly recommended — All clinical notes for this drug
        // Includes: administration instructions, vesicant warnings, special handling,
        // administration order, dose rounding instructions, banding reference
        "notes": "Intravenous infusion in 500ml sodium chloride 0.9%. Rate of administration varies — refer to rituximab administration guidelines. Rounded to nearest 100mg (up if halfway). FIRST in administration order. Check patient has taken prednisolone 100mg oral on morning of treatment before starting rituximab."
      },

      {
        "drug_name": "Vincristine",
        "dose": 1.4,
        "dose_unit": "mg/m²",
        "route": "IV bolus",
        "days": [1],
        "infusion_duration_hours": 0.167,
        // CRITICAL: vincristine hard cap. Without this, a BSA 2.0 patient gets 2.8mg.
        // Overdose causes permanent paralysis and death.
        "max_dose": 2.0,
        "max_dose_unit": "mg",
        "diluent": "Sodium chloride 0.9%",
        "diluent_volume_ml": 50,
        "notes": "Intravenous bolus in 50ml sodium chloride 0.9% over 10 minutes. Maximum dose 2mg. Round to nearest 0.1mg (up if halfway). VESICANT — NPSA/2008/RRR04 must be followed. Administer AFTER doxorubicin."
      },

      {
        "drug_name": "Prednisolone",
        "dose": 100.0,
        // FLAT DOSE — note "mg" not "mg/m²". Engine will not multiply by BSA.
        "dose_unit": "mg",
        "route": "Oral",
        // Multi-day drug: days 1 through 5
        "days": [1, 2, 3, 4, 5],
        "infusion_duration_hours": null,
        "max_dose": null,
        "max_dose_unit": null,
        "diluent": null,
        "diluent_volume_ml": null,
        "notes": "100mg once daily oral on days 1-5. Patient self-administers on morning of chemotherapy (day 1) and for 4 days after. Take with or after food. Day 1 dose also counts as rituximab pre-medication. Check patient has taken day 1 dose before rituximab is started."
      }
    ],

    // REQUIRED — Pre-medications to be given before chemotherapy
    // Can be dicts (preferred, structured) or strings (parsed automatically by _parse_premed_string)
    // Use strings for simple standard pre-meds (ondansetron 8mg etc.) — the parser handles them
    // Use dicts for non-standard premeds or those needing precise control
    "pre_medications": [
      "Prednisolone 100mg oral — patient must take on morning of treatment DAY 1 BEFORE rituximab is started. Nurse to verify dose taken and document time. If forgotten, administer 100mg oral 30 minutes prior to rituximab.",
      "Chlorphenamine 10mg intravenous — 30 minutes prior to rituximab",
      "Paracetamol 1000mg oral — 30 minutes prior to rituximab",
      "Ondansetron 8mg oral or intravenous — 15-30 minutes prior to chemotherapy (after rituximab is running, before doxorubicin)"
    ],

    // REQUIRED — Medications to take home (antiemetics, steroids, support drugs)
    // Include cycle-specificity markers in the string where applicable
    "take_home_medicines": [
      // "CYCLES 1–5 ONLY" — suppressed on final cycle
      "Prednisolone 100mg oral once a day on morning of next treatment day (day 1 of next cycle) — CYCLES 1–5 ONLY. Do not issue for cycle 6 (no further cycle follows).",
      "Prednisolone 100mg oral once a day for 4 days starting day 2 (take with or after food)",
      "Metoclopramide 10mg oral three times a day when required",
      "Ondansetron 8mg oral twice a day for 3 days starting evening of day 1",
      // "CYCLE 1 ONLY" — suppressed on cycles 2+
      "Allopurinol 300mg oral once a day for 21 days — CYCLE 1 ONLY"
    ],

    // REQUIRED — PRN / rescue medications
    "rescue_medications": [
      "Hydrocortisone 100mg intravenous when required for rituximab infusion related reactions",
      "Salbutamol 2.5mg nebulised when required for rituximab related bronchospasm",
      "Pethidine 25–50mg intravenous when required for rituximab related rigors that fail to respond to steroids"
    ],

    // REQUIRED — Array of dose modification rules
    // One object per PDF table row
    "dose_modifications": [
      {
        // REQUIRED — Human-readable condition string for display and parsing
        // Must follow the parser format described in Section 5
        "condition": "Hepatic impairment — Doxorubicin: Bilirubin <30 µmol/L AND AST/ALT 2–3×ULN",

        // REQUIRED — Drug name affected by this rule
        // Must match drug_name in drugs[] exactly (case-insensitive match in engine)
        "drug_name": "Doxorubicin",

        // REQUIRED — Retained fraction (0.0 = omit, 1.0 = full dose, 0.75 = 75% retained)
        "factor": 0.75,

        // REQUIRED — Clinical note explaining the rule, source reference
        "notes": "Reduce doxorubicin to 75% (UHS RCHOP21 v1.2: bilirubin <30 AND AST/ALT 2-3×ULN)."
      },
      {
        "condition": "Hepatic impairment — Doxorubicin: Bilirubin >85 µmol/L",
        "drug_name": "Doxorubicin",
        // factor 0.0 → drug omitted entirely from output
        "factor": 0.0,
        "notes": "Omit doxorubicin (UHS RCHOP21 v1.2: bilirubin >85 µmol/L — severe hepatic impairment)."
      },
      {
        // Delay-only rules use factor 1.0 — full dose is still given when treatment proceeds
        "condition": "Neutrophils <1×10⁹/L on proposed day 1 of cycle",
        "drug_name": "Cyclophosphamide",
        "factor": 1.0,
        "notes": "Delay until neutrophils ≥1×10⁹/L. Consider G-CSF as secondary prophylaxis. Reconsider treatment options if not recovered after 14 days."
      }
    ],

    // REQUIRED — Clinical warnings for the protocol
    // Each string is a standalone alert shown in the output
    // Do NOT duplicate what the engine generates automatically (HBV, LVEF checks etc.)
    // DO include drug-specific safety requirements, vesicant handling, special populations
    "special_warnings": [
      "VESICANT DRUGS: Vincristine is a vesicant (doxorubicin also vesicant when included). Extravasation causes severe tissue necrosis. Follow NPSA/2008/RRR04 for vincristine. Discontinue immediately if extravasation suspected.",
      "CARDIAC: Baseline LVEF required before starting doxorubicin in patients with history of cardiac problems, cardiac risk factors, or age ≥70. Maximum lifetime cumulative doxorubicin dose: 450 mg/m² (standard); reduced to 400 mg/m² if prior cardiac history or prior mediastinal/pericardial radiotherapy. Discontinue doxorubicin if cardiac failure develops.",
      "HEPATITIS B REACTIVATION: Check hepatitis B status (HBsAg and anti-HBc) before starting rituximab. Rituximab can cause fatal hepatitis B reactivation. Anti-CD20 antibody causes profound B-cell depletion.",
      "RITUXIMAB — CYTOKINE RELEASE SYNDROME (CRS): Severe CRS characterised by dyspnoea, bronchospasm, hypoxia, fever, chills, rigors, urticaria, angioedema, hypotension, elevated LDH. Can cause acute respiratory failure and death. Occurs within 1–2 hours of first infusion. Medicinal products for allergic reactions must be available immediately.",
      "RITUXIMAB — PROGRESSIVE MULTIFOCAL LEUKOENCEPHALOPATHY (PML): Monitor for new or worsening neurological/cognitive/psychiatric symptoms at regular intervals. If PML suspected, suspend rituximab until excluded. If PML confirmed, permanently discontinue.",
      "ELDERLY (≥70 years): Consider initial dose reduction in patients over 70 years of age. Doses may be escalated to full dose on subsequent cycles according to tolerability.",
      "PREDNISOLONE: Must be taken on morning of treatment (day 1) BEFORE rituximab is started. Nurse must verify this. If patient forgot, administer 100mg oral 30 minutes prior to rituximab.",
      "ANTI-INFECTIVE PROPHYLAXIS: Consider aciclovir 400mg twice daily oral and co-trimoxazole 960mg oral Mon/Wed/Fri in high-risk patients. Mouthwashes per local policy for mucositis. Gastric protection (PPI or H2 antagonist) in patients at high risk of GI ulceration."
    ],

    // REQUIRED — Monitoring requirements list
    // Each string is one monitoring action, written as an imperative
    "monitoring": [
      "FBC, LFTs and U&Es prior to day 1 of each cycle",
      "Check hepatitis B status (HBsAg and anti-HBc) before cycle 1",
      "LVEF (echocardiogram) before starting doxorubicin in patients with cardiac history, cardiac risk factors, or age ≥70",
      "Consider blood transfusion if patient symptomatic of anaemia or haemoglobin <8g/dL",
      "Assess for cold or flu-like symptoms prior to each rituximab infusion (URTI increases risk of rituximab-associated hepatotoxicity)",
      "Monitor for signs of rituximab infusion-related reactions during each infusion",
      "Monitor for signs and symptoms of cytokine release syndrome",
      "Monitor for neurological/cognitive symptoms at each cycle (PML surveillance)",
      "Vincristine neurotoxicity assessment each cycle (peripheral neuropathy, constipation, jaw pain)"
    ],

    // REQUIRED — Fields the clinician must fill in for this protocol
    // Keys are PatientData field names; values are reason strings (or empty "")
    // The UI uses this list to show/hide form fields
    "required_patient_fields": [
      "neutrophil_count",
      "platelet_count",
      "creatinine_clearance",
      "bilirubin",
      "ast_alt",
      "lvef",
      "hepatitis_b_surface_antigen",
      "hepatitis_b_core_antibody",
      "prior_anthracycline_dose_mg_m2",
      "prior_mediastinal_radiation"
    ],

    // OPTIONAL — AUC dosing flag (for carboplatin). null if not applicable.
    "auc_dosing": null
  }
]
```

---

## 10. The 565 Protocol Roadmap

### 10.1 Complexity Tiers

Group protocols by encoding complexity to estimate time and test effort:

**Tier 1 — Simple (2-4 hours to encode + test, ~20 tests)**
- Single BSA-dosed drug
- No hepatic or renal dose modification table
- No max dose caps
- No cycle-specific variations
- Examples: single-agent maintenance regimens (rituximab maintenance, ibrutinib monotherapy)
- Estimated count in 565: approximately 80-100 protocols

**Tier 2 — Standard (4-8 hours, ~40 tests)**
- 2-5 drugs, mixed flat + BSA doses
- One dose modification table (typically renal OR hepatic, not both)
- Standard pre-meds and take-home
- Examples: R-CHOP14, CHOP, CVP, BEAM conditioning
- Estimated count: approximately 200-250 protocols

**Tier 3 — Complex (8-16 hours, ~64 tests)**
- 4-8 drugs
- Multiple dose modification tables (hepatic AND renal)
- Compound AND/OR conditions
- Cycle-specific variations (loading dose, step-up dosing, ramp-up)
- Max dose caps on multiple drugs
- Examples: RCHOP21 (reference), R-FCR, DHAP, R-ICE, BEAM+autograft
- Estimated count: approximately 180-200 protocols

**Tier 4 — Specialist (16-32 hours, ~100 tests)**
- AUC dosing (carboplatin)
- Complex cycle variations (blinatumomab 4-week continuous infusion with bag schedule)
- Multiple sub-protocols with cross-references
- Age-banded regimens (paediatric-to-adult transitions)
- Examples: Blinatumomab B-ALL, high-dose methotrexate with rescue, HDAC
- Estimated count: approximately 50-80 protocols

### 10.2 Group by Drug Class for Shared Patterns

Protocols sharing the same drug class share dose modification patterns. Encode one, then copy/adapt the relevant sections:

**Anthracycline-containing protocols** (doxorubicin/epirubicin/daunorubicin)
- All need the hepatic table (bilirubin + AST/ALT)
- All need the LVEF check in `required_patient_fields`
- All need the cumulative dose warning in `special_warnings`
- Template: RCHOP21 doxorubicin section
- Examples: CHOP, CODOX-M, DHAP, ESHAP, DA-R-EPOCH, ABVD

**Vincristine-containing protocols**
- All need the hepatic table (bilirubin + AST/ALT, different thresholds from doxorubicin)
- All need `max_dose: 2.0` on vincristine
- All need neuropathy monitoring in `monitoring[]`
- Template: RCHOP21 vincristine section
- Examples: CVP, CODOX-M, CHOP, VMP, VRD, MACE

**Rituximab-containing protocols**
- All need HBV screening in `required_patient_fields` and `special_warnings`
- All need CRS and PML warnings
- All need chlorphenamine/paracetamol/prednisolone pre-meds
- Template: RCHOP21 pre_medications + special_warnings
- Examples: R-CHOP14, R-DHAP, R-ICE, R-GDP, G-CHOP, RB (bendamustine+rituximab)

**Platinum-containing protocols** (cisplatin/carboplatin/oxaliplatin)
- Cisplatin: contraindicated at CrCl <60 (engine handles automatically)
- Carboplatin: AUC dosing, renal monitoring
- Oxaliplatin: peripheral neuropathy grading, no renal dose cap needed
- Template: cisplatin section from any lung or GI protocol

**Fludarabine/bendamustine protocols**
- Both require irradiated blood warning (engine handles automatically, but also encode in `special_warnings`)
- Both require `required_patient_fields: ["hepatitis_b_surface_antigen"]` if rituximab co-administered

### 10.3 Shared Test Templates

For each drug class, maintain a template test module that can be parameterised with the protocol code:

```python
def run_anthracycline_hepatic_tests(protocol_code, drug_name="Doxorubicin"):
    """Run standard hepatic dose table tests for any anthracycline protocol."""
    # Test rows at: bili<30+AST2-3xULN, bili30-50+/or>3xULN, bili51-85, bili>85
    ...

def run_vincristine_tests(protocol_code):
    """Run vincristine cap and neuropathy tests for any vinca alkaloid protocol."""
    ...

def run_rituximab_hbv_tests(protocol_code):
    """Run HBV warning tests for any rituximab-containing protocol."""
    ...
```

This template approach means protocols 2-N in a drug class each take perhaps 25% of the time of the first protocol — you are adding the protocol-specific tests (renal thresholds, extra drugs) on top of an already-verified template.

### 10.4 Estimated Test Count per Protocol Type

| Protocol type | Test count estimate |
|---|---|
| Single-agent maintenance (flat dose, no DM table) | 15-25 |
| 2-drug combination (one DM table) | 25-35 |
| Standard R-CHOP-like (5 drugs, hepatic + renal tables) | 50-70 |
| Complex multi-drug with cycle variations | 80-120 |
| Blinatumomab/step-up dosing specialist protocols | 100-150 |

**Projection for 565 protocols:**
At an average of 40 tests per protocol: 22,600 individual test assertions covering the full protocol library.

The `qa_test_100.py` framework handles the generic checks (A through T: BSA arithmetic, banding, warnings format, cycle-specific suppression). Protocol-specific tests need only focus on the dose modification logic, drug-specific caps, and clinical edge cases unique to that protocol.

---

## Appendix A: PatientData Fields Reference

Fields required by the engine for RCHOP21-class protocols:

| Field | Type | Unit | Notes |
|---|---|---|---|
| `weight_kg` | float | kg | Required for BSA |
| `height_cm` | float | cm | Required for BSA |
| `age_years` | int | years | Required for elderly check, anthracycline limit |
| `performance_status` | int (0-4) | ECOG | Required |
| `neutrophils` | float | ×10⁹/L | Required, hard stop at <0.5 |
| `platelets` | float | ×10⁹/L | Required, hard stop at <50 |
| `hemoglobin` | float | g/dL | Required |
| `creatinine_clearance` | float | ml/min | Required for renal DM rules |
| `bilirubin` | float | µmol/L (SI) | Required for hepatic DM rules |
| `ast` | float or null | U/L | Required for compound hepatic conditions |
| `alt` | float or null | U/L | Required for compound hepatic conditions |
| `hep_b_surface_antigen` | "positive"/"negative"/"unknown" | — | Required for rituximab protocols |
| `hep_b_core_antibody` | "positive"/"negative"/"unknown" | — | Required for rituximab protocols |
| `lvef_percent` | float or null | % | Required for anthracycline protocols |
| `peripheral_neuropathy_grade` | int (0-4) or null | CTCAE | Required for vincristine protocols |
| `prior_anthracycline_dose_mg_m2` | float or null | mg/m² (doxo-equivalent) | Required for repeat-treatment patients |
| `prior_mediastinal_radiation` | bool | — | Reduces anthracycline limit to 400 mg/m² |
| `known_allergies` | list[str] | — | Drug names, cross-checked against protocol |

## Appendix B: RCHOP21 Dose Modification Table Summary

| Parameter | Condition | Drug | Action | Factor |
|---|---|---|---|---|
| Neutrophils | <1.0 on day 1 | Cyclophosphamide, Doxorubicin | Delay | 1.0 |
| Neutrophils | Grade 4 + febrile neutropenia | Cyclophosphamide | Add G-CSF | 1.0 |
| Neutrophils | Grade 4 + infection despite G-CSF | Cyclophosphamide, Doxorubicin | Reduce 50% | 0.5 |
| Neutrophils | Grade 4 recurs after 50% reduction | Cyclophosphamide | Stop | 0.0 |
| Platelets | <100 on day 1 | Cyclophosphamide, Doxorubicin | Delay | 1.0 |
| Platelets | Grade 4 thrombocytopenia | Cyclophosphamide, Doxorubicin | Reduce 50% | 0.5 |
| Bilirubin | <30 AND AST/ALT 2-3×ULN | Doxorubicin | Reduce 25% | 0.75 |
| Bilirubin | 30-50 AND/OR AST/ALT >3×ULN | Doxorubicin | Reduce 50% | 0.5 |
| Bilirubin | 51-85 µmol/L | Doxorubicin | Reduce 75% | 0.25 |
| Bilirubin | >85 µmol/L | Doxorubicin | Omit | 0.0 |
| Bilirubin OR AST/ALT | 30-51 µmol/L OR 60-180 U/L | Vincristine | Reduce 50% | 0.5 |
| Bilirubin AND AST/ALT | >51 AND normal (<40) | Vincristine | Reduce 50% | 0.5 |
| Bilirubin AND AST/ALT | >51 AND >180 | Vincristine | Omit | 0.0 |
| CrCl | 10-20 ml/min | Cyclophosphamide | Reduce 25% | 0.75 |
| CrCl | <10 ml/min | Cyclophosphamide | Reduce 50% | 0.5 |
| Neuropathy | Grade 2 motor or Grade 3 sensory | Vincristine | Reduce to flat 1 mg | (manual) |

---

*This document reflects the SOPHIA codebase as of March 2026. The source files governing all behaviour documented here are:*
- `/backend/engine.py` — Core calculation and safety check logic
- `/backend/json_protocol_loader.py` — JSON parsing, condition parser, protocol loading
- `/backend/models.py` — All Pydantic data models, safety constants, validators
- `/backend/protocol_jsons_normalized/lymphoma-9.json` — Contains LYMPHOMA-RCHOP21 at line 1111
- `/backend/qa_test_100.py` — QA test suite framework
