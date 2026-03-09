"""
Chemotherapy Protocol Engine - Enhanced FastAPI Application
With Gemini-powered PDF parsing and protocol management
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from models import (
    ProtocolRequest, ProtocolResponse, ProtocolSummary, DrugSummary,
    PatientData, Protocol, CustomRegimenRequest
)
from engine import ProtocolEngine, calculate_bsa_mosteller, calculate_creatinine_clearance
from protocol_data import get_all_protocols, get_all_drugs, PROTOCOLS, DRUGS
from gemini_parser import GeminiProtocolParser, ProtocolIngestionService
from adapters import PatientStateAdapter
from json_protocol_loader import load_all_json_protocols

# Load environment variables
load_dotenv()

# ============= CONFIGURATION =============

class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    UPLOAD_DIR: str = "data/uploads"
    PROTOCOLS_DIR: str = "data/protocols"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB

settings = Settings()

# Create directories
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.PROTOCOLS_DIR).mkdir(parents=True, exist_ok=True)


# ============= APP INITIALIZATION =============

app = FastAPI(
    title="SOPHIA API - System for Orchestrating Protocol-guided Healthcare Inference & Analysis",
    description="""
    ## SOPHIA by Jivana AI
    ### System for Orchestrating Protocol-guided Healthcare Inference & Analysis
    
    Intelligent chemotherapy protocol management powered by AI.
    
    ### Features:
    - **Protocol Generation**: Generate personalized protocols based on patient data
    - **Dose Calculations**: BSA-based and weight-based dosing
    - **Dose Modifications**: Automatic adjustments for organ function
    - **Drug Selection**: Flexible drug inclusion/exclusion
    - **PDF Ingestion**: AI-powered protocol extraction from PDFs
    - **Multi-Disease Support**: Expandable to any cancer type
    
    ### API Sections:
    - `/api/v1/protocols` - Protocol browsing and generation
    - `/api/v1/drugs` - Drug information
    - `/api/v1/calculate` - BSA and CrCl calculators
    - `/api/v1/admin` - Protocol management and ingestion
    
    ---
    **Powered by Jivana AI** - Advanced Healthcare Intelligence
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
parser = GeminiProtocolParser(settings.GEMINI_API_KEY)
ingestion_service = ProtocolIngestionService(parser, settings.PROTOCOLS_DIR)

# Load JSON protocols once at startup (581 NHS UHS protocols)
_json_protocols: dict[str, Protocol] = load_all_json_protocols()


# Load protocols — NHS UHS JSON protocols only
def get_combined_protocols() -> dict[str, Protocol]:
    """Get all protocols from NHS UHS JSON files only"""
    return dict(_json_protocols)

# Initialize engine with combined protocols
engine = ProtocolEngine(get_combined_protocols())

def refresh_engine():
    """Refresh the engine with updated protocols"""
    global engine
    engine = ProtocolEngine(get_combined_protocols())


# ============= REQUEST/RESPONSE MODELS =============

class IngestionRequest(BaseModel):
    disease_category: str = "lymphoma"
    force_reparse: bool = False

class IngestionResponse(BaseModel):
    success: bool
    protocol_id: Optional[str] = None
    protocol_code: Optional[str] = None
    protocol_name: Optional[str] = None
    drugs_count: int = 0
    message: str

class BatchIngestionResponse(BaseModel):
    total_files: int
    successful: int
    failed: int
    protocols: list[IngestionResponse]

class CategoryStats(BaseModel):
    category: str
    protocol_count: int
    protocols: list[str]

class SystemStats(BaseModel):
    total_protocols: int
    total_drugs: int
    categories: list[CategoryStats]
    hardcoded_protocols: int
    ingested_protocols: int
    last_updated: Optional[str]
    gemini_configured: bool


# ============= CORE API ENDPOINTS =============

@app.get("/")
async def root():
    """API root with system information"""
    stats = ingestion_service.get_stats()
    return {
        "name": "SOPHIA API",
        "full_name": "System for Orchestrating Protocol-guided Healthcare Inference & Analysis",
        "version": "2.0.0",
        "company": "Jivana AI",
        "description": "Intelligent chemotherapy protocol management powered by AI",
        "total_protocols": len(get_combined_protocols()),
        "gemini_enabled": bool(settings.GEMINI_API_KEY),
        "endpoints": {
            "docs": "/docs",
            "protocols": "/api/v1/protocols",
            "generate": "/api/v1/protocol/generate",
            "drugs": "/api/v1/drugs",
            "admin": "/api/v1/admin",
            "upload": "/api/v1/admin/upload"
        }
    }


@app.get("/api/v1/protocols", response_model=list[ProtocolSummary])
async def list_protocols(
    search: Optional[str] = Query(None, description="Search term"),
    category: Optional[str] = Query(None, description="Filter by disease category")
):
    """List all available protocols with optional search and filtering"""
    
    # Refresh to get latest protocols
    refresh_engine()
    
    protocols = list(engine.protocols.values())
    
    # Filter by category if specified
    if category:
        category_lower = category.lower()
        protocols = [p for p in protocols
                     if category_lower in (p.source_file or '').lower()
                     or category_lower in p.id.lower()]
    
    # Search filter
    if search:
        search_lower = search.lower()
        protocols = [
            p for p in protocols
            if (search_lower in p.code.lower() or
                search_lower in p.name.lower() or
                search_lower in p.indication.lower() or
                any(search_lower in d.drug_name.lower() for d in p.drugs))
        ]
    
    return [
        ProtocolSummary(
            id=p.id,
            code=p.code,
            name=p.name,
            indication=p.indication,
            drugs=[d.drug_name for d in p.drugs],
            cycle_length_days=p.cycle_length_days,
            total_cycles=p.total_cycles
        )
        for p in protocols
    ]


@app.get("/api/v1/protocols/{protocol_code}")
async def get_protocol(protocol_code: str):
    """Get detailed protocol information by code"""
    refresh_engine()
    protocol = engine.get_protocol(protocol_code)
    if not protocol:
        raise HTTPException(status_code=404, detail=f"Protocol not found: {protocol_code}")
    return protocol.model_dump()


@app.post("/api/v1/protocol/generate", response_model=ProtocolResponse)
async def generate_protocol(request: ProtocolRequest):
    """
    Generate a personalized protocol based on patient data and drug selection.
    
    This is the main endpoint for generating treatment protocols. It:
    - Calculates doses based on BSA
    - Applies dose modifications for organ function
    - Allows selective drug inclusion/exclusion
    - Handles cycle-specific variations
    
    Example:
    ```json
    {
        "protocol_code": "RCHOP21",
        "patient": {
            "weight_kg": 70,
            "height_cm": 175,
            "neutrophils": 2.5,
            "platelets": 150,
            "bilirubin": 15
        },
        "cycle_number": 1,
        "excluded_drugs": ["rituximab"],
        "include_premeds": true,
        "include_take_home": true
    }
    ```
    """
    refresh_engine()
    try:
        response = engine.generate_protocol(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating protocol: {str(e)}")


@app.post("/api/v1/protocol/generate-from-patient-json", response_model=ProtocolResponse)
async def generate_from_patient_json(
    protocol_code: str,
    patient_json: dict,
    target_cycle: Optional[int] = None,
):
    """
    Generate a protocol from a raw patient JSON (e.g. from mobile app or WhatsApp form).
    The adapter handles unit conversion, post-cycle lab selection, and virology fields.

    Pass the raw patient record as the request body and the protocol code as a query param.
    """
    refresh_engine()
    try:
        patient = PatientStateAdapter.adapt(patient_json, target_cycle=target_cycle)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Patient data error: {e}")

    request = ProtocolRequest(
        protocol_code=protocol_code,
        patient=patient,
        cycle_number=target_cycle or 1,
    )
    try:
        return engine.generate_protocol(request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/protocol/generate-custom", response_model=ProtocolResponse)
async def generate_custom_regimen(request: CustomRegimenRequest):
    """
    Generate a protocol from a custom drug list built in the Flexible Protocol Builder.

    This endpoint accepts any combination of drugs the clinician has assembled — e.g.:
    - Azacitidine alone
    - Venetoclax alone
    - Aza + Ven
    - Aza + 7+3 (custom combination)

    The same BSA calculations, vincristine cap, allergy checks and delay logic apply,
    but no protocol-level dose modification rules are enforced.

    A pharmacist verification gate is always required for the output.
    """
    try:
        response = engine.generate_custom_regimen(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating custom regimen: {str(e)}")


@app.get("/api/v1/protocol/{protocol_code}/drugs")
async def get_protocol_drugs(protocol_code: str):
    """Get all drugs in a protocol with their default doses"""
    refresh_engine()
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


# ============= DRUG ENDPOINTS =============

@app.get("/api/v1/drugs", response_model=list[DrugSummary])
async def list_drugs(category: Optional[str] = Query(None, description="Filter by drug category")):
    """List all drugs in the system"""
    refresh_engine()
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
    """Get detailed drug information"""
    refresh_engine()
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


# ============= CALCULATION ENDPOINTS =============

@app.post("/api/v1/calculate/bsa")
async def calculate_bsa(
    height_cm: float = Query(..., gt=0),
    weight_kg: float = Query(..., gt=0),
    method: str = Query("mosteller", description="mosteller or dubois")
):
    """Calculate Body Surface Area (BSA)"""
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
    age: int = Query(..., gt=0),
    weight_kg: float = Query(..., gt=0),
    female: bool = Query(False)
):
    """Calculate Creatinine Clearance using Cockcroft-Gault formula"""
    crcl = calculate_creatinine_clearance(creatinine, age, weight_kg, female)
    return {
        "creatinine_umol": creatinine,
        "age": age,
        "weight_kg": weight_kg,
        "female": female,
        "creatinine_clearance_ml_min": crcl
    }


# ============= ADMIN / INGESTION ENDPOINTS =============

@app.get("/api/v1/admin/stats", response_model=SystemStats)
async def get_system_stats():
    """Get system statistics"""
    refresh_engine()
    ingested_stats = ingestion_service.get_stats()
    hardcoded_count = len(PROTOCOLS)
    
    categories = []
    for cat, protocol_ids in ingested_stats.get("categories", {}).items():
        categories.append(CategoryStats(
            category=cat,
            protocol_count=len(protocol_ids),
            protocols=protocol_ids
        ))
    
    return SystemStats(
        total_protocols=len(engine.protocols),
        total_drugs=len(get_all_drugs()),
        categories=categories,
        hardcoded_protocols=hardcoded_count,
        ingested_protocols=ingested_stats.get("total_protocols", 0),
        last_updated=ingested_stats.get("last_updated"),
        gemini_configured=bool(settings.GEMINI_API_KEY)
    )


@app.get("/api/v1/admin/categories")
async def get_categories():
    """Get all disease categories"""
    categories = ingestion_service.get_categories()
    
    # Add default lymphoma if not present
    if "lymphoma" not in categories:
        categories.append("lymphoma")
    
    return {
        "categories": sorted(categories),
        "default": "lymphoma"
    }


@app.post("/api/v1/admin/upload", response_model=IngestionResponse)
async def upload_protocol(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Protocol PDF file"),
    disease_category: str = Form("lymphoma", description="Disease category"),
    force_reparse: bool = Form(False, description="Force re-parsing even if cached")
):
    """
    Upload a new protocol PDF for AI-powered extraction.
    
    The PDF will be parsed by Gemini to extract:
    - Protocol name, code, indication
    - All drugs with doses, routes, schedules
    - Pre-medications and supportive care
    - Dose modification rules
    - Monitoring requirements
    
    Supported categories: lymphoma, breast_cancer, lung_cancer, colorectal, etc.
    """
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Gemini API key not configured. Set GEMINI_API_KEY environment variable."
        )
    
    # Validate file
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Save file
    file_path = Path(settings.UPLOAD_DIR) / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    
    try:
        with open(file_path, 'wb') as f:
            content = await file.read()
            if len(content) > settings.MAX_UPLOAD_SIZE:
                raise HTTPException(status_code=413, detail="File too large (max 50MB)")
            f.write(content)
        
        # Parse with Gemini
        protocol = await ingestion_service.ingest_pdf(
            str(file_path),
            disease_category,
            force_reparse
        )
        
        # Refresh engine
        refresh_engine()
        
        return IngestionResponse(
            success=True,
            protocol_id=protocol.id,
            protocol_code=protocol.code,
            protocol_name=protocol.name,
            drugs_count=len(protocol.drugs),
            message=f"Successfully ingested protocol: {protocol.code}"
        )
        
    except Exception as e:
        # Clean up on failure
        if file_path.exists():
            file_path.unlink()
        
        return IngestionResponse(
            success=False,
            message=f"Failed to ingest protocol: {str(e)}"
        )


@app.post("/api/v1/admin/ingest-directory", response_model=BatchIngestionResponse)
async def ingest_directory(
    directory_path: str = Query(..., description="Path to directory containing PDFs"),
    disease_category: str = Query("lymphoma")
):
    """
    Batch ingest all PDF files from a directory.
    
    Useful for initial setup when you have many protocols.
    """
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Gemini API key not configured"
        )
    
    dir_path = Path(directory_path)
    if not dir_path.exists():
        raise HTTPException(status_code=404, detail=f"Directory not found: {directory_path}")
    
    pdf_files = list(dir_path.glob("*.pdf"))
    if not pdf_files:
        raise HTTPException(status_code=404, detail="No PDF files found in directory")
    
    results = []
    successful = 0
    failed = 0
    
    for pdf_file in pdf_files:
        try:
            protocol = await ingestion_service.ingest_pdf(
                str(pdf_file),
                disease_category
            )
            results.append(IngestionResponse(
                success=True,
                protocol_id=protocol.id,
                protocol_code=protocol.code,
                protocol_name=protocol.name,
                drugs_count=len(protocol.drugs),
                message=f"Successfully ingested: {protocol.code}"
            ))
            successful += 1
        except Exception as e:
            results.append(IngestionResponse(
                success=False,
                message=f"Failed to ingest {pdf_file.name}: {str(e)}"
            ))
            failed += 1
    
    # Refresh engine
    refresh_engine()
    
    return BatchIngestionResponse(
        total_files=len(pdf_files),
        successful=successful,
        failed=failed,
        protocols=results
    )


@app.delete("/api/v1/admin/protocol/{protocol_id}")
async def delete_protocol(protocol_id: str):
    """Delete an ingested protocol (cannot delete hardcoded protocols)"""
    if protocol_id in PROTOCOLS:
        raise HTTPException(
            status_code=403,
            detail="Cannot delete hardcoded protocols. Only ingested protocols can be deleted."
        )
    
    protocol_file = Path(settings.PROTOCOLS_DIR) / f"{protocol_id}.json"
    if not protocol_file.exists():
        raise HTTPException(status_code=404, detail=f"Protocol not found: {protocol_id}")
    
    protocol_file.unlink()
    refresh_engine()
    
    return {"message": f"Protocol {protocol_id} deleted successfully"}


@app.post("/api/v1/admin/clear-cache")
async def clear_parser_cache():
    """Clear the Gemini parsing cache (forces re-parsing on next upload)"""
    parser.clear_cache()
    return {"message": "Parser cache cleared"}


# ============= HEALTH CHECK =============

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "protocols_loaded": len(get_combined_protocols()),
        "drugs_loaded": len(get_all_drugs()),
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "timestamp": datetime.now().isoformat()
    }


# ============= MAIN =============

if __name__ == "__main__":
    uvicorn.run(
        "main_enhanced:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
