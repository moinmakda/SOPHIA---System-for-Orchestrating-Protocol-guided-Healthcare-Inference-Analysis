# 🏥 ChemoProtocol Engine

## NHS Chemotherapy Protocol Management System with AI-Powered PDF Ingestion

A production-grade, scalable chemotherapy protocol management system that can dynamically generate personalized treatment protocols. Features Gemini AI integration for automatic PDF parsing, enabling expansion to any cancer type.

![Architecture](https://img.shields.io/badge/Architecture-FastAPI%20%2B%20React-blue)
![AI](https://img.shields.io/badge/AI-Google%20Gemini-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🌟 Features

### Core Functionality
- **Protocol Generation**: Generate personalized chemotherapy protocols based on patient data
- **BSA-Based Dosing**: Automatic dose calculation using Mosteller/Du Bois formulas
- **Dose Modifications**: Automatic adjustments for renal/hepatic impairment
- **Flexible Drug Selection**: Include/exclude specific drugs (e.g., AZA+VEN → AZA only)
- **Cycle-Specific Protocols**: Handle variations between treatment cycles
- **Print-Ready Output**: Generate professional protocol documents

### AI-Powered Expansion
- **Gemini PDF Parsing**: Upload any NHS protocol PDF and AI extracts structured data
- **Multi-Disease Support**: Expandable from lymphoma to breast, lung, colorectal, etc.
- **Automatic Indexing**: Protocols automatically categorized and searchable
- **Intelligent Extraction**: Extracts drugs, doses, schedules, modifications, warnings

### Technical Features
- **RESTful API**: Full-featured FastAPI backend with OpenAPI docs
- **React Frontend**: Modern, responsive UI with real-time calculations
- **Scalable Storage**: JSON-based storage (easily upgradeable to PostgreSQL)
- **Admin Panel**: Upload protocols, view statistics, manage categories

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CHEMOTHERAPY PROTOCOL ENGINE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────┐         ┌─────────────────┐         ┌──────────────┐ │
│   │   React UI      │◄───────►│   FastAPI       │◄───────►│   Gemini AI  │ │
│   │                 │         │   Backend       │         │   Parser     │ │
│   │ • Protocol      │         │                 │         │              │ │
│   │   Browser       │  HTTP   │ • /protocols    │  API    │ • PDF Parse  │ │
│   │ • Patient Form  │◄───────►│ • /generate     │◄───────►│ • Extract    │ │
│   │ • Drug Selector │         │ • /admin        │         │ • Structure  │ │
│   │ • Admin Panel   │         │ • /calculate    │         │              │ │
│   └─────────────────┘         └────────┬────────┘         └──────────────┘ │
│                                        │                                    │
│                                        ▼                                    │
│                          ┌─────────────────────────┐                       │
│                          │     Protocol Store      │                       │
│                          │                         │                       │
│                          │ • Hardcoded Protocols   │                       │
│                          │ • Ingested Protocols    │                       │
│                          │ • Protocol Index        │                       │
│                          └─────────────────────────┘                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Gemini API Key (for PDF parsing)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY="your-gemini-api-key"

# Run the server
uvicorn main_enhanced:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Visit `http://localhost:3000` to access the application.

---

## 📚 API Documentation

### Protocol Endpoints

#### List Protocols
```http
GET /api/v1/protocols?search=RCHOP&category=lymphoma
```

#### Get Protocol Details
```http
GET /api/v1/protocols/RCHOP21
```

#### Generate Personalized Protocol
```http
POST /api/v1/protocol/generate
Content-Type: application/json

{
  "protocol_code": "RCHOP21",
  "patient": {
    "weight_kg": 70,
    "height_cm": 175,
    "neutrophils": 2.5,
    "platelets": 150,
    "bilirubin": 15,
    "creatinine_clearance": 90
  },
  "cycle_number": 1,
  "excluded_drugs": ["rituximab"],
  "include_premeds": true,
  "include_take_home": true
}
```

**Response:**
```json
{
  "protocol_code": "CHOP21",
  "patient_bsa": 1.85,
  "chemotherapy_drugs": [
    {
      "drug_name": "Doxorubicin",
      "calculated_dose": 92.5,
      "calculated_dose_unit": "mg",
      "route": "IV bolus",
      "days": [1],
      "dose_modified": false
    }
  ],
  "warnings": [],
  "dose_modifications_applied": []
}
```

### Admin Endpoints

#### Upload Protocol PDF
```http
POST /api/v1/admin/upload
Content-Type: multipart/form-data

file: <PDF file>
disease_category: "breast_cancer"
```

#### Get System Statistics
```http
GET /api/v1/admin/stats
```

#### Get Categories
```http
GET /api/v1/admin/categories
```

---

## 🎯 Usage Examples

### Example 1: Generate R-CHOP without Rituximab

```python
import requests

response = requests.post("http://localhost:8000/api/v1/protocol/generate", json={
    "protocol_code": "RCHOP21",
    "patient": {
        "weight_kg": 75,
        "height_cm": 180
    },
    "cycle_number": 1,
    "excluded_drugs": ["Rituximab"]  # Exclude Rituximab → becomes CHOP
})

protocol = response.json()
print(f"Generated: {protocol['protocol_code']}")
for drug in protocol['chemotherapy_drugs']:
    print(f"  {drug['drug_name']}: {drug['calculated_dose']} {drug['calculated_dose_unit']}")
```

### Example 2: Dose Modification for Hepatic Impairment

```python
response = requests.post("http://localhost:8000/api/v1/protocol/generate", json={
    "protocol_code": "RCHOP21",
    "patient": {
        "weight_kg": 70,
        "height_cm": 175,
        "bilirubin": 60  # Elevated bilirubin
    },
    "cycle_number": 2
})

# Doxorubicin will be reduced to 50% due to bilirubin 30-50 µmol/L
```

### Example 3: Upload New Protocol (Expanding to Breast Cancer)

```python
with open("breast_cancer_AC_protocol.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/admin/upload",
        files={"file": f},
        data={"disease_category": "breast_cancer"}
    )

result = response.json()
print(f"Ingested: {result['protocol_code']} - {result['protocol_name']}")
print(f"Extracted {result['drugs_count']} drugs")
```

---

## 📁 Project Structure

```
chemo-protocol-engine/
├── backend/
│   ├── main_enhanced.py      # FastAPI application
│   ├── models.py             # Pydantic data models
│   ├── engine.py             # Protocol engine (dose calc, modifications)
│   ├── protocol_data.py      # Hardcoded protocol definitions
│   ├── gemini_parser.py      # AI-powered PDF parser
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── ProtocolBrowser.jsx
│   │   │   ├── PatientForm.jsx
│   │   │   ├── DrugSelector.jsx
│   │   │   ├── ProtocolDisplay.jsx
│   │   │   └── AdminPanel.jsx
│   │   ├── utils/
│   │   │   └── api.js
│   │   ├── App-enhanced.jsx
│   │   ├── App-enhanced.css
│   │   └── main.jsx
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── data/
│   ├── protocols/            # Ingested protocol JSON files
│   ├── parsed_protocols/     # Gemini parsing cache
│   └── uploads/              # Uploaded PDF files
│
└── README.md
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key for PDF parsing | For AI features |
| `VITE_API_URL` | Backend API URL (frontend) | No (defaults to localhost) |

### Gemini API Setup

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key
3. Set environment variable:
   ```bash
   export GEMINI_API_KEY="AIza..."
   ```

---

## 📊 Included Protocols

### Lymphoma Protocols (Built-in)
| Code | Name | Indication |
|------|------|------------|
| RCHOP21 | R-CHOP 21 | CD20+ Non-Hodgkin's Lymphoma |
| CHOP21 | CHOP 21 | Non-Hodgkin's Lymphoma |
| BR | Bendamustine-Rituximab | Relapsed/Refractory NHL |
| RCVP | R-CVP | Follicular Lymphoma |
| ABVD | ABVD | Hodgkin Lymphoma |
| GDP | GDP | Relapsed DLBCL |
| BENDA | Bendamustine | Indolent NHL |

### Expandable to Any Disease
Upload PDFs for:
- Breast Cancer (AC, TC, FEC, etc.)
- Lung Cancer (Cisplatin-Pemetrexed, Carboplatin-Paclitaxel)
- Colorectal (FOLFOX, FOLFIRI, CAPOX)
- Leukemia (AZA+VEN, FLAG-IDA)
- Multiple Myeloma (VRd, KRd)
- And more...

---

## 🔒 Safety Features

- **Max Dose Caps**: Vincristine capped at 2mg, etc.
- **Dose Modification Rules**: Automatic adjustments for organ impairment
- **Warning System**: Critical alerts for low counts, hepatic/renal issues
- **Irradiated Blood Warnings**: For bendamustine patients
- **Monitoring Requirements**: Lab requirements before each cycle

---

## 🚧 Future Roadmap

- [ ] PostgreSQL database integration
- [ ] User authentication & audit trails
- [ ] Protocol versioning & approval workflow
- [ ] Integration with hospital EMR systems
- [ ] Mobile app for bedside dosing
- [ ] Drug interaction checker
- [ ] Treatment calendar generation
- [ ] Patient outcome tracking

---

## 📜 License

MIT License - see LICENSE file for details.

---

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

---

## ⚠️ Disclaimer

This software is for educational and research purposes only. All chemotherapy protocols must be verified by qualified clinical pharmacists and oncologists before administration. The developers assume no liability for clinical decisions made using this software.

---

## 📞 Support

For questions or support, please open an issue on GitHub or contact the development team.

---

Built with ❤️ for healthcare by the Jivana AI team
