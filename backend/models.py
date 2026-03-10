"""
Chemotherapy Protocol Engine - Data Models
NHS Lymphoma Protocols

SAFETY CRITICAL: This module contains patient safety validation logic.
Changes must be reviewed by medical professional before deployment.
"""

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator
from typing import Optional, Literal, Self
from enum import Enum
from datetime import datetime
import math


# ============= SAFETY CONSTANTS =============
# Based on ASCO, ONS, and NHS guidelines

# BSA limits (ASCO guidelines)
BSA_MIN = 0.5  # m² - minimum physiologically possible
BSA_MAX = 3.5  # m² - maximum physiologically possible
BSA_CAP_OBESE = 2.0  # m² - cap for obese patients per ASCO guidelines

# Lab value hard stops (treatment contraindicated)
NEUTROPHIL_HARD_STOP = 0.5  # x10⁹/L - absolute contraindication
PLATELET_HARD_STOP = 50  # x10⁹/L - absolute contraindication
CREATININE_CLEARANCE_HARD_STOP = 10  # ml/min - severe renal failure

# Lab value warnings (delay treatment)
NEUTROPHIL_DELAY_THRESHOLD = 1.0  # x10⁹/L
PLATELET_DELAY_THRESHOLD = 100  # x10⁹/L


class LabUnitSystem(str, Enum):
    """Unit system for lab values - CRITICAL for correct dosing"""
    SI = "SI"  # International System (UK, most of world)
    CONVENTIONAL = "Conventional"  # US customary units


class ECOGPerformanceStatus(int, Enum):
    """ECOG Performance Status Scale - Required for dose decisions"""
    FULLY_ACTIVE = 0  # Fully active, no restrictions
    RESTRICTED_STRENUOUS = 1  # Restricted in strenuous activity but ambulatory
    AMBULATORY_SELFCARE = 2  # Ambulatory and capable of all selfcare, up >50% of waking hours
    LIMITED_SELFCARE = 3  # Capable of only limited selfcare, confined to bed/chair >50% of waking hours
    COMPLETELY_DISABLED = 4  # Completely disabled, cannot carry out any selfcare


class RouteOfAdministration(str, Enum):
    IV_BOLUS = "IV bolus"
    IV_INFUSION = "IV infusion"
    ORAL = "Oral"
    SC = "Subcutaneous"
    IM = "Intramuscular"
    NEBULISED = "Nebulised"
    TOPICAL = "Topical"
    OROMUCOSAL = "Oromucosal"


class DoseUnit(str, Enum):
    MG = "mg"
    MG_M2 = "mg/m²"
    MG_KG = "mg/kg"
    G = "g"
    G_M2 = "g/m²"
    UNITS = "units"
    UNITS_M2 = "units/m²"
    MG_FLAT = "mg (flat)"
    MCG = "mcg"
    MCG_M2 = "mcg/m²"
    ML = "ml"
    DROP = "drop"  # Added for eye drops
    ML_HOUR = "ml/hour"
    UNKNOWN = "unknown" # Fallback


class DrugCategory(str, Enum):
    CHEMOTHERAPY = "chemotherapy"
    IMMUNOTHERAPY = "immunotherapy"
    TARGETED = "targeted_therapy"
    STEROID = "steroid"
    ANTIEMETIC = "antiemetic"
    PREMEDICATION = "premedication"
    SUPPORTIVE = "supportive_care"
    RESCUE = "rescue_medication"


class Drug(BaseModel):
    """Individual drug information"""
    id: str
    name: str
    generic_name: str
    category: DrugCategory
    aliases: list[str] = []
    vesicant: bool = False
    default_route: RouteOfAdministration = RouteOfAdministration.IV_INFUSION
    max_dose: Optional[float] = None
    max_dose_unit: Optional[str] = None
    requires_bsa: bool = True
    special_warnings: list[str] = []
    
    class Config:
        use_enum_values = True


class ProtocolDrug(BaseModel):
    """Drug within a protocol with dosing details"""
    drug_id: str
    drug_name: str
    dose: float
    dose_unit: DoseUnit
    route: RouteOfAdministration
    days: list[int]  # e.g., [1, 2] for days 1 and 2
    duration_minutes: Optional[int] = None
    diluent: Optional[str] = None
    diluent_volume_ml: Optional[int] = None
    administration_order: int = Field(default=0)
    is_core_drug: bool = True  # False for pre-meds, supportive care
    is_optional: bool = False
    max_dose: Optional[float] = None
    max_dose_unit: Optional[str] = None
    timing: Optional[str] = None  # e.g., "30 mins before rituximab"
    frequency: Optional[str] = None  # e.g., "twice daily", "three times a day"
    special_instructions: Optional[str] = None
    prn: bool = False  # As needed
    
    # Handle None values from Gemini parsing - convert to defaults
    @field_validator('administration_order', mode='before')
    @classmethod
    def set_admin_order_default(cls, v):
        if v is None:
            return 0
        return int(v)
    
    @field_validator('dose', mode='before')
    @classmethod
    def set_dose_default(cls, v):
        if v is None:
            return 0.0
        if isinstance(v, str):
            # Handle ranges "50-100" -> 100.0 (Safety check uses max)
            matches = re.findall(r"(\d+\.?\d*)", v)
            if matches:
                return float(max(matches, key=float))
            return 0.0
        return float(v)
    
    @field_validator('days', mode='before')
    @classmethod
    def set_days_default(cls, v):
        if v is None or v == []:
            return [1]
        return v
    
    @field_validator('is_core_drug', 'is_optional', 'prn', mode='before')
    @classmethod
    def set_bool_default(cls, v):
        if v is None:
            return False
        return bool(v)

    @field_validator('dose_unit', mode='before')
    @classmethod
    def set_dose_unit_default(cls, v):
        if v is None:
            return DoseUnit.MG  # Default for safety/schema compliance
        return v

    @field_validator('route', mode='before')
    @classmethod
    def set_route_default(cls, v):
        if v is None:
            return RouteOfAdministration.ORAL  # Safest default
        # Handle fuzzy matching — bolus must be checked before generic "iv"
        if isinstance(v, str):
            v_lower = v.lower()
            if "oral" in v_lower:
                return RouteOfAdministration.ORAL
            if "bolus" in v_lower:
                return RouteOfAdministration.IV_BOLUS
            if "iv" in v_lower or "intravenous" in v_lower:
                return RouteOfAdministration.IV_INFUSION
            if "subcutaneous" in v_lower or "sc" in v_lower:
                return RouteOfAdministration.SC
            if "intramuscular" in v_lower or "im" in v_lower:
                return RouteOfAdministration.IM
            if "topical" in v_lower:
                return RouteOfAdministration.TOPICAL
            if "nebulised" in v_lower:
                return RouteOfAdministration.NEBULISED
            if "oromucosal" in v_lower:
                return RouteOfAdministration.OROMUCOSAL
        return v
    
    class Config:
        use_enum_values = True


import re

class ModificationType(str, Enum):
    """Types of dose modifications"""
    OMIT = "omit"  # Do not give the drug
    REDUCE = "reduce"  # Reduce by percentage
    DELAY = "delay"  # Delay treatment
    CAP = "cap"  # Cap at maximum dose
    HOLD = "hold"  # Hold until condition resolves
    CONSIDER = "consider_modification"  # Alert for clinical judgment


class ConditionType(str, Enum):
    """Types of conditions for dose modifications"""
    LESS_THAN = "less_than"
    GREATER_THAN = "greater_than"
    LESS_EQUAL = "less_equal"
    GREATER_EQUAL = "greater_equal"
    RANGE = "range"
    EQUALS = "equals"


class DoseModificationRule(BaseModel):
    """
    Enhanced rules for dose modification based on lab values.
    Supports complex conditions like those in RCHOP protocol.
    """
    rule_id: str = ""  # Unique identifier for the rule
    parameter: str = ""  # e.g., "neutrophils", "bilirubin", "gfr", "creatinine_clearance"
    parameter_unit: str = ""  # e.g., "x10⁹/L", "µmol/L", "ml/min"
    condition: str = ""  # Human readable: "< 1.0", "20-50", "> 85"
    condition_type: str = "less_than"  # "less_than", "greater_than", "range", etc.
    threshold_value: Optional[float] = None  # Single threshold for </>/<=/>= 
    threshold_low: Optional[float] = None  # Lower bound for range
    threshold_high: Optional[float] = None  # Upper bound for range
    affected_drugs: list[str] = []  # Drug IDs affected, or ["all"] for all drugs
    modification: str = ""  # Legacy field for backwards compatibility
    modification_type: str = "reduce"  # "omit", "reduce", "delay", "cap", "hold"
    modification_percent: Optional[int] = None  # Percentage of original dose (75 = reduce by 25%)
    delay_days: Optional[int] = None  # Days to delay if modification_type is "delay"
    description: str = ""  # Clinical description
    action_text: str = ""  # Text to show in the changes list (nurse-friendly)
    priority: int = 1  # Priority order (1 = highest, apply first)
    check_if_already_reduced: bool = False  # Skip if dose already reduced by other rule

    # Secondary condition for compound AND/OR rules
    # e.g. "Bilirubin <30 AND AST 2-3×ULN" → primary=bilirubin, secondary=ast
    secondary_parameter: str = ""          # e.g. "ast", "alt"
    secondary_condition_type: str = ""     # "less_than", "greater_than", "range", "normal", "elevated"
    secondary_threshold_value: Optional[float] = None
    secondary_threshold_low: Optional[float] = None
    secondary_threshold_high: Optional[float] = None
    secondary_connector: str = ""          # "AND" or "OR" — how primary+secondary are combined
    
    @field_validator('rule_id', 'parameter', 'parameter_unit', 'condition', 'condition_type', 
                     'modification', 'modification_type', 'description', 'action_text', mode='before')
    @classmethod
    def set_string_defaults(cls, v):
        if v is None:
            return ""
        return str(v)
    
    @field_validator('affected_drugs', mode='before')
    @classmethod
    def set_list_defaults(cls, v):
        if v is None:
            return []
        return v
    
    @field_validator('priority', mode='before')
    @classmethod
    def set_priority_default(cls, v):
        if v is None:
            return 1
        try:
            return int(v)
        except (ValueError, TypeError):
            return 1
    
    @field_validator('check_if_already_reduced', mode='before')
    @classmethod
    def set_bool_default(cls, v):
        if v is None:
            return False
        return bool(v)


class HematologicalToxicityRule(BaseModel):
    """Rules for managing hematological toxicity"""
    toxicity_type: str = ""  # "neutropenia", "thrombocytopenia", "anemia"
    grade: Optional[int] = None  # CTCAE grade
    threshold: str = ""  # e.g., "< 0.5", "50-74"
    threshold_value: Optional[float] = None
    threshold_low: Optional[float] = None
    threshold_high: Optional[float] = None
    action: str = ""  # "delay", "reduce", "hold", "gcsf"
    delay_days: Optional[int] = None
    reduction_percent: Optional[int] = None
    check_drugs: list[str] = []
    additional_notes: str = ""
    
    @field_validator('toxicity_type', 'threshold', 'action', 'additional_notes', mode='before')
    @classmethod
    def set_string_defaults(cls, v):
        return "" if v is None else str(v)
    
    @field_validator('check_drugs', mode='before')
    @classmethod
    def set_list_defaults(cls, v):
        return [] if v is None else v


class NonHematologicalToxicityRule(BaseModel):
    """Rules for managing non-hematological toxicity like neuropathy, mucositis, etc."""
    toxicity_type: str = ""  # "motor_weakness", "peripheral_neuropathy", "gross_hematuria", etc.
    grade: Optional[int] = None
    parameter: Optional[str] = None  # Lab parameter if applicable
    threshold: Optional[str] = None
    affected_drugs: list[str] = []
    action: str = ""  # "reduce_or_omit", "hold", "consider_modification"
    action_text: str = ""
    monitoring_frequency: str = "each_cycle"
    
    @field_validator('toxicity_type', 'action', 'action_text', 'monitoring_frequency', mode='before')
    @classmethod
    def set_string_defaults(cls, v):
        return "" if v is None else str(v)
    
    @field_validator('affected_drugs', mode='before')
    @classmethod
    def set_list_defaults(cls, v):
        return [] if v is None else v


class MetabolicMonitoringRule(BaseModel):
    """Rules for metabolic monitoring (glucose, HbA1c, etc.)"""
    parameter: str = ""
    baseline_required: bool = True
    change_threshold_percent: Optional[float] = None
    action_on_change: str = "alert"
    action_text: str = ""
    
    @field_validator('parameter', 'action_on_change', 'action_text', mode='before')
    @classmethod
    def set_string_defaults(cls, v):
        return "" if v is None else str(v)


class AgeBasedModification(BaseModel):
    """Age-based dose modifications"""
    age_threshold: int = 70
    operator: str = ">"  # ">", "<", ">=", "<="
    affected_drugs: list[str] = []
    modification_type: str = "cap"  # "cap", "reduce"
    cap_dose: Optional[float] = None
    cap_unit: Optional[str] = None
    reduction_percent: Optional[int] = None
    trigger_condition: Optional[str] = None  # e.g., "cumulative_anthracycline > 300 mg/m²"
    recommendation: Optional[str] = None  # e.g., "cardioprotectant"
    cardioprotectant_drug: Optional[str] = None
    description: str = ""
    
    @field_validator('operator', 'modification_type', 'description', mode='before')
    @classmethod
    def set_string_defaults(cls, v):
        return "" if v is None else str(v)
    
    @field_validator('affected_drugs', mode='before')
    @classmethod
    def set_list_defaults(cls, v):
        return [] if v is None else v


class ReducedLimitCondition(BaseModel):
    """Condition for reduced cumulative dose limit"""
    condition: str = ""
    limit: float = 0
    unit: str = "mg/m²"
    
    @field_validator('condition', 'unit', mode='before')
    @classmethod
    def set_string_defaults(cls, v):
        return "" if v is None else str(v)


class CumulativeToxicityTracking(BaseModel):
    """Tracking cumulative drug toxicity (anthracyclines, bleomycin, etc.)"""
    drug_class: Optional[str] = None  # "anthracycline"
    drug: Optional[str] = None  # For single-drug tracking like "bleomycin"
    drugs: list[str] = []  # List of drugs in class
    standard_limit_mg_m2: Optional[float] = None
    lifetime_limit: Optional[float] = None
    limit_unit: str = "mg/m²"
    monitoring: str = ""
    reduced_limits: list[ReducedLimitCondition] = []
    warning_at_percent: Optional[float] = 80
    alert_text: str = ""
    
    @field_validator('warning_at_percent', mode='before')
    @classmethod
    def set_warning_default(cls, v):
        if v is None:
            return 80.0
        return float(v)

    @field_validator('limit_unit', 'monitoring', 'alert_text', mode='before')
    @classmethod
    def set_string_defaults(cls, v):
        return "" if v is None else str(v)
    
    @field_validator('drugs', mode='before')
    @classmethod
    def set_list_defaults(cls, v):
        return [] if v is None else v
    
    @field_validator('reduced_limits', mode='before')
    @classmethod
    def set_reduced_limits_default(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return [ReducedLimitCondition(**item) if isinstance(item, dict) else item for item in v]
        return []


class TreatmentDelayCriteria(BaseModel):
    """Criteria for when to delay treatment"""
    parameter: str = ""
    threshold: str = ""
    threshold_value: Optional[float] = None
    delay_until: str = ""
    max_delay_weeks: Optional[int] = None
    action_if_not_recovered: Optional[str] = None
    condition: Optional[str] = None  # For non-lab conditions like "active_infection"
    
    @field_validator('parameter', 'threshold', 'delay_until', mode='before')
    @classmethod
    def set_string_defaults(cls, v):
        return "" if v is None else str(v)


class BaselineRequirement(BaseModel):
    """Baseline tests required before starting protocol"""
    test: str = ""
    includes: list[str] = []
    timing: str = ""
    required: str = "true"  # "true", "false", "conditional"
    condition: Optional[str] = None
    
    @field_validator('test', 'timing', 'required', mode='before')
    @classmethod
    def set_string_defaults(cls, v):
        return "" if v is None else str(v)
    
    @field_validator('includes', mode='before')
    @classmethod
    def set_list_defaults(cls, v):
        return [] if v is None else v


class PreCycleLab(BaseModel):
    """Labs required before each cycle"""
    test: str = ""
    timing: str = ""
    required: bool = True
    
    @field_validator('test', 'timing', mode='before')
    @classmethod
    def set_string_defaults(cls, v):
        return "" if v is None else str(v)


class PostCycleMonitoring(BaseModel):
    """Post-cycle monitoring requirements"""
    test: str = ""
    timing: str = ""
    purpose: str = ""
    action_on_abnormal: str = ""
    
    @field_validator('test', 'timing', 'purpose', 'action_on_abnormal', mode='before')
    @classmethod
    def set_string_defaults(cls, v):
        return "" if v is None else str(v)


class CycleVariation(BaseModel):
    """Variations in protocol between cycles"""
    cycles: list[int] = [1]  # Which cycles this applies to, e.g., [1] or [2,3,4,5]
    cycle_range: Optional[str] = None  # e.g., "2-5", "6+"
    drugs: list[ProtocolDrug] = []
    take_home_medicines: list[ProtocolDrug] = []
    special_instructions: list[str] = []
    
    @field_validator('cycles', mode='before')
    @classmethod
    def set_cycles_default(cls, v):
        if v is None or v == []:
            return [1]
        return v
    
    @field_validator('drugs', 'take_home_medicines', 'special_instructions', mode='before')
    @classmethod
    def set_list_defaults(cls, v):
        if v is None:
            return []
        return v


class Toxicity(BaseModel):
    """Drug toxicity information"""
    drug_id: str = ""
    adverse_effects: list[str] = []
    
    @field_validator('drug_id', mode='before')
    @classmethod
    def set_drug_id_default(cls, v):
        if v is None:
            return ""
        return str(v)
    
    @field_validator('adverse_effects', mode='before')
    @classmethod
    def set_effects_default(cls, v):
        if v is None:
            return []
        return v


class Protocol(BaseModel):
    """
    Complete chemotherapy protocol with comprehensive automation support.
    Matches the enhanced Gemini extraction for RCHOP-level automation.
    """
    id: str = Field(..., alias="protocol_id")
    name: str = Field(..., alias="protocol_name")
    code: str = Field(..., alias="protocol_code")  # Short code like "RCHOP21"
    full_name: str = ""
    indication: str = ""
    cycle_length_days: int = 21
    total_cycles: int = 6
    version: str = "1.0"
    treatment_intent: str = ""  # curative, palliative, maintenance, consolidation
    
    # Core drugs in the regimen
    drugs: list[ProtocolDrug] = []
    
    # Pre-medications
    pre_medications: list[ProtocolDrug] = []
    
    # Take-home medicines
    take_home_medicines: list[ProtocolDrug] = []
    
    # Rescue medications (PRN)
    rescue_medications: list[ProtocolDrug] = []
    
    # Cycle-specific variations
    cycle_variations: list[CycleVariation] = []
    
    # Dose modification rules (lab-based: GFR, bilirubin, etc.)
    dose_modifications: list[DoseModificationRule] = []
    
    # Hematological toxicity rules (neutropenia, thrombocytopenia)
    hematological_toxicity_rules: list[HematologicalToxicityRule] = []
    
    # Non-hematological toxicity rules (neuropathy, hematuria, etc.)
    non_hematological_toxicity_rules: list[NonHematologicalToxicityRule] = []
    
    # Metabolic monitoring (HbA1c, glucose changes)
    metabolic_monitoring: list[MetabolicMonitoringRule] = []
    
    # Age-based modifications (elderly caps, young patient cardioprotection)
    age_based_modifications: list[AgeBasedModification] = []
    
    # Cumulative toxicity tracking (anthracyclines, bleomycin)
    cumulative_toxicity_tracking: list[CumulativeToxicityTracking] = []
    
    # Treatment delay criteria
    treatment_delay_criteria: list[TreatmentDelayCriteria] = []
    
    # Baseline requirements
    baseline_requirements: list[BaselineRequirement] = []
    
    # Pre-cycle labs
    pre_cycle_labs: list[PreCycleLab] = []
    
    # Post-cycle monitoring
    post_cycle_monitoring: list[PostCycleMonitoring] = []
    
    # Toxicity information
    toxicities: list[Toxicity] = []
    
    # Monitoring requirements (legacy - string list)
    monitoring: list[str] = []
    
    # Warnings and special instructions
    warnings: list[str] = []
    
    # Source PDF
    source_file: Optional[str] = None

    # AI-extraction flag — True for Gemini-parsed protocols, False for hardcoded
    is_ai_generated: bool = False

    # Fields the clinician MUST fill in for this specific protocol
    # Keys are PatientData field names; values are reasons/explanations
    # Set by Gemini extraction; hardcoded protocols can override
    required_patient_fields: dict[str, str] = {}
    
    # Handle None values from Gemini parsing
    @field_validator('cycle_length_days', 'total_cycles', mode='before')
    @classmethod
    def set_numeric_defaults(cls, v, info):
        if v is None:
            return 21 if info.field_name == 'cycle_length_days' else 6
        try:
            return int(v)
        except (ValueError, TypeError):
            return 21 if info.field_name == 'cycle_length_days' else 6
    
    @field_validator('full_name', 'indication', 'version', 'treatment_intent', mode='before')
    @classmethod  
    def set_string_defaults(cls, v):
        if v is None:
            return ""
        return str(v)
    
    @field_validator('drugs', 'pre_medications', 'take_home_medicines', 'rescue_medications',
                     'cycle_variations', 'dose_modifications', 'toxicities', 'monitoring', 'warnings',
                     'hematological_toxicity_rules', 'non_hematological_toxicity_rules',
                     'metabolic_monitoring', 'age_based_modifications', 'cumulative_toxicity_tracking',
                     'treatment_delay_criteria', 'baseline_requirements', 'pre_cycle_labs',
                     'post_cycle_monitoring',
                     mode='before')
    @classmethod
    def set_list_defaults(cls, v):
        if v is None:
            return []
        return v

    @field_validator('required_patient_fields', mode='before')
    @classmethod
    def set_required_fields_default(cls, v):
        if v is None:
            return {}
        if isinstance(v, dict):
            return v
        return {}
    
    class Config:
        use_enum_values = True
        populate_by_name = True


# ============= REQUEST/RESPONSE MODELS =============

class PatientData(BaseModel):
    """
    Patient information for dose calculation.
    
    SAFETY CRITICAL: All lab values are MANDATORY per "No labs, no chemo" principle.
    BSA is capped at 2.0 m² for obese patients per ASCO guidelines.
    """
    # Demographics
    weight_kg: float = Field(..., gt=0, le=500, description="Patient weight in kg")
    height_cm: float = Field(..., gt=0, le=300, description="Patient height in cm")
    age_years: int = Field(..., ge=0, le=120, description="Patient age in years - REQUIRED for dosing")
    bsa_m2: Optional[float] = Field(None, description="BSA in m², calculated if not provided")
    
    # Performance status - CRITICAL for treatment decisions
    performance_status: ECOGPerformanceStatus = Field(
        ..., 
        description="ECOG Performance Status (0-4). ECOG 3-4 requires dose reduction or treatment contraindication."
    )
    
    # Unit system for lab values - prevents 10-100x dosing errors
    lab_unit_system: LabUnitSystem = Field(
        default=LabUnitSystem.SI, 
        description="SI (UK/International) or Conventional (US) units. CRITICAL for correct interpretation."
    )
    
    # MANDATORY Lab values - "No labs, no chemo" principle
    neutrophils: float = Field(
        ...,
        description="Neutrophils x10⁹/L - MANDATORY. Treatment contraindicated if <0.5"
    )
    platelets: float = Field(
        ...,
        description="Platelets x10⁹/L - MANDATORY. Treatment contraindicated if <50"
    )
    hemoglobin: float = Field(
        ...,
        description="Hemoglobin g/dL - MANDATORY"
    )
    creatinine_clearance: float = Field(
        ...,
        description="CrCl in ml/min (Cockcroft-Gault) - MANDATORY for nephrotoxic drugs"
    )
    bilirubin: float = Field(
        ...,
        description="Bilirubin in µmol/L (SI) or mg/dL (Conventional) - MANDATORY for hepatotoxic drugs"
    )
    
    # Optional but recommended lab values
    ast: Optional[float] = Field(None, ge=0, description="AST in units/L")
    alt: Optional[float] = Field(None, ge=0, description="ALT in units/L")
    alp: Optional[float] = Field(None, ge=0, description="ALP in units/L")
    wbc: Optional[float] = Field(None, ge=0, description="White blood cell count x10⁹/L")
    lymphocytes: Optional[float] = Field(None, ge=0, description="Lymphocyte count x10⁹/L")
    creatinine: Optional[float] = Field(None, ge=0, description="Serum creatinine in µmol/L")
    
    # Allergy checking - CRITICAL for safety
    known_allergies: list[str] = Field(
        default=[],
        description="List of known drug allergies (e.g., ['platinum', 'rituximab']). Cross-checked against protocol drugs."
    )
    
    # Prior treatment for cumulative toxicity tracking
    prior_anthracycline_dose_mg_m2: Optional[float] = Field(
        None, ge=0,
        description="Cumulative prior anthracycline dose in mg/m² (doxorubicin equivalent). Max lifetime: 450-550 mg/m²"
    )
    prior_bleomycin_units: Optional[float] = Field(
        None, ge=0,
        description="Cumulative prior bleomycin dose in units. Max lifetime: 400,000 units"
    )
    
    # Cardiac history for anthracycline limits
    prior_cardiac_history: bool = Field(
        default=False,
        description="History of cardiac disease - reduces anthracycline limit to 400 mg/m²"
    )
    prior_mediastinal_radiation: bool = Field(
        default=False,
        description="Prior mediastinal radiation - reduces anthracycline limit to 350 mg/m²"
    )
    
    # Metabolic baseline values (for comparison with post-cycle values)
    baseline_hba1c: Optional[float] = Field(None, description="Baseline HbA1c (%)")
    baseline_glucose: Optional[float] = Field(None, description="Baseline fasting glucose (mmol/L)")
    
    # Current/Post-cycle metabolic values
    current_hba1c: Optional[float] = Field(None, description="Current HbA1c (%)")
    current_glucose: Optional[float] = Field(None, description="Current fasting glucose (mmol/L)")
    
    # Non-hematological toxicities (checkboxes for common toxicities)
    has_gross_hematuria: bool = Field(default=False, description="Gross hematuria present")
    has_motor_weakness: bool = Field(default=False, description="Motor weakness/neuropathy present")
    has_peripheral_neuropathy: bool = Field(default=False, description="Peripheral neuropathy present")
    has_mucositis: bool = Field(default=False, description="Mucositis present")
    has_skin_toxicity: bool = Field(default=False, description="Skin toxicity present")
    peripheral_neuropathy_grade: Optional[int] = Field(None, ge=0, le=4, description="CTCAE grade of peripheral neuropathy")
    
    # Pregnancy/fertility
    pregnancy_status: Optional[Literal["not_pregnant", "pregnant", "unknown", "not_applicable"]] = Field(
        None,
        description="Pregnancy status - CRITICAL for teratogenic drugs"
    )

    # ---- Disease characterisation ----
    histology: Optional[str] = Field(None, description="Tumour histology / diagnosis (e.g., DLBCL, AML, CLL)")
    disease_stage: Optional[str] = Field(None, description="Disease stage (e.g., Ann Arbor IV, RAI 3)")
    ct_result: Optional[str] = Field(None, description="CT scan result summary / findings")
    ldh: Optional[float] = Field(None, ge=0, description="LDH in U/L - elevated in high-grade lymphoma/AML")
    esr: Optional[float] = Field(None, ge=0, description="ESR in mm/hr")
    urate: Optional[float] = Field(None, ge=0, description="Serum urate in µmol/L")
    calcium: Optional[float] = Field(None, ge=0, description="Corrected serum calcium in mmol/L")
    vitamin_d: Optional[float] = Field(None, ge=0, description="25-OH Vitamin D in nmol/L")
    magnesium: Optional[float] = Field(None, ge=0, description="Serum magnesium in mmol/L")
    beta2_microglobulin: Optional[float] = Field(None, ge=0, description="Beta-2 microglobulin in mg/L — prognostic in lymphoma/myeloma")
    immunoglobulins: Optional[str] = Field(None, description="Immunoglobulin levels summary (e.g., IgG 5.2, IgA 0.8, IgM 0.3)")

    # ---- Virology panel ----
    hep_b_surface_antigen: Optional[Literal["positive", "negative", "unknown"]] = Field(None, description="HBsAg")
    hep_b_core_antibody: Optional[Literal["positive", "negative", "unknown"]] = Field(None, description="HBcAb — indicates prior HBV exposure; reactivation risk with rituximab")
    hep_c_antibody: Optional[Literal["positive", "negative", "unknown"]] = Field(None, description="HCV antibody")
    hiv_status: Optional[Literal["positive", "negative", "unknown"]] = Field(None, description="HIV status — affects immunosuppression risk")
    htlv1_status: Optional[Literal["positive", "negative", "unknown"]] = Field(None, description="HTLV-1 — associated with adult T-cell lymphoma")
    ebv_status: Optional[Literal["positive", "negative", "unknown"]] = Field(None, description="EBV serology")
    cmv_status: Optional[Literal["positive", "negative", "unknown"]] = Field(None, description="CMV serology — relevant for immunosuppressed patients")
    vzv_status: Optional[Literal["positive", "negative", "unknown"]] = Field(None, description="VZV serology — determines aciclovir prophylaxis need")

    # ---- Metabolic / endocrine ----
    g6pd_status: Optional[Literal["normal", "deficient", "unknown"]] = Field(None, description="G6PD enzyme status — critical before rasburicase")
    smoker: Optional[bool] = Field(None, description="Current or ex-smoker — affects bleomycin toxicity risk")
    lung_function_fev1: Optional[float] = Field(None, ge=0, description="FEV1 % predicted — relevant for bleomycin")
    heart_disease: Optional[bool] = Field(None, description="Pre-existing cardiac disease")
    lvef_percent: Optional[float] = Field(None, ge=0, le=100, description="Left ventricular ejection fraction % — baseline before anthracyclines")

    # ---- Post-cycle tracking (cycle-by-cycle outcomes) ----
    post_cycle_gfr: Optional[float] = Field(None, ge=0, description="GFR post last cycle (ml/min/1.73m²)")
    post_cycle_bilirubin: Optional[float] = Field(None, ge=0, description="Bilirubin post last cycle (µmol/L)")
    post_cycle_neutrophils: Optional[float] = Field(None, ge=0, description="Neutrophil nadir post last cycle (x10⁹/L)")
    post_cycle_platelets: Optional[float] = Field(None, ge=0, description="Platelet nadir post last cycle (x10⁹/L)")
    post_cycle_hba1c: Optional[float] = Field(None, description="HbA1c post last cycle (%)")
    post_cycle_glucose: Optional[float] = Field(None, description="Fasting glucose post last cycle (mmol/L)")
    post_cycle_motor_weakness: Optional[bool] = Field(None, description="Motor weakness/neuropathy post last cycle")
    post_cycle_gross_hematuria: Optional[bool] = Field(None, description="Gross haematuria post last cycle")

    # ---- Cycle completion tracking ----
    cycles_completed: Optional[int] = Field(None, ge=0, description="Number of cycles completed so far")

    # ---- Active infection / fitness for treatment ----
    active_infection: Optional[bool] = Field(None, description="Active infection or fever present — treatment must be delayed")

    # ---- Blast count (blinatumomab pre-phase assessment) ----
    peripheral_blast_percent: Optional[float] = Field(None, ge=0, le=100, description="Peripheral blood blast % — if >15% pre-phase corticosteroid required before blinatumomab")
    bone_marrow_blast_percent: Optional[float] = Field(None, ge=0, le=100, description="Bone marrow blast % — if >50% pre-phase corticosteroid required before blinatumomab")

    # ---- Tumor lysis risk ----
    tls_risk: Optional[Literal["low", "intermediate", "high"]] = Field(None, description="Tumor lysis syndrome risk assessment")
    hbv_prophylaxis_started: Optional[bool] = Field(None, description="HBV antiviral prophylaxis started (required if HBsAg+ or HBcAb+ with rituximab)")

    @field_validator('neutrophils')
    @classmethod
    def validate_neutrophils(cls, v: float) -> float:
        """Accept any non-negative value — engine generates clinical warnings for low counts."""
        if v < 0:
            raise ValueError("Neutrophils cannot be negative")
        if v > 100:
            raise ValueError("Neutrophils > 100 x10⁹/L is physiologically unlikely. Please verify input.")
        return v

    @field_validator('platelets')
    @classmethod
    def validate_platelets(cls, v: float) -> float:
        """Accept any non-negative value — engine generates clinical warnings for low counts."""
        if v < 0:
            raise ValueError("Platelets cannot be negative")
        if v > 2000:
            raise ValueError("Platelets > 2000 x10⁹/L is physiologically unlikely. Please verify input.")
        return v

    @field_validator('creatinine_clearance')
    @classmethod
    def validate_renal_function(cls, v: float) -> float:
        """Accept any non-negative value — engine applies dose reductions and warnings for low CrCl."""
        if v < 0:
            raise ValueError("Creatinine clearance cannot be negative")
        if v > 250:
            raise ValueError("CrCl > 250 ml/min is physiologically unlikely. Please verify input.")
        return v

    @field_validator('bilirubin')
    @classmethod
    def validate_bilirubin(cls, v: float) -> float:
        """Validate bilirubin"""
        if v < 0:
            raise ValueError("Bilirubin cannot be negative")
        if v > 1000: # Very high, but theoretically possible in severe failure, though likely error
             raise ValueError("Bilirubin > 1000 µmol/L is extremely high. Please verify input.")
        return v

    @field_validator('weight_kg')
    @classmethod
    def validate_weight(cls, v: float) -> float:
        if v < 10:
             raise ValueError("Weight < 10kg is not supported by this adult protocol system.")
        if v > 400:
             raise ValueError("Weight > 400kg exceeds system validation limits. Please verify input.")
        return v

    @field_validator('height_cm')
    @classmethod
    def validate_height(cls, v: float) -> float:
        if v < 50:
             raise ValueError("Height < 50cm is not supported.")
        if v > 250:
             raise ValueError("Height > 250cm exceeds normal physiological limits. Please verify input.")
        return v

    @computed_field
    @property
    def calculated_bsa(self) -> float:
        """
        Calculate BSA using Mosteller formula if not provided.
        
        SAFETY: BSA is capped at 2.0 m² for obese patients per ASCO guidelines
        to prevent overdosing.
        """
        if self.bsa_m2:
            raw_bsa = self.bsa_m2
        else:
            raw_bsa = math.sqrt((self.height_cm * self.weight_kg) / 3600)
        
        # Validate physiological bounds
        if raw_bsa < BSA_MIN:
            raise ValueError(f"BSA {raw_bsa:.2f} m² is below physiological minimum of {BSA_MIN} m²")
        if raw_bsa > BSA_MAX:
            raise ValueError(f"BSA {raw_bsa:.2f} m² exceeds physiological maximum of {BSA_MAX} m²")
        
        return raw_bsa
    
    @computed_field
    @property
    def capped_bsa(self) -> float:
        """
        BSA capped at 2.0 m² for obese patients per ASCO guidelines.
        
        Use this for dose calculations, not calculated_bsa.
        """
        return min(self.calculated_bsa, BSA_CAP_OBESE)
    
    @computed_field
    @property
    def bsa_was_capped(self) -> bool:
        """True if BSA was capped due to obesity"""
        return self.calculated_bsa > BSA_CAP_OBESE
    
    @computed_field
    @property
    def requires_delay(self) -> bool:
        """True if treatment should be delayed based on lab values"""
        return (
            self.neutrophils < NEUTROPHIL_DELAY_THRESHOLD or 
            self.platelets < PLATELET_DELAY_THRESHOLD
        )
    
    @computed_field
    @property
    def delay_reasons(self) -> list[str]:
        """Reasons treatment should be delayed"""
        reasons = []
        if self.neutrophils < NEUTROPHIL_DELAY_THRESHOLD:
            reasons.append(f"Neutrophils {self.neutrophils} x10⁹/L < {NEUTROPHIL_DELAY_THRESHOLD}")
        if self.platelets < PLATELET_DELAY_THRESHOLD:
            reasons.append(f"Platelets {self.platelets} < {PLATELET_DELAY_THRESHOLD}")
        return reasons
    
    @computed_field
    @property
    def elderly_patient(self) -> bool:
        """True if patient is elderly (>=70 years) and may require dose reduction"""
        return self.age_years >= 70
    
    @computed_field
    @property
    def poor_performance_status(self) -> bool:
        """True if ECOG 3-4, requiring dose modification or treatment reconsideration"""
        return self.performance_status >= ECOGPerformanceStatus.LIMITED_SELFCARE
    
    def has_allergy_to(self, drug_name: str, drug_aliases: list[str] = []) -> bool:
        """Check if patient has documented allergy to a drug"""
        all_names = [drug_name.lower()] + [a.lower() for a in drug_aliases]
        for allergy in self.known_allergies:
            allergy_lower = allergy.lower()
            for name in all_names:
                if allergy_lower in name or name in allergy_lower:
                    return True
        return False


class DrugOverride(BaseModel):
    """Manual override for a specific drug"""
    dose_percent: Optional[int] = Field(None, ge=0, le=100)
    omit: bool = False
    custom_dose: Optional[float] = None


class CustomRegimenDrug(BaseModel):
    """A drug in a custom-built regimen (from FlexibleProtocolBuilder)"""
    drug_name: str
    dose: float = Field(..., gt=0)
    dose_unit: str = "mg/m²"
    route: str = "IV infusion"
    days: list[int] = [1]
    duration_minutes: Optional[int] = None
    diluent: Optional[str] = None
    diluent_volume_ml: Optional[int] = None
    frequency: Optional[str] = None
    special_instructions: Optional[str] = None
    max_dose: Optional[float] = None
    prn: bool = False


class CustomRegimenRequest(BaseModel):
    """Request to generate a protocol from a fully custom drug list"""
    patient: PatientData
    drugs: list[CustomRegimenDrug] = Field(..., min_length=1)
    regimen_name: str = "Custom Regimen"
    cycle_number: int = Field(1, ge=1)
    cycle_length_days: int = Field(21, ge=1, le=365)
    total_cycles: int = Field(6, ge=1)


class ProtocolRequest(BaseModel):
    """Request to generate a protocol"""
    protocol_code: str
    patient: PatientData
    cycle_number: int = Field(1, ge=1, description="Current cycle number")

    # Drug selection
    excluded_drugs: list[str] = []  # Drug IDs to exclude
    included_drugs: Optional[list[str]] = None  # If specified, only include these

    # Include/exclude categories
    include_premeds: bool = True
    include_antiemetics: bool = True
    include_take_home: bool = True
    include_rescue: bool = True

    # Manual overrides
    drug_overrides: dict[str, DrugOverride] = {}

    # Treatment start date (ISO format YYYY-MM-DD) — used for bag-change schedules
    treatment_start_date: Optional[str] = None


class CalculatedDose(BaseModel):
    """Calculated dose for a drug"""
    drug_id: str
    drug_name: str
    original_dose: float
    original_dose_unit: str
    calculated_dose: float
    calculated_dose_unit: str
    route: str
    days: list[int]
    duration_minutes: Optional[int] = None
    diluent: Optional[str] = None
    diluent_volume_ml: Optional[int] = None
    timing: Optional[str] = None
    frequency: Optional[str] = None
    special_instructions: Optional[str] = None
    prn: bool = False

    # Modification tracking
    dose_modified: bool = False
    modification_reason: Optional[str] = None
    modification_percent: Optional[int] = None

    # Banding info (for dose banding)
    banded_dose: Optional[float] = None

    # Pre-cap calculated dose (set when a max dose cap was applied, e.g. vincristine 2mg cap)
    # This preserves the true BSA-based calculation so the banded display shows e.g. "2mg (capped; calculated: 2.8mg)"
    uncapped_calculated_dose: Optional[float] = None

    @property
    def duration_human(self) -> Optional[str]:
        """Human-readable duration string (e.g. '2 hr', '7 days', '30 mins')"""
        if not self.duration_minutes:
            return None
        mins = self.duration_minutes
        if mins < 60:
            return f"{mins} mins"
        hours = mins / 60
        if hours < 24:
            h = int(hours)
            m = round((hours - h) * 60)
            return f"{h} hr {m} mins" if m else f"{h} hr"
        days = hours / 24
        is_round_days = abs(days - round(days)) < 0.05
        if hours < 48 or not is_round_days:
            h = int(hours)
            m = round((hours - h) * 60)
            return f"{h} hr {m} mins" if m else f"{h} hr"
        return f"{round(days)} days"

    class Config:
        use_enum_values = True


class Warning(BaseModel):
    """Warning or alert for the protocol"""
    level: Literal["info", "warning", "critical"]
    message: str
    drug_id: Optional[str] = None


class BlinatumomabBagEntry(BaseModel):
    """One bag in a blinatumomab continuous infusion schedule."""
    bag_number: int
    date_start: str          # e.g. "21.08.25"
    date_end: str            # e.g. "25.08.25"
    dose_mcg_per_day: float  # 9 or 28
    total_dose_mcg: float    # e.g. 38.5 (1 vial) or 115.5 (3 vials)
    vials: int               # number of 38.5mcg vials
    ns_volume_ml: float      # NS added to bag (e.g. 275 or 269)
    stabilizer_volume_ml: float  # stabilizer added (5.5ml)
    total_volume_ml: float   # total dilution volume (283.5ml)
    rate_ml_per_hr: float    # infusion rate (3ml/hr)
    duration_hours: int      # 96


class ProtocolResponse(BaseModel):
    """
    Generated protocol response with full audit trail.

    SAFETY: This response includes treatment delay recommendations,
    BSA capping information, and audit trail for regulatory compliance.
    """
    protocol_id: str
    protocol_name: str
    protocol_code: str
    indication: str
    cycle_number: int
    cycle_length_days: int
    total_cycles: int
    
    # Patient info (enhanced for safety)
    patient_bsa: float  # Capped BSA used for calculations
    patient_bsa_actual: Optional[float] = None  # Actual calculated BSA before capping
    patient_bsa_capped: bool = False  # True if BSA was capped for obesity
    patient_weight: float
    patient_age: Optional[int] = None
    patient_performance_status: Optional[int] = None
    
    # Calculated doses
    pre_medications: list[CalculatedDose]
    chemotherapy_drugs: list[CalculatedDose]
    take_home_medicines: list[CalculatedDose]
    rescue_medications: list[CalculatedDose]
    
    # Monitoring and instructions
    monitoring_requirements: list[str]
    special_instructions: list[str]
    
    # Warnings (categorized by severity)
    warnings: list[Warning]
    
    # Modifications applied
    dose_modifications_applied: list[str]
    
    # Safety flags
    treatment_delay_recommended: bool = False
    delay_reasons: list[str] = []
    # Hard stop: neutrophils <0.5 or platelets <50 — ALL chemotherapy withheld, no prescriber override
    treatment_absolutely_contraindicated: bool = False
    
    # Audit trail (required for regulatory compliance)
    generated_at: Optional[str] = None  # ISO timestamp
    protocol_version: Optional[str] = None
    
    # AI-generation flag — frontend uses this to gate verification checkbox
    is_ai_generated: bool = False

    # Blinatumomab bag-change schedule (populated only for blinatumomab protocols)
    blinatumomab_bag_schedule: Optional[list[BlinatumomabBagEntry]] = None

    # Disclaimer
    disclaimer: str = (
        "⚠️ CLINICAL DECISION SUPPORT ONLY: This protocol is generated by SOPHIA for decision support purposes. "
        "It does NOT replace clinical judgment. Independent verification by a qualified prescriber and pharmacist "
        "is REQUIRED before administration. SOPHIA is not a licensed medical device and has not undergone "
        "regulatory approval for clinical use. Use at your own risk."
    )


# ============= SEARCH/LISTING MODELS =============

class ProtocolSummary(BaseModel):
    """Summary of a protocol for listing"""
    id: str
    code: str
    name: str
    indication: str
    drugs: list[str]  # List of drug names
    cycle_length_days: int
    total_cycles: int


class DrugSummary(BaseModel):
    """Summary of a drug"""
    id: str
    name: str
    category: str
    protocols_count: int
