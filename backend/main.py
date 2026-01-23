"""
Chemotherapy Protocol Engine - FastAPI Application
NHS Lymphoma Protocols API
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn

from models import (
    ProtocolRequest, ProtocolResponse, ProtocolSummary, DrugSummary,
    PatientData, Protocol
)
from engine import ProtocolEngine, calculate_bsa_mosteller, calculate_creatinine_clearance
from protocol_data import get_all_protocols, get_all_drugs, PROTOCOLS, DRUGS


# Initialize FastAPI app
app = FastAPI(
    title="Chemotherapy Protocol Engine",
    description="NHS Lymphoma Chemotherapy Protocol Management System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize protocol engine
engine = ProtocolEngine(get_all_protocols())


# ============= API ENDPOINTS =============

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Chemotherapy Protocol Engine",
        "version": "1.0.0",
        "description": "NHS Lymphoma Protocol Management API",
        "endpoints": {
            "protocols": "/api/v1/protocols",
            "generate": "/api/v1/protocol/generate",
            "drugs": "/api/v1/drugs",
            "calculate_bsa": "/api/v1/calculate/bsa",
            "docs": "/docs"
        }
    }


@app.get("/api/v1/protocols", response_model=list[ProtocolSummary])
async def list_protocols(
    search: Optional[str] = Query(None, description="Search term for protocol name, code, or drug")
):
    """
    List all available protocols with optional search
    """
    protocols = engine.protocols.values()
    
    if search:
        protocols = engine.search_protocols(search)
    
    summaries = []
    for p in protocols:
        summaries.append(ProtocolSummary(
            id=p.id,
            code=p.code,
            name=p.name,
            indication=p.indication,
            drugs=[d.drug_name for d in p.drugs],
            cycle_length_days=p.cycle_length_days,
            total_cycles=p.total_cycles
        ))
    
    return summaries


@app.get("/api/v1/protocols/{protocol_code}")
async def get_protocol(protocol_code: str):
    """
    Get detailed protocol information by code
    """
    protocol = engine.get_protocol(protocol_code)
    if not protocol:
        raise HTTPException(status_code=404, detail=f"Protocol not found: {protocol_code}")
    
    return protocol.model_dump()


@app.post("/api/v1/protocol/generate", response_model=ProtocolResponse)
async def generate_protocol(request: ProtocolRequest):
    """
    Generate a personalized protocol based on patient data and drug selection.
    
    This endpoint calculates doses based on BSA, applies dose modifications
    based on organ function, and allows selective drug inclusion/exclusion.
    
    Example request:
    ```json
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
        "excluded_drugs": [],
        "include_premeds": true,
        "include_antiemetics": true,
        "include_take_home": true
    }
    ```
    """
    try:
        response = engine.generate_protocol(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating protocol: {str(e)}")


@app.get("/api/v1/drugs", response_model=list[DrugSummary])
async def list_drugs(
    category: Optional[str] = Query(None, description="Filter by drug category")
):
    """
    List all drugs in the system
    """
    drugs = get_all_drugs()
    
    # Count protocols per drug
    drug_protocol_count = {}
    for protocol in engine.protocols.values():
        for drug in protocol.drugs + protocol.pre_medications + protocol.take_home_medicines:
            drug_protocol_count[drug.drug_name] = drug_protocol_count.get(drug.drug_name, 0) + 1
    
    summaries = []
    for drug_id, drug in drugs.items():
        if category and drug.category.value != category:
            continue
        
        summaries.append(DrugSummary(
            id=drug.id,
            name=drug.name,
            category=drug.category.value,
            protocols_count=drug_protocol_count.get(drug.name, 0)
        ))
    
    return summaries


@app.get("/api/v1/drugs/{drug_id}")
async def get_drug(drug_id: str):
    """
    Get detailed drug information
    """
    drugs = get_all_drugs()
    drug = drugs.get(drug_id.lower())
    
    if not drug:
        raise HTTPException(status_code=404, detail=f"Drug not found: {drug_id}")
    
    # Find protocols containing this drug
    containing_protocols = []
    for protocol in engine.protocols.values():
        all_drugs = protocol.drugs + protocol.pre_medications + protocol.take_home_medicines
        if any(d.drug_id == drug_id or d.drug_name.lower() == drug.name.lower() for d in all_drugs):
            containing_protocols.append({
                "id": protocol.id,
                "code": protocol.code,
                "name": protocol.name
            })
    
    return {
        **drug.model_dump(),
        "containing_protocols": containing_protocols
    }


@app.get("/api/v1/protocol/{protocol_code}/drugs")
async def get_protocol_drugs(protocol_code: str):
    """
    Get all drugs in a protocol with their default doses
    """
    protocol = engine.get_protocol(protocol_code)
    if not protocol:
        raise HTTPException(status_code=404, detail=f"Protocol not found: {protocol_code}")
    
    return {
        "protocol_code": protocol.code,
        "protocol_name": protocol.name,
        "core_drugs": [d.model_dump() for d in protocol.drugs],
        "pre_medications": [d.model_dump() for d in protocol.pre_medications],
        "take_home_medicines": [d.model_dump() for d in protocol.take_home_medicines],
        "rescue_medications": [d.model_dump() for d in protocol.rescue_medications]
    }


@app.post("/api/v1/calculate/bsa")
async def calculate_bsa(
    height_cm: float = Query(..., gt=0, description="Height in cm"),
    weight_kg: float = Query(..., gt=0, description="Weight in kg"),
    method: str = Query("mosteller", description="Calculation method: mosteller or dubois")
):
    """
    Calculate Body Surface Area (BSA)
    """
    if method == "mosteller":
        bsa = calculate_bsa_mosteller(height_cm, weight_kg)
    else:
        from engine import calculate_bsa_dubois
        bsa = calculate_bsa_dubois(height_cm, weight_kg)
    
    return {
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "method": method,
        "bsa_m2": round(bsa, 2)
    }


@app.post("/api/v1/calculate/crcl")
async def calculate_crcl(
    creatinine: float = Query(..., gt=0, description="Serum creatinine in µmol/L"),
    age: int = Query(..., gt=0, description="Patient age in years"),
    weight_kg: float = Query(..., gt=0, description="Weight in kg"),
    female: bool = Query(False, description="Is patient female")
):
    """
    Calculate Creatinine Clearance using Cockcroft-Gault formula
    """
    crcl = calculate_creatinine_clearance(creatinine, age, weight_kg, female)
    
    return {
        "creatinine_umol": creatinine,
        "age": age,
        "weight_kg": weight_kg,
        "female": female,
        "creatinine_clearance_ml_min": crcl
    }


@app.get("/api/v1/dose-modifications/{protocol_code}")
async def get_dose_modifications(protocol_code: str):
    """
    Get dose modification rules for a protocol
    """
    protocol = engine.get_protocol(protocol_code)
    if not protocol:
        raise HTTPException(status_code=404, detail=f"Protocol not found: {protocol_code}")
    
    return {
        "protocol_code": protocol.code,
        "modifications": [m.model_dump() for m in protocol.dose_modifications]
    }


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "protocols_loaded": len(engine.protocols),
        "drugs_loaded": len(get_all_drugs())
    }


# ============= MAIN =============

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
