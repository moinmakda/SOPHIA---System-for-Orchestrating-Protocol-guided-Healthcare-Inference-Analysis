"""
Gemini-Powered Protocol Parser
Automatically extracts structured protocol data from PDF documents
"""

import os
import json
import base64
import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime
import google.generativeai as genai
from pydantic import BaseModel

from models import (
    Protocol, ProtocolDrug, DoseModificationRule, Toxicity,
    DoseUnit, RouteOfAdministration, DrugCategory
)


# Gemini extraction prompt template
EXTRACTION_PROMPT = """You are an expert clinical pharmacist and oncologist. Analyze this NHS chemotherapy protocol PDF and extract ALL information into a structured JSON format.

CRITICAL: Be extremely precise with drug doses, units, and administration details. Lives depend on accuracy.

Extract the following structure:

```json
{
  "protocol_id": "unique_lowercase_id",
  "protocol_code": "SHORT_CODE (e.g., RCHOP21, BR, ABVD)",
  "protocol_name": "Full Protocol Name",
  "full_name": "Complete descriptive name with all drugs",
  "indication": "Cancer type and stage/condition this treats",
  "cycle_length_days": 21,
  "total_cycles": 6,
  "version": "1.0",
  
  "drugs": [
    {
      "drug_id": "lowercase_drug_name",
      "drug_name": "Proper Drug Name",
      "dose": 375,
      "dose_unit": "mg/m²",
      "route": "IV infusion",
      "days": [1],
      "duration_minutes": 60,
      "diluent": "Sodium chloride 0.9%",
      "diluent_volume_ml": 500,
      "administration_order": 1,
      "max_dose": null,
      "max_dose_unit": null,
      "special_instructions": "Any specific instructions"
    }
  ],
  
  "pre_medications": [
    {
      "drug_id": "drug_name",
      "drug_name": "Drug Name",
      "dose": 10,
      "dose_unit": "mg",
      "route": "IV bolus",
      "days": [1],
      "timing": "30 minutes before chemotherapy",
      "special_instructions": null
    }
  ],
  
  "take_home_medicines": [
    {
      "drug_id": "drug_name",
      "drug_name": "Drug Name",
      "dose": 100,
      "dose_unit": "mg",
      "route": "Oral",
      "days": [2, 3, 4, 5],
      "frequency": "Once daily",
      "special_instructions": null,
      "prn": false
    }
  ],
  
  "rescue_medications": [
    {
      "drug_id": "drug_name",
      "drug_name": "Drug Name",
      "dose": 100,
      "dose_unit": "mg",
      "route": "IV bolus",
      "days": [1],
      "prn": true,
      "special_instructions": "For infusion reactions"
    }
  ],
  
  "dose_modifications": [
    {
      "parameter": "neutrophils",
      "condition": "< 1.0",
      "affected_drugs": ["cyclophosphamide", "doxorubicin"],
      "modification": "delay",
      "modification_percent": null,
      "description": "Delay until neutrophils ≥ 1.0 x10⁹/L"
    },
    {
      "parameter": "bilirubin",
      "condition": "30-50",
      "affected_drugs": ["doxorubicin"],
      "modification": "reduce_50",
      "modification_percent": 50,
      "description": "Bilirubin 30-50 µmol/L: reduce to 50%"
    }
  ],
  
  "toxicities": [
    {
      "drug_id": "drug_name",
      "adverse_effects": ["Effect 1", "Effect 2", "Effect 3"]
    }
  ],
  
  "monitoring": [
    "FBC, LFTs and U&Es prior to day one",
    "Check hepatitis B status before rituximab",
    "Baseline LVEF for patients with cardiac history"
  ],
  
  "warnings": [
    "CRITICAL warnings go here",
    "Special precautions"
  ],
  
  "cycle_variations": [
    {
      "cycles": [1],
      "description": "Cycle 1 specific instructions",
      "drugs_modified": []
    }
  ]
}
```

IMPORTANT RULES:
1. dose_unit must be one of: "mg", "mg/m²", "mg/kg", "g", "g/m²", "units", "units/m²", "mcg", "mcg/m²", "ml"
2. route must be one of: "IV bolus", "IV infusion", "Oral", "Subcutaneous", "IM", "Nebulised", "Topical"
3. For dose modifications, parameter must be: "neutrophils", "platelets", "bilirubin", "creatinine_clearance", "ast", "alt", "hemoglobin"
4. Extract ALL drugs mentioned including antiemetics, hydration, etc.
5. Be precise with day numbers - extract exactly as written
6. If information is not clearly stated, use null
7. Include cycle-specific variations if the protocol differs between cycles

Return ONLY valid JSON, no markdown code blocks or explanations."""


class GeminiProtocolParser:
    """
    Uses Google Gemini to parse chemotherapy protocol PDFs into structured data
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None
        
        self.parsed_protocols_dir = Path("data/parsed_protocols")
        self.parsed_protocols_dir.mkdir(parents=True, exist_ok=True)
        
        self.upload_dir = Path("data/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_hash(self, file_path: str) -> str:
        """Generate hash for file to detect duplicates"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def _read_pdf_as_base64(self, file_path: str) -> str:
        """Read PDF file and encode as base64"""
        with open(file_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    async def parse_pdf(self, file_path: str, disease_category: str = "lymphoma") -> dict:
        """
        Parse a protocol PDF using Gemini
        
        Args:
            file_path: Path to the PDF file
            disease_category: Category for organizing protocols (e.g., 'lymphoma', 'breast', 'lung')
        
        Returns:
            Parsed protocol data as dictionary
        """
        if not self.model:
            raise ValueError("Gemini API key not configured")
        
        # Check if already parsed
        file_hash = self._get_file_hash(file_path)
        cache_file = self.parsed_protocols_dir / f"{file_hash}.json"
        
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        
        # Read PDF
        pdf_data = self._read_pdf_as_base64(file_path)
        
        # Call Gemini
        response = self.model.generate_content([
            EXTRACTION_PROMPT,
            {"mime_type": "application/pdf", "data": pdf_data}
        ])
        
        # Parse response
        try:
            # Clean response - remove markdown code blocks if present
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()
            
            protocol_data = json.loads(text)
            
            # Add metadata
            protocol_data["_metadata"] = {
                "source_file": os.path.basename(file_path),
                "file_hash": file_hash,
                "disease_category": disease_category,
                "parsed_at": datetime.now().isoformat(),
                "parser_version": "1.0"
            }
            
            # Cache the result
            with open(cache_file, 'w') as f:
                json.dump(protocol_data, f, indent=2)
            
            return protocol_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Gemini response as JSON: {e}\nResponse: {response.text[:500]}")
    
    def parse_pdf_sync(self, file_path: str, disease_category: str = "lymphoma") -> dict:
        """Synchronous version of parse_pdf"""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self.parse_pdf(file_path, disease_category)
        )
    
    def convert_to_protocol_model(self, data: dict) -> Protocol:
        """
        Convert parsed JSON data to Protocol model
        """
        # Map dose units
        dose_unit_map = {
            "mg": DoseUnit.MG,
            "mg/m²": DoseUnit.MG_M2,
            "mg/m2": DoseUnit.MG_M2,
            "mg/kg": DoseUnit.MG_KG,
            "g": DoseUnit.G,
            "g/m²": DoseUnit.G_M2,
            "g/m2": DoseUnit.G_M2,
            "units": DoseUnit.UNITS,
            "units/m²": DoseUnit.UNITS_M2,
            "units/m2": DoseUnit.UNITS_M2,
            "mcg": DoseUnit.MCG,
            "mcg/m²": DoseUnit.MCG_M2,
            "mcg/m2": DoseUnit.MCG_M2,
            "ml": DoseUnit.ML,
        }
        
        # Map routes
        route_map = {
            "iv bolus": RouteOfAdministration.IV_BOLUS,
            "iv infusion": RouteOfAdministration.IV_INFUSION,
            "intravenous bolus": RouteOfAdministration.IV_BOLUS,
            "intravenous infusion": RouteOfAdministration.IV_INFUSION,
            "oral": RouteOfAdministration.ORAL,
            "po": RouteOfAdministration.ORAL,
            "subcutaneous": RouteOfAdministration.SC,
            "sc": RouteOfAdministration.SC,
            "im": RouteOfAdministration.IM,
            "intramuscular": RouteOfAdministration.IM,
            "nebulised": RouteOfAdministration.NEBULISED,
            "nebulized": RouteOfAdministration.NEBULISED,
            "topical": RouteOfAdministration.TOPICAL,
        }
        
        def parse_drug(d: dict, order: int = 0) -> ProtocolDrug:
            """Parse drug data with robust error handling"""
            # Handle dose unit
            dose_unit_str = d.get("dose_unit", "mg")
            if dose_unit_str:
                dose_unit = dose_unit_map.get(str(dose_unit_str).lower(), DoseUnit.MG)
            else:
                dose_unit = DoseUnit.MG
            
            # Handle route
            route_str = d.get("route", "IV infusion")
            if route_str:
                route = route_map.get(str(route_str).lower(), RouteOfAdministration.IV_INFUSION)
            else:
                route = RouteOfAdministration.IV_INFUSION
            
            # Handle days - ensure it's always a list
            days = d.get("days")
            if days is None or not isinstance(days, list):
                days = [1]
            elif not days:  # Empty list
                days = [1]
            
            # Handle dose - ensure it's a valid number
            try:
                dose = float(d.get("dose", 0))
            except (ValueError, TypeError):
                dose = 0.0
            
            # Handle drug_id
            drug_id = d.get("drug_id")
            if not drug_id:
                drug_name = d.get("drug_name", "unknown")
                drug_id = str(drug_name).lower().replace(" ", "_")
            
            # Handle boolean fields
            prn = d.get("prn")
            if prn is None:
                prn = False
            
            is_core_drug = d.get("is_core_drug")
            if is_core_drug is None:
                is_core_drug = True
            
            return ProtocolDrug(
                drug_id=drug_id,
                drug_name=d.get("drug_name") or "Unknown",
                dose=dose,
                dose_unit=dose_unit,
                route=route,
                days=days,
                duration_minutes=d.get("duration_minutes"),
                diluent=d.get("diluent"),
                diluent_volume_ml=d.get("diluent_volume_ml"),
                administration_order=d.get("administration_order", order),
                max_dose=d.get("max_dose"),
                max_dose_unit=d.get("max_dose_unit"),
                timing=d.get("timing"),
                frequency=d.get("frequency"),
                special_instructions=d.get("special_instructions"),
                prn=prn,
                is_core_drug=is_core_drug
            )
        
        def parse_modification(m: dict) -> DoseModificationRule:
            """Parse dose modification with error handling"""
            # Ensure affected_drugs is a list
            affected_drugs = m.get("affected_drugs")
            if not isinstance(affected_drugs, list):
                affected_drugs = []
            
            return DoseModificationRule(
                parameter=m.get("parameter") or "",
                condition=m.get("condition") or "",
                affected_drugs=affected_drugs,
                modification=m.get("modification") or "",
                modification_percent=m.get("modification_percent"),
                description=m.get("description") or ""
            )
        
        def parse_toxicity(t: dict) -> Toxicity:
            """Parse toxicity with error handling"""
            # Ensure adverse_effects is a list
            adverse_effects = t.get("adverse_effects")
            if not isinstance(adverse_effects, list):
                adverse_effects = []
            
            return Toxicity(
                drug_id=t.get("drug_id") or "",
                adverse_effects=adverse_effects
            )
        
        # Build protocol with safe defaults
        # Ensure lists are actually lists
        drugs = data.get("drugs")
        if not isinstance(drugs, list):
            drugs = []
        
        pre_medications = data.get("pre_medications")
        if not isinstance(pre_medications, list):
            pre_medications = []
        
        take_home_medicines = data.get("take_home_medicines")
        if not isinstance(take_home_medicines, list):
            take_home_medicines = []
        
        rescue_medications = data.get("rescue_medications")
        if not isinstance(rescue_medications, list):
            rescue_medications = []
        
        dose_modifications = data.get("dose_modifications")
        if not isinstance(dose_modifications, list):
            dose_modifications = []
        
        toxicities = data.get("toxicities")
        if not isinstance(toxicities, list):
            toxicities = []
        
        monitoring = data.get("monitoring")
        if not isinstance(monitoring, list):
            monitoring = []
        
        warnings = data.get("warnings")
        if not isinstance(warnings, list):
            warnings = []
        
        # Ensure numeric fields are valid
        try:
            cycle_length_days = int(data.get("cycle_length_days", 21))
        except (ValueError, TypeError):
            cycle_length_days = 21
        
        try:
            total_cycles = int(data.get("total_cycles", 6))
        except (ValueError, TypeError):
            total_cycles = 6
        
        # Build protocol
        return Protocol(
            id=data.get("protocol_id") or "unknown",
            name=data.get("protocol_name") or "Unknown Protocol",
            code=data.get("protocol_code") or "UNK",
            full_name=data.get("full_name") or data.get("protocol_name") or "",
            indication=data.get("indication") or "",
            cycle_length_days=cycle_length_days,
            total_cycles=total_cycles,
            version=data.get("version") or "1.0",
            drugs=[parse_drug(d, i) for i, d in enumerate(drugs)],
            pre_medications=[parse_drug(d, i) for i, d in enumerate(pre_medications)],
            take_home_medicines=[parse_drug(d, i) for i, d in enumerate(take_home_medicines)],
            rescue_medications=[parse_drug(d, i) for i, d in enumerate(rescue_medications)],
            dose_modifications=[parse_modification(m) for m in dose_modifications],
            toxicities=[parse_toxicity(t) for t in toxicities],
            monitoring=monitoring,
            warnings=warnings,
            source_file=data.get("_metadata", {}).get("source_file")
        )
    
    def get_all_cached_protocols(self) -> list[dict]:
        """Get all previously parsed protocols from cache"""
        protocols = []
        for cache_file in self.parsed_protocols_dir.glob("*.json"):
            with open(cache_file, 'r') as f:
                protocols.append(json.load(f))
        return protocols
    
    def clear_cache(self):
        """Clear the parsed protocols cache"""
        for f in self.parsed_protocols_dir.glob("*.json"):
            f.unlink()


class ProtocolIngestionService:
    """
    Service for ingesting and managing protocols from various sources
    """
    
    def __init__(self, parser: GeminiProtocolParser, storage_path: str = "data/protocols"):
        self.parser = parser
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.index_file = self.storage_path / "protocol_index.json"
        self.index = self._load_index()
    
    def _load_index(self) -> dict:
        """Load the protocol index"""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                return json.load(f)
        return {
            "protocols": {},
            "categories": {},
            "drugs": {},
            "last_updated": None
        }
    
    def _save_index(self):
        """Save the protocol index"""
        self.index["last_updated"] = datetime.now().isoformat()
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    async def ingest_pdf(
        self,
        file_path: str,
        disease_category: str = "lymphoma",
        force_reparse: bool = False
    ) -> Protocol:
        """
        Ingest a single protocol PDF
        
        Args:
            file_path: Path to PDF
            disease_category: Category (e.g., 'lymphoma', 'breast_cancer')
            force_reparse: If True, ignore cache and reparse
        
        Returns:
            Parsed Protocol model
        """
        # Parse with Gemini
        parsed_data = await self.parser.parse_pdf(file_path, disease_category)
        
        # Convert to Protocol model
        protocol = self.parser.convert_to_protocol_model(parsed_data)
        
        # Save to storage
        protocol_file = self.storage_path / f"{protocol.id}.json"
        with open(protocol_file, 'w') as f:
            json.dump(protocol.model_dump(), f, indent=2)
        
        # Update index
        self.index["protocols"][protocol.id] = {
            "code": protocol.code,
            "name": protocol.name,
            "category": disease_category,
            "file": str(protocol_file),
            "drugs": [d.drug_name for d in protocol.drugs]
        }
        
        # Update category index
        if disease_category not in self.index["categories"]:
            self.index["categories"][disease_category] = []
        if protocol.id not in self.index["categories"][disease_category]:
            self.index["categories"][disease_category].append(protocol.id)
        
        # Update drug index
        for drug in protocol.drugs:
            if drug.drug_name not in self.index["drugs"]:
                self.index["drugs"][drug.drug_name] = []
            if protocol.id not in self.index["drugs"][drug.drug_name]:
                self.index["drugs"][drug.drug_name].append(protocol.id)
        
        self._save_index()
        
        return protocol
    
    async def ingest_directory(
        self,
        directory: str,
        disease_category: str = "lymphoma"
    ) -> list[Protocol]:
        """
        Ingest all PDFs from a directory
        """
        protocols = []
        dir_path = Path(directory)
        
        for pdf_file in dir_path.glob("*.pdf"):
            try:
                protocol = await self.ingest_pdf(str(pdf_file), disease_category)
                protocols.append(protocol)
                print(f"✓ Ingested: {protocol.code} - {protocol.name}")
            except Exception as e:
                print(f"✗ Failed to ingest {pdf_file.name}: {e}")
        
        return protocols
    
    def get_protocol(self, protocol_id: str) -> Optional[Protocol]:
        """Get a protocol by ID"""
        if protocol_id not in self.index["protocols"]:
            return None
        
        protocol_file = Path(self.index["protocols"][protocol_id]["file"])
        if not protocol_file.exists():
            return None
        
        with open(protocol_file, 'r') as f:
            data = json.load(f)
        
        return Protocol(**data)
    
    def get_all_protocols(self) -> dict[str, Protocol]:
        """Get all stored protocols"""
        protocols = {}
        for protocol_id in self.index["protocols"]:
            protocol = self.get_protocol(protocol_id)
            if protocol:
                protocols[protocol_id] = protocol
        return protocols
    
    def get_protocols_by_category(self, category: str) -> list[Protocol]:
        """Get all protocols in a category"""
        if category not in self.index["categories"]:
            return []
        
        return [
            self.get_protocol(pid)
            for pid in self.index["categories"][category]
            if self.get_protocol(pid)
        ]
    
    def get_protocols_by_drug(self, drug_name: str) -> list[Protocol]:
        """Get all protocols containing a specific drug"""
        if drug_name not in self.index["drugs"]:
            return []
        
        return [
            self.get_protocol(pid)
            for pid in self.index["drugs"][drug_name]
            if self.get_protocol(pid)
        ]
    
    def search_protocols(self, query: str) -> list[Protocol]:
        """Search protocols by name, code, drug, or indication"""
        query_lower = query.lower()
        results = []
        
        for protocol_id, info in self.index["protocols"].items():
            if (query_lower in info["code"].lower() or
                query_lower in info["name"].lower() or
                any(query_lower in d.lower() for d in info.get("drugs", []))):
                protocol = self.get_protocol(protocol_id)
                if protocol:
                    results.append(protocol)
        
        return results
    
    def get_categories(self) -> list[str]:
        """Get all disease categories"""
        return list(self.index["categories"].keys())
    
    def get_all_drugs(self) -> list[str]:
        """Get all unique drugs across all protocols"""
        return list(self.index["drugs"].keys())
    
    def get_stats(self) -> dict:
        """Get statistics about the protocol database"""
        return {
            "total_protocols": len(self.index["protocols"]),
            "categories": self.index["categories"],  # Return the full dict with protocol IDs
            "unique_drugs": len(self.index["drugs"]),
            "last_updated": self.index["last_updated"]
        }
