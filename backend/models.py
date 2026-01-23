"""
Chemotherapy Protocol Engine - Data Models
NHS Lymphoma Protocols
"""

from pydantic import BaseModel, Field, computed_field
from typing import Optional, Literal
from enum import Enum
import math


class RouteOfAdministration(str, Enum):
    IV_BOLUS = "IV bolus"
    IV_INFUSION = "IV infusion"
    ORAL = "Oral"
    SC = "Subcutaneous"
    IM = "Intramuscular"
    NEBULISED = "Nebulised"
    TOPICAL = "Topical"


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
    administration_order: int = 0
    is_core_drug: bool = True  # False for pre-meds, supportive care
    is_optional: bool = False
    max_dose: Optional[float] = None
    max_dose_unit: Optional[str] = None
    timing: Optional[str] = None  # e.g., "30 mins before rituximab"
    frequency: Optional[str] = None  # e.g., "twice daily", "three times a day"
    special_instructions: Optional[str] = None
    prn: bool = False  # As needed
    
    class Config:
        use_enum_values = True


class DoseModificationRule(BaseModel):
    """Rules for dose modification based on lab values"""
    parameter: str  # e.g., "neutrophils", "bilirubin", "creatinine_clearance"
    condition: str  # e.g., "< 1.0", "20-50", "> 85"
    affected_drugs: list[str]  # Drug IDs affected
    modification: str  # e.g., "reduce_50", "omit", "delay"
    modification_percent: Optional[int] = None
    description: str


class CycleVariation(BaseModel):
    """Variations in protocol between cycles"""
    cycles: list[int]  # Which cycles this applies to, e.g., [1] or [2,3,4,5]
    cycle_range: Optional[str] = None  # e.g., "2-5", "6+"
    drugs: list[ProtocolDrug]
    take_home_medicines: list[ProtocolDrug] = []
    special_instructions: list[str] = []


class Toxicity(BaseModel):
    """Drug toxicity information"""
    drug_id: str
    adverse_effects: list[str]


class Protocol(BaseModel):
    """Complete chemotherapy protocol"""
    id: str
    name: str
    code: str  # Short code like "RCHOP21"
    full_name: str
    indication: str
    cycle_length_days: int
    total_cycles: int
    version: str
    
    # Core drugs in the regimen
    drugs: list[ProtocolDrug]
    
    # Pre-medications
    pre_medications: list[ProtocolDrug] = []
    
    # Take-home medicines
    take_home_medicines: list[ProtocolDrug] = []
    
    # Rescue medications (PRN)
    rescue_medications: list[ProtocolDrug] = []
    
    # Cycle-specific variations
    cycle_variations: list[CycleVariation] = []
    
    # Dose modification rules
    dose_modifications: list[DoseModificationRule] = []
    
    # Toxicity information
    toxicities: list[Toxicity] = []
    
    # Monitoring requirements
    monitoring: list[str] = []
    
    # Warnings and special instructions
    warnings: list[str] = []
    
    # Source PDF
    source_file: Optional[str] = None
    
    class Config:
        use_enum_values = True


# ============= REQUEST/RESPONSE MODELS =============

class PatientData(BaseModel):
    """Patient information for dose calculation"""
    weight_kg: float = Field(..., gt=0, description="Patient weight in kg")
    height_cm: float = Field(..., gt=0, description="Patient height in cm")
    bsa_m2: Optional[float] = Field(None, description="BSA in m², calculated if not provided")
    
    # Lab values for dose modifications
    creatinine_clearance: Optional[float] = Field(None, ge=0, description="CrCl in ml/min")
    bilirubin: Optional[float] = Field(None, ge=0, description="Bilirubin in µmol/L")
    ast: Optional[float] = Field(None, ge=0, description="AST in units/L")
    alt: Optional[float] = Field(None, ge=0, description="ALT in units/L")
    neutrophils: Optional[float] = Field(None, ge=0, description="Neutrophils x10⁹/L")
    platelets: Optional[float] = Field(None, ge=0, description="Platelets x10⁹/L")
    hemoglobin: Optional[float] = Field(None, ge=0, description="Hemoglobin g/dL")
    
    @computed_field
    @property
    def calculated_bsa(self) -> float:
        """Calculate BSA using Mosteller formula if not provided"""
        if self.bsa_m2:
            return self.bsa_m2
        return math.sqrt((self.height_cm * self.weight_kg) / 3600)


class DrugOverride(BaseModel):
    """Manual override for a specific drug"""
    dose_percent: Optional[int] = Field(None, ge=0, le=100)
    omit: bool = False
    custom_dose: Optional[float] = None


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
    
    class Config:
        use_enum_values = True


class Warning(BaseModel):
    """Warning or alert for the protocol"""
    level: Literal["info", "warning", "critical"]
    message: str
    drug_id: Optional[str] = None


class ProtocolResponse(BaseModel):
    """Generated protocol response"""
    protocol_id: str
    protocol_name: str
    protocol_code: str
    indication: str
    cycle_number: int
    cycle_length_days: int
    total_cycles: int
    
    # Patient info
    patient_bsa: float
    patient_weight: float
    
    # Calculated doses
    pre_medications: list[CalculatedDose]
    chemotherapy_drugs: list[CalculatedDose]
    take_home_medicines: list[CalculatedDose]
    rescue_medications: list[CalculatedDose]
    
    # Monitoring and instructions
    monitoring_requirements: list[str]
    special_instructions: list[str]
    
    # Warnings
    warnings: list[Warning]
    
    # Modifications applied
    dose_modifications_applied: list[str]


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
