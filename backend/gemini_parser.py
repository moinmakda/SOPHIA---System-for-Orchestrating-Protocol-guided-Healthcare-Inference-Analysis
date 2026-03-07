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
    DoseUnit, RouteOfAdministration, DrugCategory,
    HematologicalToxicityRule, NonHematologicalToxicityRule,
    MetabolicMonitoringRule, AgeBasedModification, CumulativeToxicityTracking,
    ReducedLimitCondition, TreatmentDelayCriteria, BaselineRequirement,
    PreCycleLab, PostCycleMonitoring
)


# Gemini extraction prompt template - COMPREHENSIVE VERSION
# This prompt extracts ALL automation-relevant data for nurse/doctor decision support
EXTRACTION_PROMPT = """You are an expert clinical pharmacist and oncologist. Analyze this NHS chemotherapy protocol PDF and extract ALL information into a structured JSON format.

CRITICAL: Be extremely precise with drug doses, units, and administration details. Lives depend on accuracy.
Your goal is to extract EVERYTHING needed for automated dose calculation and safety checks, minimizing manual work for nurses and doctors.

Extract the following COMPREHENSIVE structure:

```json
{
  "protocol_id": "unique_lowercase_id",
  "protocol_code": "SHORT_CODE (e.g., RCHOP21, BR, ABVD, GILTERITINIB)",
  "protocol_name": "Full Protocol Name",
  "full_name": "Complete descriptive name with all drugs",
  "indication": "Cancer type and stage/condition this treats",
  "cycle_length_days": 21,
  "total_cycles": 6,
  "version": "1.0",
  "treatment_intent": "curative|palliative|maintenance|consolidation",
  
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
      "max_dose": 2.0,
      "max_dose_unit": "mg",
      "max_dose_reason": "Neurotoxicity risk - cap applies regardless of BSA",
      "frequency": null,
      "special_instructions": "Any specific instructions",
      "age_based_cap": {
        "age_threshold": 70,
        "capped_dose": 1.0,
        "capped_dose_unit": "mg",
        "reason": "Elderly patients - cap vincristine at 1mg"
      },
      "cumulative_limit": {
        "max_lifetime_dose": 450,
        "dose_unit": "mg/m²",
        "organ_at_risk": "heart",
        "monitoring_required": "ECHO/MUGA",
        "reduced_limit_conditions": [
          {"condition": "prior cardiac disease", "limit": 400},
          {"condition": "age > 70", "limit": 400},
          {"condition": "prior mediastinal radiation", "limit": 350}
        ]
      },
      "infusion_rate_modifications": [
        {
          "condition": "first infusion",
          "initial_rate": "50 mg/hour",
          "escalation": "increase by 50 mg/hour every 30 min to max 400 mg/hour"
        }
      ]
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
      "timing_minutes": 30,
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
      "duration_days": 5,
      "special_instructions": null,
      "prn": false,
      "cycle_specific": null
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
      "indication": "For infusion reactions",
      "special_instructions": null
    }
  ],
  
  "dose_modifications": [
    {
      "rule_id": "unique_rule_id",
      "parameter": "gfr",
      "parameter_unit": "ml/min",
      "condition": "< 10",
      "condition_type": "less_than",
      "threshold_value": 10,
      "threshold_low": null,
      "threshold_high": null,
      "affected_drugs": ["cyclophosphamide"],
      "modification_type": "omit",
      "modification_percent": 0,
      "description": "Omit cyclophosphamide if GFR < 10 ml/min",
      "action_text": "Cyclophosphamide omitted because GFR < 10",
      "priority": 1
    },
    {
      "rule_id": "gfr_10_29",
      "parameter": "gfr",
      "parameter_unit": "ml/min",
      "condition": "10-29",
      "condition_type": "range",
      "threshold_value": null,
      "threshold_low": 10,
      "threshold_high": 29,
      "affected_drugs": ["cyclophosphamide"],
      "modification_type": "reduce",
      "modification_percent": 75,
      "description": "Reduce cyclophosphamide by 25% if GFR 10-29",
      "action_text": "Cyclophosphamide reduced by 25% because GFR is between 10-29",
      "priority": 2
    },
    {
      "rule_id": "bili_high_omit",
      "parameter": "bilirubin",
      "parameter_unit": "µmol/L",
      "condition": "> 86",
      "condition_type": "greater_than",
      "threshold_value": 86,
      "threshold_low": null,
      "threshold_high": null,
      "affected_drugs": ["doxorubicin"],
      "modification_type": "omit",
      "modification_percent": 0,
      "description": "Omit doxorubicin if bilirubin > 86 µmol/L",
      "action_text": "Doxorubicin omitted because bilirubin > 86 µmol/L",
      "priority": 1
    },
    {
      "rule_id": "bili_51_86",
      "parameter": "bilirubin",
      "parameter_unit": "µmol/L",
      "condition": "51-86",
      "condition_type": "range",
      "threshold_value": null,
      "threshold_low": 51,
      "threshold_high": 86,
      "affected_drugs": ["doxorubicin"],
      "modification_type": "reduce",
      "modification_percent": 25,
      "description": "Reduce doxorubicin to 25% if bilirubin 51-86 µmol/L",
      "action_text": "Doxorubicin reduced to 25% because bilirubin is between 51–86 µmol/L",
      "priority": 2
    },
    {
      "rule_id": "plt_low_reduce",
      "parameter": "platelets",
      "parameter_unit": "x10⁹/L",
      "condition": "50-74",
      "condition_type": "range",
      "threshold_value": null,
      "threshold_low": 50,
      "threshold_high": 74,
      "affected_drugs": ["cyclophosphamide", "doxorubicin"],
      "modification_type": "reduce",
      "modification_percent": 75,
      "description": "Reduce by 25% if platelets 50-74 x10⁹/L",
      "action_text": "Dosage reduced by 25% because of low platelets",
      "priority": 3,
      "check_if_already_reduced": true
    },
    {
      "rule_id": "plt_very_low",
      "parameter": "platelets",
      "parameter_unit": "x10⁹/L",
      "condition": "< 50",
      "condition_type": "less_than",
      "threshold_value": 50,
      "affected_drugs": ["all"],
      "modification_type": "delay",
      "delay_days": 7,
      "description": "Delay cycle by 1 week if platelets < 50",
      "action_text": "Platelet counts are very low, consider delay next cycle by 1 week",
      "priority": 1
    },
    {
      "rule_id": "neut_low_delay",
      "parameter": "neutrophils",
      "parameter_unit": "x10⁹/L",
      "condition": "< 0.5",
      "condition_type": "less_than",
      "threshold_value": 0.5,
      "affected_drugs": ["all"],
      "modification_type": "delay",
      "delay_days": 7,
      "description": "Delay if neutrophils < 0.5",
      "action_text": "Consider delaying the next cycle by 1 week due to very low neutrophil count",
      "priority": 1
    }
  ],
  
  "hematological_toxicity_rules": [
    {
      "toxicity_type": "neutropenia",
      "grade": 4,
      "threshold": "< 0.5",
      "threshold_value": 0.5,
      "action": "delay",
      "delay_days": 7,
      "additional_notes": "Consider G-CSF support"
    },
    {
      "toxicity_type": "thrombocytopenia", 
      "grade": 3,
      "threshold": "50-74",
      "threshold_low": 50,
      "threshold_high": 74,
      "action": "reduce",
      "reduction_percent": 25,
      "check_drugs": ["cyclophosphamide", "doxorubicin"]
    }
  ],
  
  "non_hematological_toxicity_rules": [
    {
      "toxicity_type": "gross_hematuria",
      "affected_drugs": ["cyclophosphamide"],
      "action": "consider_modification",
      "action_text": "Gross hematuria has developed, consider changing cyclophosphamide dosage",
      "monitoring_frequency": "each_cycle"
    },
    {
      "toxicity_type": "motor_weakness",
      "affected_drugs": ["vincristine"],
      "action": "reduce_or_omit",
      "action_text": "Consider withholding or reducing vincristine due to motor weakness",
      "monitoring_frequency": "each_cycle"
    },
    {
      "toxicity_type": "peripheral_neuropathy",
      "grade": 2,
      "affected_drugs": ["vincristine", "oxaliplatin", "bortezomib"],
      "action": "reduce_50",
      "action_text": "Reduce dose by 50% for Grade 2 peripheral neuropathy"
    },
    {
      "toxicity_type": "hepatotoxicity",
      "parameter": "alt",
      "threshold": "> 5x ULN",
      "action": "hold",
      "action_text": "Hold treatment until ALT returns to < 3x ULN"
    }
  ],
  
  "metabolic_monitoring": [
    {
      "parameter": "hba1c",
      "baseline_required": true,
      "change_threshold_percent": 10,
      "action_on_change": "alert",
      "action_text": "HbA1c has changed by ≥10% from baseline - review glucose control"
    },
    {
      "parameter": "glucose",
      "baseline_required": true,
      "change_threshold_percent": 10,
      "action_on_change": "alert",
      "action_text": "Plasma glucose has changed by ≥10% from baseline"
    }
  ],
  
  "age_based_modifications": [
    {
      "age_threshold": 70,
      "operator": ">",
      "affected_drugs": ["vincristine"],
      "modification_type": "cap",
      "cap_dose": 1.0,
      "cap_unit": "mg",
      "description": "Cap vincristine at 1mg for patients over 70"
    },
    {
      "age_threshold": 26,
      "operator": "<",
      "trigger_condition": "cumulative_anthracycline > 300 mg/m²",
      "recommendation": "cardioprotectant",
      "cardioprotectant_drug": "dexrazoxane",
      "description": "Consider dexrazoxane for patients < 26 years receiving > 300 mg/m² anthracycline"
    }
  ],
  
  "cumulative_toxicity_tracking": [
    {
      "drug_class": "anthracycline",
      "drugs": ["doxorubicin", "daunorubicin", "epirubicin", "idarubicin"],
      "standard_limit_mg_m2": 450,
      "monitoring": "ECHO/MUGA before treatment and periodically",
      "reduced_limits": [
        {"condition": "prior cardiac disease", "limit": 400, "unit": "mg/m²"},
        {"condition": "age > 70", "limit": 400, "unit": "mg/m²"},
        {"condition": "prior mediastinal radiation", "limit": 350, "unit": "mg/m²"},
        {"condition": "concurrent trastuzumab", "limit": 300, "unit": "mg/m²"}
      ],
      "warning_at_percent": 80,
      "alert_text": "Approaching lifetime anthracycline limit - monitor cardiac function"
    },
    {
      "drug": "bleomycin",
      "lifetime_limit": 400,
      "limit_unit": "units",
      "monitoring": "Pulmonary function tests",
      "warning_at_percent": 75,
      "alert_text": "Approaching lifetime bleomycin limit - monitor pulmonary function"
    }
  ],
  
  "treatment_delay_criteria": [
    {
      "parameter": "neutrophils",
      "threshold": "< 1.0",
      "threshold_value": 1.0,
      "delay_until": "≥ 1.0 x10⁹/L",
      "max_delay_weeks": 2,
      "action_if_not_recovered": "Consider G-CSF or dose reduction"
    },
    {
      "parameter": "platelets",
      "threshold": "< 100",
      "threshold_value": 100,
      "delay_until": "≥ 100 x10⁹/L",
      "max_delay_weeks": 2
    },
    {
      "parameter": "infection",
      "condition": "active_infection",
      "delay_until": "Infection resolved and afebrile 48h"
    }
  ],
  
  "baseline_requirements": [
    {
      "test": "FBC",
      "includes": ["neutrophils", "platelets", "hemoglobin", "WBC"],
      "timing": "Within 7 days before cycle 1",
      "required": true
    },
    {
      "test": "renal_function",
      "includes": ["creatinine", "GFR", "creatinine_clearance", "urea"],
      "timing": "Within 7 days before cycle 1",
      "required": true
    },
    {
      "test": "liver_function",
      "includes": ["bilirubin", "ALT", "AST", "ALP"],
      "timing": "Within 7 days before cycle 1",
      "required": true
    },
    {
      "test": "cardiac_function",
      "includes": ["LVEF", "ECHO"],
      "timing": "Before first cycle if anthracycline or cardiac risk",
      "required": "conditional",
      "condition": "anthracycline in protocol OR prior cardiac history"
    },
    {
      "test": "virology_panel",
      "includes": ["hep_b_surface_antigen", "hep_b_core_antibody", "hep_c_antibody", "HIV", "EBV", "CMV", "VZV"],
      "timing": "Before first cycle if anti-CD20 (rituximab/obinutuzumab) or immunosuppressive therapy",
      "required": "conditional",
      "condition": "rituximab OR obinutuzumab OR fludarabine OR bendamustine in protocol"
    },
    {
      "test": "g6pd",
      "includes": ["g6pd_status"],
      "timing": "Before first cycle",
      "required": "conditional",
      "condition": "rasburicase prescribed OR high TLS risk"
    },
    {
      "test": "tumour_markers",
      "includes": ["LDH", "beta2_microglobulin", "disease_stage", "histology"],
      "timing": "Before first cycle",
      "required": "conditional",
      "condition": "lymphoma OR leukaemia — prognostic markers for IPI/FLIPI score"
    },
    {
      "test": "metabolic_baseline",
      "includes": ["HbA1c", "glucose", "calcium", "magnesium", "urate", "phosphate"],
      "timing": "Before first cycle if TLS risk or corticosteroid use",
      "required": "conditional",
      "condition": "steroid in protocol OR high tumour burden OR venetoclax/TLS risk"
    }
  ],

  "required_patient_fields": {
    "_comment": "Map fields from PatientData that THIS protocol specifically requires. Used to highlight mandatory inputs in the UI.",
    "always_required": ["neutrophils", "platelets", "hemoglobin", "creatinine_clearance", "bilirubin", "performance_status"],
    "required_if_present": {
      "hep_b_surface_antigen": "Protocol contains rituximab or obinutuzumab — HBV reactivation risk",
      "hep_b_core_antibody": "Protocol contains rituximab or obinutuzumab — HBV reactivation risk",
      "hep_c_antibody": "Protocol contains rituximab or obinutuzumab",
      "hiv_status": "Protocol contains rituximab or obinutuzumab",
      "ebv_status": "Protocol contains rituximab",
      "cmv_status": "Immunosuppressive protocol — CMV reactivation risk",
      "vzv_status": "Protocol contains aciclovir/bortezomib — check VZV before starting",
      "lvef_percent": "Protocol contains anthracycline — baseline cardiac function required",
      "g6pd_status": "Protocol contains rasburicase — G6PD deficiency is absolute contraindication",
      "prior_anthracycline_dose_mg_m2": "Protocol contains anthracycline — cumulative dose tracking required",
      "ldh": "Lymphoma/leukaemia — LDH is prognostic and TLS risk marker",
      "beta2_microglobulin": "Lymphoma — prognostic marker",
      "urate": "High TLS risk protocol — baseline urate required",
      "calcium": "TLS monitoring — baseline calcium required",
      "histology": "Required for correct dose modification rule selection",
      "disease_stage": "Affects total cycles and treatment intent"
    }
  },
  
  "pre_cycle_labs": [
    {
      "test": "FBC",
      "timing": "Within 48h before each cycle",
      "required": true
    },
    {
      "test": "U&E",
      "timing": "Within 7 days before each cycle",
      "required": true
    },
    {
      "test": "LFT",
      "timing": "Within 7 days before each cycle", 
      "required": true
    }
  ],
  
  "post_cycle_monitoring": [
    {
      "test": "FBC",
      "timing": "Day 10-14 (nadir)",
      "purpose": "Monitor for neutropenia/thrombocytopenia",
      "action_on_abnormal": "Consider G-CSF, transfusion as needed"
    }
  ],
  
  "toxicities": [
    {
      "drug_id": "drug_name",
      "adverse_effects": ["Effect 1", "Effect 2", "Effect 3"],
      "severity_grades": {
        "Effect 1": "common",
        "Effect 2": "serious",
        "Effect 3": "rare but severe"
      }
    }
  ],
  
  "monitoring": [
    "FBC, LFTs and U&Es prior to day one of each cycle",
    "Check hepatitis B status before rituximab - risk of reactivation",
    "Baseline LVEF for patients with cardiac history or receiving anthracyclines",
    "Monitor for tumor lysis syndrome in first cycle if high tumor burden"
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

CRITICAL EXTRACTION RULES - READ CAREFULLY:

1. dose_unit must be one of: "mg", "mg/m²", "mg/kg", "g", "g/m²", "units", "units/m²", "mcg", "mcg/m²", "ml", "AUC"
2. route must be one of: "IV bolus", "IV infusion", "Oral", "Subcutaneous", "IM", "Nebulised", "Topical", "Intrathecal"
3. For dose modifications, parameter can be: "neutrophils", "platelets", "bilirubin", "gfr", "creatinine_clearance", "creatinine", "ast", "alt", "alp", "hemoglobin", "wbc", "lymphocytes", "ldh", "urate", "calcium", "lvef_percent"
4. modification_type must be: "omit", "reduce", "delay", "cap", "hold", "consider_modification"
5. condition_type must be: "less_than", "greater_than", "less_equal", "greater_equal", "range", "equals"
6. In required_patient_fields, only include keys that are ACTUALLY required by this specific protocol based on its drugs and risks.

EXTRACTION PRIORITIES - Extract ALL of the following:

A. DOSE MODIFICATION RULES - Extract EVERY rule for:
   - Renal impairment (GFR/CrCl thresholds with % reductions)
   - Hepatic impairment (bilirubin, ALT, AST thresholds)
   - Hematological toxicity (neutropenia, thrombocytopenia)
   - Non-hematological toxicity (neuropathy, mucositis, skin reactions, etc.)
   - Age-based modifications (caps, reductions for elderly)
   - LDH-based rules (e.g., TLS prophylaxis if LDH > 2x ULN)
   - LVEF-based rules (e.g., reduce anthracycline if LVEF < 50%)

B. CUMULATIVE TOXICITY - For drugs with lifetime limits:
   - Anthracyclines (doxorubicin limit ~450 mg/m², less for cardiac risk)
   - Bleomycin (pulmonary toxicity limit)
   - Cumulative platinum (nephrotoxicity)

C. TREATMENT DELAYS - When to delay:
   - Lab value thresholds for delay
   - How long to delay
   - When to restart

D. SPECIAL MONITORING:
   - Baseline tests required (including virology, G6PD, LVEF, LDH, β2-microglobulin)
   - Per-cycle tests required
   - Post-cycle monitoring (nadir FBC, renal function, urate/TLS markers)
   - Drug-specific monitoring (cardiac for anthracyclines, pulmonary for bleomycin)
   - VZV/CMV/EBV surveillance for immunosuppressive protocols

E. DRUG INTERACTIONS AND CONTRAINDICATIONS:
   - Foods to avoid (grapefruit, etc.)
   - Drug interactions (CYP3A4 inhibitors/inducers for venetoclax/ibrutinib/imatinib/gilteritinib, QT prolonging drugs)
   - Absolute contraindications (e.g., G6PD deficiency + rasburicase)
   - HBV reactivation risk (rituximab/obinutuzumab + HBcAb positive)

F. SUPPORTIVE CARE REQUIREMENTS:
   - Hydration requirements
   - Antiemetic regimen
   - Infection prophylaxis (cotrimoxazole, aciclovir, fluconazole — with triggers)
   - Tumor lysis syndrome prophylaxis (allopurinol/rasburicase — with LDH/urate triggers)
   - Growth factor support criteria (G-CSF — with neutrophil threshold triggers)
   - Irradiated blood products requirement (fludarabine, cladribine, clofarabine, bendamustine)

G. SPECIAL POPULATIONS:
   - Elderly adjustments
   - Renal dosing
   - Hepatic dosing
   - Obesity (BSA capping)
   - Pregnancy contraindications

H. ADMINISTRATION DETAILS:
   - Infusion rates and escalation (especially rituximab, obinutuzumab ramp-up)
   - Line requirements (central vs peripheral)
   - Filter requirements
   - Stability and storage
   - Vesicant precautions

I. PATIENT WORKUP (required_patient_fields):
   - Map every pre-treatment check the protocol REQUIRES to the corresponding PatientData field name
   - Be specific: if rituximab is present → "hep_b_surface_antigen", "hep_b_core_antibody", "hiv_status"
   - If anthracycline → "lvef_percent", "prior_anthracycline_dose_mg_m2"
   - If rasburicase → "g6pd_status" (CONTRAINDICATED in G6PD deficiency)
   - If lymphoma/leukaemia → "ldh", "beta2_microglobulin", "histology", "disease_stage"
   - If TLS risk → "urate", "calcium", "ldh"
   - If bortezomib → "vzv_status" (aciclovir prophylaxis needed)
   - If venetoclax → "urate", "ldh", "calcium" (TLS monitoring)
   - If bleomycin → "lung_function_fev1" (pulmonary baseline)
   - If imatinib/gilteritinib/midostaurin → note CYP3A4 interactions in warnings

BE COMPREHENSIVE - Extract every dose modification rule, every threshold, every warning.
The more detail you extract, the more automation is possible and the safer patient care becomes.
If the protocol mentions ANY condition that affects dosing, extract it as a rule.

Return ONLY valid JSON, no markdown code blocks or explanations."""


class GeminiProtocolParser:
    """
    Uses Google Gemini to parse chemotherapy protocol PDFs into structured data
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-pro')
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
    
    # Prompt version — bump this whenever EXTRACTION_PROMPT changes to bust cache
    _PROMPT_VERSION = "4"

    async def parse_pdf(self, file_path: str, disease_category: str = "lymphoma") -> dict:
        """
        Parse a protocol PDF using Gemini (async, non-blocking).
        """
        if not self.model:
            raise ValueError("Gemini API key not configured")

        # Cache key includes prompt version so stale AI output is re-parsed when prompt changes
        file_hash = self._get_file_hash(file_path)
        cache_key = f"{file_hash}_v{self._PROMPT_VERSION}"
        cache_file = self.parsed_protocols_dir / f"{cache_key}.json"

        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)

        # Read PDF
        pdf_data = self._read_pdf_as_base64(file_path)

        # Run blocking Gemini call in a thread pool so the event loop is not blocked
        import asyncio
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.model.generate_content([
                EXTRACTION_PROMPT,
                {"mime_type": "application/pdf", "data": pdf_data}
            ])
        )
        
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
            
            # Add metadata with safety flags
            protocol_data["_metadata"] = {
                "source_file": os.path.basename(file_path),
                "file_hash": file_hash,
                "disease_category": disease_category,
                "parsed_at": datetime.now().isoformat(),
                "parser_version": "2.0",
                # SAFETY: AI-parsed protocols MUST be reviewed before clinical use
                "ai_generated": True,
                "pharmacist_verified": False,
                "verification_required": True,
                "verification_warning": "⚠️ AI-EXTRACTED PROTOCOL: This protocol was automatically extracted by AI and has NOT been verified by a pharmacist. DO NOT use for patient care until verified."
            }
            
            # Add safety warnings to the protocol
            if "warnings" not in protocol_data:
                protocol_data["warnings"] = []
            protocol_data["warnings"].insert(0, 
                "⚠️ AI-EXTRACTED: This protocol was parsed by AI from PDF and requires pharmacist verification before clinical use. "
                "Doses, routes, and schedules must be independently verified against the original source document."
            )

            # SAFETY: Perform sanity checks on extracted data
            self._sanity_check_protocol(protocol_data)
            
            # Cache the result (keyed by file hash + prompt version)
            with open(cache_file, 'w') as f:
                json.dump(protocol_data, f, indent=2)
            
            return protocol_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Gemini response as JSON: {e}\nResponse: {response.text[:500]}")

    # Plausibility ranges: drug_substring -> list of (min, max, unit, note)
    # Used to catch AI hallucinations. Ranges are intentionally wide to allow
    # unusual protocols, but catch obvious 10x errors.
    DOSE_PLAUSIBILITY = {
        "rituximab":        [(350, 400, "mg/m²", "IV standard"), (1300, 1500, "mg", "SC fixed")],
        "cyclophosphamide": [(100, 1500, "mg/m²", "standard range")],
        "doxorubicin":      [(25, 75, "mg/m²", "standard range")],
        "vincristine":      [(1.0, 1.4, "mg/m²", "standard range")],
        "prednisolone":     [(40, 100, "mg", "flat dose")],
        "bendamustine":     [(70, 120, "mg/m²", "standard range")],
        "etoposide":        [(50, 200, "mg/m²", "standard range")],
        "gemcitabine":      [(800, 1250, "mg/m²", "standard range")],
        "cisplatin":        [(25, 100, "mg/m²", "standard range")],
        "carboplatin":      [(4, 7, "AUC", "Calvert formula")],
        "methotrexate":     [(10, 5000, "mg/m²", "wide — IT to HD-MTX")],
        "cytarabine":       [(100, 3000, "mg/m²", "standard to HD")],
        "fludarabine":      [(25, 30, "mg/m²", "standard range")],
        "bleomycin":        [(10, 15, "units/m²", "standard range")],
        "dacarbazine":      [(150, 375, "mg/m²", "standard range")],
        "vinblastine":      [(4, 6, "mg/m²", "standard range")],
        "ifosfamide":       [(1000, 5000, "mg/m²", "standard range")],
        "brentuximab":      [(1.2, 1.8, "mg/kg", "standard range")],
        "obinutuzumab":     [(1000, 1000, "mg", "fixed dose")],
        "polatuzumab":      [(1.8, 1.8, "mg/kg", "fixed dose")],
        "idarubicin":       [(8, 12, "mg/m²", "standard range")],
        "daunorubicin":     [(30, 90, "mg/m²", "standard range")],
        "chlorambucil":     [(2, 10, "mg/m²", "standard range")],
        "lenalidomide":     [(10, 25, "mg", "flat dose")],
        "thalidomide":      [(100, 200, "mg", "flat dose")],
        "bortezomib":       [(1.0, 1.3, "mg/m²", "standard range")],
        "ibrutinib":        [(420, 560, "mg", "flat dose")],
        "venetoclax":       [(20, 400, "mg", "flat dose ramp-up")],
        "azacitidine":      [(75, 75, "mg/m²", "fixed dose")],
        "decitabine":       [(15, 20, "mg/m²", "standard range")],
        "gilteritinib":     [(120, 120, "mg", "fixed dose")],
        "midostaurin":      [(50, 50, "mg", "fixed dose")],
        "enasidenib":       [(100, 100, "mg", "fixed dose")],
        "ivosidenib":       [(500, 500, "mg", "fixed dose")],
    }

    def _sanity_check_protocol(self, data: dict):
        """
        Perform sanity checks on AI-extracted protocol data.
        Catches dose hallucinations and enforces critical safety caps.
        """
        warnings = data.get("warnings", [])
        drugs = data.get("drugs", [])

        for drug in drugs:
            name = str(drug.get("drug_name", "")).lower()
            try:
                dose = float(drug.get("dose", 0))
            except (ValueError, TypeError):
                dose = 0.0
            dose_unit = str(drug.get("dose_unit", "")).lower()

            # --- Vincristine: force max dose cap regardless of what AI said ---
            if "vincristine" in name:
                max_dose = drug.get("max_dose")
                try:
                    max_dose_f = float(max_dose) if max_dose is not None else None
                except (ValueError, TypeError):
                    max_dose_f = None
                if max_dose_f is None or max_dose_f > 2.0:
                    warnings.insert(0, "⚠️ SANITY CHECK: Vincristine max dose cap forced to 2.0 mg. This is a life-critical safety cap.")
                    drug["max_dose"] = 2.0
                    drug["max_dose_unit"] = "mg"

            # --- High-dose Methotrexate: ensure leucovorin rescue present ---
            if "methotrexate" in name and dose > 500 and "m²" in dose_unit:
                rescue_drugs = [d.get("drug_name", "").lower() for d in data.get("rescue_medications", [])]
                take_home_drugs = [d.get("drug_name", "").lower() for d in data.get("take_home_medicines", [])]
                all_other = rescue_drugs + take_home_drugs
                if not any("leucovorin" in d or "folinic" in d or "calcium folinate" in d for d in all_other):
                    warnings.insert(0, f"⚠️ SANITY CHECK: High-dose Methotrexate ({dose} {dose_unit}) detected but NO leucovorin rescue found. This is life-critical — verify extraction.")

            # --- Plausibility range check ---
            for drug_key, ranges in self.DOSE_PLAUSIBILITY.items():
                if drug_key in name:
                    unit_matches = any(
                        r[2].lower().replace("²", "2") in dose_unit.replace("²", "2")
                        for r in ranges
                    )
                    if unit_matches:
                        in_any_range = any(r[0] <= dose <= r[1] for r in ranges if r[2].lower().replace("²","2") in dose_unit.replace("²","2"))
                        if not in_any_range:
                            expected = " or ".join(f"{r[0]}–{r[1]} {r[2]} ({r[3]})" for r in ranges)
                            warnings.insert(0,
                                f"⚠️ SANITY CHECK: {drug.get('drug_name')} dose {dose} {drug.get('dose_unit')} is OUTSIDE expected range ({expected}). "
                                f"Verify against original PDF — possible AI hallucination."
                            )
                    break

        data["warnings"] = warnings
    
    def parse_pdf_sync(self, file_path: str, disease_category: str = "lymphoma") -> dict:
        """Synchronous version of parse_pdf"""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            # Already inside an event loop — run in a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, self.parse_pdf(file_path, disease_category))
                return future.result()
        return asyncio.run(self.parse_pdf(file_path, disease_category))
    
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
            
            # Handle administration_order - explicit None check because d.get() returns None if key exists with None value
            admin_order = d.get("administration_order")
            if admin_order is None:
                admin_order = order
            else:
                try:
                    admin_order = int(admin_order)
                except (ValueError, TypeError):
                    admin_order = order
            
            # Handle optional integer fields - they can be None
            duration_mins = d.get("duration_minutes")
            if duration_mins is not None:
                try:
                    duration_mins = int(duration_mins)
                except (ValueError, TypeError):
                    duration_mins = None
            
            diluent_vol = d.get("diluent_volume_ml")
            if diluent_vol is not None:
                try:
                    diluent_vol = int(diluent_vol)
                except (ValueError, TypeError):
                    diluent_vol = None
            
            max_dose_val = d.get("max_dose")
            if max_dose_val is not None:
                try:
                    max_dose_val = float(max_dose_val)
                except (ValueError, TypeError):
                    max_dose_val = None
            
            return ProtocolDrug(
                drug_id=drug_id,
                drug_name=d.get("drug_name") or "Unknown",
                dose=dose,
                dose_unit=dose_unit,
                route=route,
                days=days,
                duration_minutes=duration_mins,
                diluent=d.get("diluent"),
                diluent_volume_ml=diluent_vol,
                administration_order=admin_order,
                max_dose=max_dose_val,
                max_dose_unit=d.get("max_dose_unit"),
                timing=d.get("timing"),
                frequency=d.get("frequency"),
                special_instructions=d.get("special_instructions"),
                prn=prn,
                is_core_drug=is_core_drug
            )
        
        def parse_modification(m: dict) -> DoseModificationRule:
            """Parse dose modification with full support for new enhanced fields"""
            # Ensure affected_drugs is a list
            affected_drugs = m.get("affected_drugs")
            if not isinstance(affected_drugs, list):
                affected_drugs = []
            
            # Parse threshold values
            threshold_value = m.get("threshold_value")
            if threshold_value is not None:
                try:
                    threshold_value = float(threshold_value)
                except (ValueError, TypeError):
                    threshold_value = None
            
            threshold_low = m.get("threshold_low")
            if threshold_low is not None:
                try:
                    threshold_low = float(threshold_low)
                except (ValueError, TypeError):
                    threshold_low = None
            
            threshold_high = m.get("threshold_high")
            if threshold_high is not None:
                try:
                    threshold_high = float(threshold_high)
                except (ValueError, TypeError):
                    threshold_high = None
            
            delay_days = m.get("delay_days")
            if delay_days is not None:
                try:
                    delay_days = int(delay_days)
                except (ValueError, TypeError):
                    delay_days = None
            
            priority = m.get("priority", 1)
            try:
                priority = int(priority)
            except (ValueError, TypeError):
                priority = 1
            
            return DoseModificationRule(
                rule_id=m.get("rule_id") or "",
                parameter=m.get("parameter") or "",
                parameter_unit=m.get("parameter_unit") or "",
                condition=m.get("condition") or "",
                condition_type=m.get("condition_type") or "less_than",
                threshold_value=threshold_value,
                threshold_low=threshold_low,
                threshold_high=threshold_high,
                affected_drugs=affected_drugs,
                modification=m.get("modification") or "",
                modification_type=m.get("modification_type") or "reduce",
                modification_percent=m.get("modification_percent"),
                delay_days=delay_days,
                description=m.get("description") or "",
                action_text=m.get("action_text") or "",
                priority=priority,
                check_if_already_reduced=bool(m.get("check_if_already_reduced", False))
            )
        
        def parse_hematological_toxicity_rule(h: dict) -> HematologicalToxicityRule:
            """Parse hematological toxicity rules"""
            return HematologicalToxicityRule(
                toxicity_type=h.get("toxicity_type") or "",
                grade=h.get("grade"),
                threshold=h.get("threshold") or "",
                threshold_value=h.get("threshold_value"),
                threshold_low=h.get("threshold_low"),
                threshold_high=h.get("threshold_high"),
                action=h.get("action") or "",
                delay_days=h.get("delay_days"),
                reduction_percent=h.get("reduction_percent"),
                check_drugs=h.get("check_drugs") or [],
                additional_notes=h.get("additional_notes") or ""
            )
        
        def parse_non_hematological_toxicity_rule(n: dict) -> NonHematologicalToxicityRule:
            """Parse non-hematological toxicity rules"""
            return NonHematologicalToxicityRule(
                toxicity_type=n.get("toxicity_type") or "",
                grade=n.get("grade"),
                parameter=n.get("parameter"),
                threshold=n.get("threshold"),
                affected_drugs=n.get("affected_drugs") or [],
                action=n.get("action") or "",
                action_text=n.get("action_text") or "",
                monitoring_frequency=n.get("monitoring_frequency") or "each_cycle"
            )
        
        def parse_metabolic_monitoring_rule(mm: dict) -> MetabolicMonitoringRule:
            """Parse metabolic monitoring rules"""
            return MetabolicMonitoringRule(
                parameter=mm.get("parameter") or "",
                baseline_required=bool(mm.get("baseline_required", True)),
                change_threshold_percent=mm.get("change_threshold_percent"),
                action_on_change=mm.get("action_on_change") or "alert",
                action_text=mm.get("action_text") or ""
            )
        
        def parse_age_based_modification(a: dict) -> AgeBasedModification:
            """Parse age-based modification rules"""
            return AgeBasedModification(
                age_threshold=a.get("age_threshold", 70),
                operator=a.get("operator") or ">",
                affected_drugs=a.get("affected_drugs") or [],
                modification_type=a.get("modification_type") or "cap",
                cap_dose=a.get("cap_dose"),
                cap_unit=a.get("cap_unit"),
                reduction_percent=a.get("reduction_percent"),
                trigger_condition=a.get("trigger_condition"),
                recommendation=a.get("recommendation"),
                cardioprotectant_drug=a.get("cardioprotectant_drug"),
                description=a.get("description") or ""
            )
        
        def parse_cumulative_toxicity_tracking(c: dict) -> CumulativeToxicityTracking:
            """Parse cumulative toxicity tracking rules"""
            reduced_limits = c.get("reduced_limits") or []
            parsed_limits = []
            for rl in reduced_limits:
                if isinstance(rl, dict):
                    parsed_limits.append(ReducedLimitCondition(
                        condition=rl.get("condition") or "",
                        limit=rl.get("limit", 0),
                        unit=rl.get("unit") or "mg/m²"
                    ))
            
            return CumulativeToxicityTracking(
                drug_class=c.get("drug_class"),
                drug=c.get("drug"),
                drugs=c.get("drugs") or [],
                standard_limit_mg_m2=c.get("standard_limit_mg_m2"),
                lifetime_limit=c.get("lifetime_limit"),
                limit_unit=c.get("limit_unit") or "mg/m²",
                monitoring=c.get("monitoring") or "",
                reduced_limits=parsed_limits,
                warning_at_percent=c.get("warning_at_percent", 80),
                alert_text=c.get("alert_text") or ""
            )
        
        def parse_treatment_delay_criteria(t: dict) -> TreatmentDelayCriteria:
            """Parse treatment delay criteria"""
            return TreatmentDelayCriteria(
                parameter=t.get("parameter") or "",
                threshold=t.get("threshold") or "",
                threshold_value=t.get("threshold_value"),
                delay_until=t.get("delay_until") or "",
                max_delay_weeks=t.get("max_delay_weeks"),
                action_if_not_recovered=t.get("action_if_not_recovered"),
                condition=t.get("condition")
            )
        
        def parse_baseline_requirement(b: dict) -> BaselineRequirement:
            """Parse baseline requirement"""
            return BaselineRequirement(
                test=b.get("test") or "",
                includes=b.get("includes") or [],
                timing=b.get("timing") or "",
                required=str(b.get("required", "true")),
                condition=b.get("condition")
            )
        
        def parse_pre_cycle_lab(p: dict) -> PreCycleLab:
            """Parse pre-cycle lab requirement"""
            return PreCycleLab(
                test=p.get("test") or "",
                timing=p.get("timing") or "",
                required=bool(p.get("required", True))
            )
        
        def parse_post_cycle_monitoring(p: dict) -> PostCycleMonitoring:
            """Parse post-cycle monitoring requirement"""
            return PostCycleMonitoring(
                test=p.get("test") or "",
                timing=p.get("timing") or "",
                purpose=p.get("purpose") or "",
                action_on_abnormal=p.get("action_on_abnormal") or ""
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
        
        # Parse new enhanced fields
        hematological_toxicity_rules = data.get("hematological_toxicity_rules")
        if not isinstance(hematological_toxicity_rules, list):
            hematological_toxicity_rules = []
        
        non_hematological_toxicity_rules = data.get("non_hematological_toxicity_rules")
        if not isinstance(non_hematological_toxicity_rules, list):
            non_hematological_toxicity_rules = []
        
        metabolic_monitoring = data.get("metabolic_monitoring")
        if not isinstance(metabolic_monitoring, list):
            metabolic_monitoring = []
        
        age_based_modifications = data.get("age_based_modifications")
        if not isinstance(age_based_modifications, list):
            age_based_modifications = []
        
        cumulative_toxicity_tracking = data.get("cumulative_toxicity_tracking")
        if not isinstance(cumulative_toxicity_tracking, list):
            cumulative_toxicity_tracking = []
        
        treatment_delay_criteria = data.get("treatment_delay_criteria")
        if not isinstance(treatment_delay_criteria, list):
            treatment_delay_criteria = []
        
        baseline_requirements = data.get("baseline_requirements")
        if not isinstance(baseline_requirements, list):
            baseline_requirements = []
        
        pre_cycle_labs = data.get("pre_cycle_labs")
        if not isinstance(pre_cycle_labs, list):
            pre_cycle_labs = []
        
        post_cycle_monitoring = data.get("post_cycle_monitoring")
        if not isinstance(post_cycle_monitoring, list):
            post_cycle_monitoring = []
        
        # Build protocol with all enhanced fields
        return Protocol(
            id=data.get("protocol_id") or "unknown",
            name=data.get("protocol_name") or "Unknown Protocol",
            code=data.get("protocol_code") or "UNK",
            full_name=data.get("full_name") or data.get("protocol_name") or "",
            indication=data.get("indication") or "",
            cycle_length_days=cycle_length_days,
            total_cycles=total_cycles,
            version=data.get("version") or "1.0",
            treatment_intent=data.get("treatment_intent") or "",
            drugs=[parse_drug(d, i) for i, d in enumerate(drugs)],
            pre_medications=[parse_drug(d, i) for i, d in enumerate(pre_medications)],
            take_home_medicines=[parse_drug(d, i) for i, d in enumerate(take_home_medicines)],
            rescue_medications=[parse_drug(d, i) for i, d in enumerate(rescue_medications)],
            dose_modifications=[parse_modification(m) for m in dose_modifications],
            hematological_toxicity_rules=[parse_hematological_toxicity_rule(h) for h in hematological_toxicity_rules],
            non_hematological_toxicity_rules=[parse_non_hematological_toxicity_rule(n) for n in non_hematological_toxicity_rules],
            metabolic_monitoring=[parse_metabolic_monitoring_rule(mm) for mm in metabolic_monitoring],
            age_based_modifications=[parse_age_based_modification(a) for a in age_based_modifications],
            cumulative_toxicity_tracking=[parse_cumulative_toxicity_tracking(c) for c in cumulative_toxicity_tracking],
            treatment_delay_criteria=[parse_treatment_delay_criteria(t) for t in treatment_delay_criteria],
            baseline_requirements=[parse_baseline_requirement(b) for b in baseline_requirements],
            pre_cycle_labs=[parse_pre_cycle_lab(p) for p in pre_cycle_labs],
            post_cycle_monitoring=[parse_post_cycle_monitoring(p) for p in post_cycle_monitoring],
            toxicities=[parse_toxicity(t) for t in toxicities],
            monitoring=monitoring,
            warnings=warnings,
            source_file=data.get("_metadata", {}).get("source_file"),
            is_ai_generated=data.get("_metadata", {}).get("ai_generated", True),
            required_patient_fields=data.get("required_patient_fields", {}).get("required_if_present", {}),
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
