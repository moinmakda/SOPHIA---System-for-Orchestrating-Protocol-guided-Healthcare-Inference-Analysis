# SOPHIA — System for Orchestrating Protocol-guided Healthcare Inference & Analysis

**NHS Chemotherapy Protocol Engine by Jivana AI**

![Backend](https://img.shields.io/badge/Backend-FastAPI%20%2B%20Python-009688)
![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB)
![Protocols](https://img.shields.io/badge/Protocols-566%20NHS-blueviolet)
![License](https://img.shields.io/badge/License-MIT-green)

---

## CRITICAL SAFETY NOTICE

**THIS SYSTEM IS FOR CLINICAL DECISION SUPPORT ONLY.**

- This software is **NOT** a licensed medical device.
- It has **NOT** undergone regulatory approval (FDA / MHRA / CE marking).
- It **MUST NOT** be used for direct patient care without independent verification by a licensed prescriber and pharmacist.
- All protocols require dual sign-off before administration.

**Use of this system for patient care without proper clinical validation may result in patient harm or death.**

---

## What is SOPHIA?

SOPHIA is a full-stack clinical decision support tool for NHS oncology teams. It serves 566 structured chemotherapy protocols, applies patient-specific dose calculations, and returns a fully safety-checked drug schedule — including BSA-adjusted doses, dose modification flags, treatment delay alerts, pre-medication lists, and cumulative toxicity tracking.

Built to support real clinical workflow: enter patient demographics and today's blood results, select a protocol and cycle number, and SOPHIA outputs a print-ready prescription sheet with every dose calculated and every safety check surfaced.

---

## Feature Overview

### Protocol Engine (`engine.py`)
- **BSA calculation** — Mosteller formula, capped at 2.0 m2 per ASCO guidelines for obese patients
- **Weight-based dosing** — mg/kg drugs (e.g. Aflibercept, Rituximab flat-dose) calculated from patient weight
- **Dose modification rules** — haematological and non-haematological toxicity rules per protocol applied automatically; "most conservative rule" wins when multiple apply
- **NHS dose banding** — 20+ drug classes banded to national agreed bands (Irinotecan, Carboplatin, Docetaxel, Paclitaxel, Rituximab, etc.)
- **Hard max-dose caps** — vincristine 2 mg (CRITICAL alert; overdose = death / permanent paralysis), cabazitaxel 25 mg, others
- **Treatment delay flags** — neutrophils < 1.0 x 10^9/L or platelets < 100 x 10^9/L
- **Hard stops** — neutrophils < 0.5, platelets < 50, or CrCl < 10 blocks treatment
- **Cycle-aware filtering** — monitoring instructions referencing past cycles (e.g. "Cycle 1 ECG") automatically suppressed for later cycles
- **Cycle-specific day adjustment** — drugs described as "Cycle 1 only: Days 1 and 15; Cycle 2 onwards: Day 1" trimmed automatically per cycle
- **Drug omission logging** — omitted drugs recorded in `dose_modifications_applied` and surfaced as CRITICAL warnings (never silently dropped)

### Patient Safety
- **Mandatory lab enforcement** — neutrophils, platelets, haemoglobin, CrCl, and bilirubin required; no labs = no protocol
- **Allergy checking** — cross-reactivity groups (platinum, taxane, anthracycline)
- **ECOG PS warnings** — ECOG 3-4 flagged
- **Elderly dose reduction** — 20% reduction on BSA-based core drugs for patients age >= 70 years (where no structured age rule exists in the protocol)
- **Cumulative anthracycline tracking** — doxorubicin-equivalent conversion (epirubicin x 0.5, idarubicin x 5.0); tiered severity warnings at 80%, 90%, 100% of lifetime limit
- **Cumulative bleomycin tracking** — 400 units lifetime limit
- **Irradiated blood product alerts** — bendamustine, fludarabine, cladribine, clofarabine flagged
- **Tiered bilirubin / renal warnings** — bilirubin >30 / >51 / >85 umol/L and CrCl <60 with cisplatin / <30 with other nephrotoxic drugs

### Patient Data Model
Full clinical picture captured per patient:

| Category | Fields |
|---|---|
| Demographics | weight, height, age, sex, ECOG PS |
| Core labs | neutrophils, platelets, Hb, CrCl, bilirubin |
| Metabolic | LDH, urate, calcium, beta-2-microglobulin, magnesium, vitamin D |
| Virology | HBsAg, HBcAb, HCV Ab, HIV, EBV, CMV, VZV |
| Disease | histology, stage, CT result, immunoglobulins |
| Cardiac / prior Rx | LVEF, heart disease flag, prior anthracycline (mg/m2), prior mediastinal RT, prior bleomycin |
| Metabolic baseline | HbA1c, fasting glucose |
| G6PD / lung | G6PD status, FEV1 %, smoker flag |
| Post-cycle tracking | post-cycle neutrophils, platelets, bilirubin, GFR, HbA1c, glucose, motor weakness, gross haematuria |

### Protocol Coverage (566 protocols)

| Tumour Group | Example Protocols |
|---|---|
| Breast | AC, EC, FEC, Paclitaxel, Docetaxel, Capecitabine, Pertuzumab-Trastuzumab, Palbociclib-Letrozole, Abemaciclib combinations, T-DM1, Sacituzumab |
| Colorectal / GI | FOLFOX, FOLFIRI, CAPOX, CAPIRI, Aflibercept-FOLFIRI, Ramucirumab-FOLFIRI, Irinotecan monotherapy, Capecitabine, FLOT, ECF, EOF |
| Lung | Carboplatin-Paclitaxel, Pemetrexed combinations, Osimertinib, Crizotinib, Durvalumab, Atezolizumab |
| Haematology | RCHOP, CHOP, R-BENDAMUSTINE, ABVD, BEACOPP, FLAG-IDA, AZA+VEN, HyperCVAD, FCR, VRd, Daratumumab combinations |
| Gynaecology | Carboplatin-Paclitaxel, Carboplatin monotherapy, Bevacizumab combinations, Olaparib, Niraparib |
| Skin / CNS / Endocrine / Head & Neck | Multiple histology-specific protocols |

### Flexible Protocol Builder
- Load any protocol and selectively include/exclude individual drugs
- Quick-add buttons dynamically derived from the loaded protocol's own drugs — never hardcoded
- Edit doses, routes, days, and frequencies inline
- Submits as a custom regimen via `POST /api/v1/protocol/generate-custom` with full safety checking

### Patient JSON Adapter
Converts external payloads (mobile app / WhatsApp intake forms) into strict `PatientData` objects:
- Parses range strings like `"0.8-<1"` to lower bound (conservative)
- Infers cycle number from `cycle{n}_complete` flags
- Maps post-cycle lab prefixes automatically

---

## Architecture

```
React Frontend (Vite)
    |
    |  HTTP / JSON
    v
FastAPI Backend (main_enhanced.py)
    |-- GET  /api/v1/protocols                            list & search 566 protocols
    |-- GET  /api/v1/protocols/{code}                     protocol detail
    |-- POST /api/v1/protocol/generate                    standard protocol generation
    |-- POST /api/v1/protocol/generate-custom             flexible regimen builder
    |-- POST /api/v1/protocol/generate-from-patient-json  mobile/WhatsApp adapter
    +-- GET  /api/v1/drugs                                drug list
         |
         |-- engine.py                  dose calc, BSA/weight, modifications, safety checks
         |-- models.py                  Pydantic v2 models (PatientData, Protocol, ProtocolResponse)
         |-- json_protocol_loader.py    loads 566 protocols from protocol_jsons_normalized/
         |-- protocol_jsons_normalized/ 566 structured protocol JSON files
         |-- adapters.py                PatientStateAdapter (external JSON -> PatientData)
         +-- requirements.txt
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main_enhanced:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.
Interactive API docs at `http://localhost:8000/docs`.

---

## API Reference

### Generate a Standard Protocol

```http
POST /api/v1/protocol/generate
Content-Type: application/json

{
  "protocol_id": "rchop21",
  "protocol_code": "RCHOP21",
  "cycle_number": 1,
  "patient": {
    "weight_kg": 75,
    "height_cm": 175,
    "age_years": 58,
    "sex": "male",
    "performance_status": 0,
    "neutrophils": 2.1,
    "platelets": 160,
    "hemoglobin": 12.0,
    "creatinine_clearance": 75,
    "bilirubin": 12
  },
  "include_premeds": true,
  "include_take_home": true
}
```

### Generate a Custom Regimen

```http
POST /api/v1/protocol/generate-custom
Content-Type: application/json

{
  "regimen_name": "Aza-Ven",
  "cycle_number": 1,
  "cycle_length_days": 28,
  "patient": { ... },
  "drugs": [
    {
      "drug_name": "Azacitidine",
      "dose": 75,
      "dose_unit": "mg/m2",
      "route": "SC injection",
      "days": [1,2,3,4,5,6,7]
    },
    {
      "drug_name": "Venetoclax",
      "dose": 400,
      "dose_unit": "mg",
      "route": "Oral",
      "days": [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28]
    }
  ]
}
```

### Submit from External Patient JSON

```http
POST /api/v1/protocol/generate-from-patient-json?protocol_code=RCHOP21
Content-Type: application/json

{
  "age": 58, "height": 172, "weight": 80,
  "bilirubin": 12, "gfr": 75,
  "neutrophils": 2.1, "platelets": 145, "hemoglobin": 11.5,
  "hepbsurface": "negative", "hepbcore": "positive", "hiv": "negative",
  "histology": "DLBCL", "dstage": "Ann Arbor IV", "g6pd": "normal",
  "cycle1_complete": true,
  "post1neutrophils": "0.8-<1",
  "post1platelets": 110, "post1bilirubin": 14, "post1crcl": 70
}
```

The adapter infers cycle 2, parses `"0.8-<1"` to `0.8`, and triggers a treatment delay flag.

---

## Project Structure

```
SOPHIA/
|-- backend/
|   |-- main_enhanced.py           FastAPI app + all endpoints
|   |-- engine.py                  Dose calculation, modification rules, safety checks
|   |-- models.py                  Pydantic v2: PatientData, Protocol, ProtocolResponse
|   |-- json_protocol_loader.py    Loads all 566 protocols from protocol_jsons_normalized/
|   |-- protocol_jsons_normalized/ 566 structured NHS protocol JSON files
|   |-- adapters.py                PatientStateAdapter (external JSON -> PatientData)
|   |-- protocol_data.py           Legacy hardcoded protocols (superseded by JSON loader)
|   +-- requirements.txt
|
|-- frontend/
|   +-- src/
|       |-- App.jsx                         Main app state, routing, generate logic
|       |-- components/
|       |   |-- Header.jsx
|       |   |-- PatientForm.jsx             Full patient form incl. virology, disease, prior Rx
|       |   |-- ProtocolDisplay.jsx         Output rendering + print-to-PDF
|       |   +-- FlexibleProtocolBuilder.jsx Custom drug selector / regimen builder
|       +-- data/drugLibrary.js             Standalone drug library for free-form builder
|
+-- README.md
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `VITE_API_URL` | No | Override backend URL (default: `http://localhost:8000`) |

---

## Recent Changes (v2.1 — March 2026)

- **566 NHS protocols** loaded from structured JSON files
- **NHS dose banding** for 20+ drug classes per national agreed bands
- **Elderly dose reduction** (age >= 70, 20% on BSA-based core drugs)
- **Cumulative toxicity tracking** — anthracycline doxorubicin-equivalent and bleomycin
- **Cycle-aware filtering** — past-cycle ECG / monitoring instructions suppressed automatically
- **Cycle-specific day adjustment** — e.g. Fulvestrant Day 15 auto-removed from cycle 2+
- **Tiered bilirubin / renal warnings** with CrCl < 60 + cisplatin CRITICAL alert
- **Duration display** — infusion times shown as hours (e.g. "46 hr") not decimal days
- **Flexible Protocol Builder** quick-add buttons now protocol-derived, never hardcoded
- **Dose modification transparency** — max-dose caps and reductions shown inline per drug
- **LHRH agonist concurrent medication** promoted to CRITICAL warning

---

## License

MIT License.

---

## Disclaimer

This software is for research and clinical decision support only. All chemotherapy protocols must be independently verified by a qualified clinical pharmacist and oncologist before administration to any patient. The developers and Jivana AI accept no liability for clinical decisions made using this software.

---

Built by the Jivana AI team.
