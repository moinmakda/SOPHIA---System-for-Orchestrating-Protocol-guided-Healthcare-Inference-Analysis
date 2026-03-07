# SOPHIA — System for Orchestrating Protocol-guided Healthcare Inference & Analysis

**Chemotherapy Protocol Management System by Jivana AI**

![Architecture](https://img.shields.io/badge/Architecture-FastAPI%20%2B%20React-blue)
![AI](https://img.shields.io/badge/AI-Google%20Gemini-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## CRITICAL SAFETY NOTICE

**THIS SYSTEM IS FOR CLINICAL DECISION SUPPORT ONLY.**

- This software is NOT a licensed medical device.
- It has NOT undergone regulatory approval (FDA / MHRA / CE).
- It MUST NOT be used for direct patient care without independent verification.
- All protocols require sign-off by a licensed prescriber AND a pharmacist.
- AI-extracted protocols carry an additional pharmacist review gate before use.

**Use of this system for patient care without proper clinical validation may result in patient harm or death.**

---

## What is SOPHIA?

SOPHIA is a full-stack clinical decision support tool for oncology teams. It takes structured patient data, applies chemotherapy protocol rules, and returns a fully calculated, safety-checked drug schedule — including BSA-adjusted doses, dose modification flags, treatment delay alerts, and pre-medication lists.

It ships with 31 built-in protocols (lymphoma, leukaemia, myeloma, CML) and can ingest any additional NHS/institutional PDF protocol via a Gemini-powered admin panel.

---

## Feature Overview

### Protocol Engine
- BSA calculation (Mosteller) capped at 2.0 m² per ASCO guidelines
- Automatic dose modifications for renal and hepatic impairment
- "Most conservative rule" — when multiple modification rules apply, the lowest resulting dose wins
- Vincristine hard cap at 2 mg (CRITICAL alert; overdose = death / permanent paralysis)
- Treatment delay flags when neutrophils < 1.0 × 10⁹/L or platelets < 100 × 10⁹/L
- Hard stops when neutrophils < 0.5, platelets < 50, or CrCl < 10
- Drug omission logging — when a drug is omitted by a dose rule, it is recorded in `dose_modifications_applied` and surfaced as a CRITICAL warning (not silently dropped)

### Patient Safety
- Mandatory lab enforcement — neutrophils, platelets, haemoglobin, CrCl, and bilirubin are required; no labs, no protocol
- Allergy checking with cross-reactivity awareness (e.g. penicillin → carbapenem caution)
- ECOG performance status warnings for PS 3–4
- Age-based dose reduction prompts for patients > 70 years
- Cumulative anthracycline and bleomycin toxicity tracking against lifetime limits
- Irradiated blood product alerts for eligible drugs (e.g. bendamustine)

### Extended Patient Data Model
Patient records carry a full clinical picture:

| Category | Fields |
|---|---|
| Demographics | weight, height, age, ECOG PS |
| Core labs | neutrophils, platelets, Hb, CrCl, bilirubin |
| Metabolic | LDH, urate, calcium, β2-microglobulin, magnesium, vitamin D |
| Virology | HBsAg, HBcAb, HCV Ab, HIV, EBV, CMV, VZV |
| Disease | histology, stage, CT result, immunoglobulins |
| Cardiac / prior Rx | LVEF, heart disease flag, prior anthracycline (mg/m²), prior mediastinal radiation, prior bleomycin |
| Metabolic baseline | HbA1c, fasting glucose |
| G6PD / lung | G6PD status, FEV1 %, smoker flag |
| Post-cycle tracking | post-cycle neutrophils, platelets, bilirubin, GFR, HbA1c, glucose, motor weakness, gross haematuria |

### Protocol-Specific Required Fields
Each protocol exposes a `required_patient_fields` map derived from its drugs. For example, RCHOP surfaces requirements for full virology panel (anti-CD20 → HBV reactivation risk), LVEF (anthracycline cardiotoxicity), and G6PD (rasburicase contraindication). The frontend displays these as a colour-coded checklist before the clinician submits.

### Custom Regimen Builder
Clinicians can:
- Take any built-in protocol and exclude individual drugs (e.g. AZA+VEN → AZA monotherapy)
- Build entirely free-form combinations (e.g. Azacitidine + 7+3) by selecting drugs, doses, dose units, routes, and days
- Custom regimens are submitted to `POST /api/v1/protocol/generate-custom`, receive the same BSA/weight calculations, vincristine cap, allergy checks, and delay detection as standard protocols, and are flagged `is_ai_generated: true` to trigger the pharmacist review gate

### AI-Powered Protocol Ingestion
- Upload any NHS/institutional chemotherapy PDF via the Admin Panel
- Google Gemini (gemini-2.0-flash) extracts: drugs, doses, dose units, routes, schedules, dose modification rules, pre-medications, take-home medicines, monitoring requirements, warnings, and `required_patient_fields`
- Extracted protocols are cached, versioned, and immediately searchable alongside built-in protocols
- Prompt version is tracked (`_PROMPT_VERSION`); incrementing it busts all cached extractions

### Patient JSON Adapter
A `PatientStateAdapter` converts external patient JSON payloads (from mobile apps or WhatsApp-based intake forms) into strict `PatientData` objects:
- Parses range strings like `"0.8-<1"` → lower bound `0.8` (conservative safety approach)
- Cycle-state logic: infers which cycle to generate based on `cycle{n}_complete` flags
- Selects post-cycle lab prefix (`post{n}neutrophils`, etc.) automatically
- Maps all virology, disease characterisation, and post-cycle tracking fields

---

## Architecture

```
React Frontend (Vite)
    │
    │  HTTP / JSON
    ▼
FastAPI Backend (main_enhanced.py)
    ├── GET  /api/v1/protocols              — list & search protocols
    ├── GET  /api/v1/protocols/{code}       — protocol detail + required_patient_fields
    ├── POST /api/v1/protocol/generate      — standard protocol generation
    ├── POST /api/v1/protocol/generate-custom          — custom regimen builder
    ├── POST /api/v1/protocol/generate-from-patient-json  — mobile/WhatsApp adapter
    ├── POST /api/v1/admin/upload           — PDF ingestion (Gemini)
    ├── GET  /api/v1/admin/stats
    └── GET  /api/v1/admin/categories
         │
         ├── engine.py          — dose calc, modification rules, delay logic
         ├── models.py          — Pydantic v2 models (PatientData, Protocol, ProtocolResponse, CustomRegimenRequest)
         ├── protocol_data.py   — 31 hardcoded protocols + DRUGS dict (51 entries) + infer_required_patient_fields()
         ├── gemini_parser.py   — Gemini extraction prompt (v4) + caching + convert_to_protocol_model()
         ├── adapters.py        — PatientStateAdapter (external JSON → PatientData)
         └── ingested_protocols.json  — persisted AI-extracted protocols
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Gemini API key (for PDF ingestion)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
echo "GEMINI_API_KEY=your-key-here" > .env
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
  "protocol_code": "RCHOP21",
  "cycle_number": 1,
  "patient": {
    "weight_kg": 75,
    "height_cm": 175,
    "age_years": 58,
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

### Submit from External Patient JSON (Mobile / WhatsApp)

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

The adapter infers cycle 2, parses `"0.8-<1"` → `0.8`, and triggers a treatment delay flag (neutrophils < 1.0).

### Upload a Protocol PDF

```http
POST /api/v1/admin/upload
Content-Type: multipart/form-data

file: <PDF>
disease_category: lymphoma
```

---

## Built-in Protocols (31 total)

| Category | Protocols |
|---|---|
| B-cell lymphoma | RCHOP21, CHOP21, RCVP, BR, GDP, BENDA, R-BENDA |
| Hodgkin lymphoma | ABVD, BEACOPP-ESC |
| T-cell lymphoma | CHOEP21, CHOP21 |
| CLL | FCR, FC |
| Myeloma | VRd (Bortezomib-Lenalidomide-Dex), Daratumumab-VRd, MPT |
| AML | 7+3 (Dauno/Ara-C), FLAG-IDA, MACE, Clofarabine-Ara-C |
| MDS / AML low-intensity | AZA+VEN, Azacitidine SC, Gilteritinib |
| ALL | HyperCVAD-A, HyperCVAD-B |
| CML | Imatinib |
| Supportive | G-CSF, Mesna, Leucovorin rescue |

---

## Project Structure

```
SOPHIA/
├── backend/
│   ├── main_enhanced.py          # FastAPI app + all endpoints
│   ├── engine.py                 # Dose calculation, modification rules, delay logic, custom regimen
│   ├── models.py                 # Pydantic v2: PatientData, Protocol, ProtocolResponse, CustomRegimenRequest
│   ├── protocol_data.py          # 31 protocols, DRUGS dict (51 entries), infer_required_patient_fields()
│   ├── gemini_parser.py          # Gemini prompt v4, caching, model conversion
│   ├── adapters.py               # PatientStateAdapter (external JSON → PatientData)
│   ├── ingest_protocols.py       # CLI tool to batch-ingest PDFs
│   ├── ingested_protocols.json   # Persisted AI-extracted protocols
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── App.jsx               # Main app state, routing, generate logic
│       ├── components/
│       │   ├── Header.jsx
│       │   ├── PatientForm.jsx               # Full patient form incl. virology, disease, prior Rx
│       │   ├── ProtocolDisplay.jsx
│       │   ├── FlexibleProtocolBuilder.jsx   # Custom drug selector
│       │   └── AdminPanel.jsx
│       └── utils/api.js          # All API calls incl. generateCustomRegimen()
│
└── README.md
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | For PDF ingestion | Google AI Studio key |
| `VITE_API_URL` | No | Override backend URL (default: `http://localhost:8000`) |

---

## License

MIT License.

---

## Disclaimer

This software is for research and clinical decision support only. All chemotherapy protocols must be independently verified by a qualified clinical pharmacist and oncologist before administration to any patient. The developers and Jivana AI accept no liability for clinical decisions made using this software.

---

Built by the Jivana AI team.
