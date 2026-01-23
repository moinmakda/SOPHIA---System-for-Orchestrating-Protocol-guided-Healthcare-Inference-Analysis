"""
Chemotherapy Protocol Engine - Core Logic
Handles dose calculations, modifications, and drug selection
"""

from typing import Optional
import re
from models import (
    Protocol, ProtocolDrug, PatientData, ProtocolRequest, ProtocolResponse,
    CalculatedDose, Warning, DoseModificationRule, DoseUnit, CycleVariation
)


class ProtocolEngine:
    """Engine for generating personalized chemotherapy protocols"""
    
    def __init__(self, protocols: dict[str, Protocol]):
        self.protocols = protocols
    
    def get_protocol(self, code: str) -> Optional[Protocol]:
        """Get protocol by code (case-insensitive)"""
        code_upper = code.upper().replace(" ", "").replace("-", "")
        for p in self.protocols.values():
            if p.code.upper().replace(" ", "").replace("-", "") == code_upper:
                return p
        return None
    
    def generate_protocol(self, request: ProtocolRequest) -> ProtocolResponse:
        """Generate a personalized protocol based on request"""
        
        protocol = self.get_protocol(request.protocol_code)
        if not protocol:
            raise ValueError(f"Protocol not found: {request.protocol_code}")
        
        patient = request.patient
        bsa = patient.calculated_bsa
        warnings: list[Warning] = []
        modifications_applied: list[str] = []
        
        # Get cycle-specific drugs
        cycle_drugs, cycle_take_home, cycle_instructions = self._get_cycle_specific_content(
            protocol, request.cycle_number
        )
        
        # Calculate doses for core drugs
        chemo_doses = []
        for drug in cycle_drugs:
            if self._should_include_drug(drug, request):
                calc_dose, drug_warnings, mods = self._calculate_dose(
                    drug, patient, bsa, request, protocol.dose_modifications
                )
                if calc_dose:
                    chemo_doses.append(calc_dose)
                    warnings.extend(drug_warnings)
                    modifications_applied.extend(mods)
        
        # Calculate pre-medication doses
        premed_doses = []
        if request.include_premeds:
            for drug in protocol.pre_medications:
                if self._should_include_drug(drug, request):
                    calc_dose, drug_warnings, mods = self._calculate_dose(
                        drug, patient, bsa, request, []
                    )
                    if calc_dose:
                        premed_doses.append(calc_dose)
                        warnings.extend(drug_warnings)
        
        # Calculate take-home medicine doses
        take_home_doses = []
        if request.include_take_home:
            for drug in cycle_take_home:
                if self._should_include_drug(drug, request):
                    calc_dose, drug_warnings, mods = self._calculate_dose(
                        drug, patient, bsa, request, []
                    )
                    if calc_dose:
                        take_home_doses.append(calc_dose)
                        warnings.extend(drug_warnings)
        
        # Calculate rescue medication doses
        rescue_doses = []
        if request.include_rescue:
            for drug in protocol.rescue_medications:
                if self._should_include_drug(drug, request):
                    calc_dose, drug_warnings, mods = self._calculate_dose(
                        drug, patient, bsa, request, []
                    )
                    if calc_dose:
                        rescue_doses.append(calc_dose)
                        warnings.extend(drug_warnings)
        
        # Add standard warnings
        warnings.extend(self._generate_standard_warnings(patient, protocol))
        
        # Combine special instructions
        all_instructions = protocol.warnings + cycle_instructions
        
        return ProtocolResponse(
            protocol_id=protocol.id,
            protocol_name=protocol.name,
            protocol_code=protocol.code,
            indication=protocol.indication,
            cycle_number=request.cycle_number,
            cycle_length_days=protocol.cycle_length_days,
            total_cycles=protocol.total_cycles,
            patient_bsa=round(bsa, 2),
            patient_weight=patient.weight_kg,
            pre_medications=premed_doses,
            chemotherapy_drugs=chemo_doses,
            take_home_medicines=take_home_doses,
            rescue_medications=rescue_doses,
            monitoring_requirements=protocol.monitoring,
            special_instructions=all_instructions,
            warnings=warnings,
            dose_modifications_applied=modifications_applied
        )
    
    def _get_cycle_specific_content(
        self, protocol: Protocol, cycle_number: int
    ) -> tuple[list[ProtocolDrug], list[ProtocolDrug], list[str]]:
        """Get drugs and instructions specific to the cycle number"""
        
        # Check for cycle-specific variations
        for variation in protocol.cycle_variations:
            if cycle_number in variation.cycles:
                return (
                    variation.drugs,
                    variation.take_home_medicines,
                    variation.special_instructions
                )
            if variation.cycle_range:
                if self._cycle_in_range(cycle_number, variation.cycle_range):
                    return (
                        variation.drugs,
                        variation.take_home_medicines,
                        variation.special_instructions
                    )
        
        # Default: use main protocol drugs
        return (protocol.drugs, protocol.take_home_medicines, [])
    
    def _cycle_in_range(self, cycle: int, range_str: str) -> bool:
        """Check if cycle number is in range like '2-5' or '6+'"""
        if '+' in range_str:
            start = int(range_str.replace('+', ''))
            return cycle >= start
        if '-' in range_str:
            parts = range_str.split('-')
            return int(parts[0]) <= cycle <= int(parts[1])
        return cycle == int(range_str)
    
    def _should_include_drug(self, drug: ProtocolDrug, request: ProtocolRequest) -> bool:
        """Check if a drug should be included based on request filters"""
        
        # Check excluded drugs
        if drug.drug_id in request.excluded_drugs:
            return False
        if drug.drug_name.lower() in [d.lower() for d in request.excluded_drugs]:
            return False
        
        # Check included drugs (whitelist)
        if request.included_drugs is not None:
            drug_in_list = (
                drug.drug_id in request.included_drugs or
                drug.drug_name.lower() in [d.lower() for d in request.included_drugs]
            )
            if not drug_in_list:
                return False
        
        # Check if drug is overridden to be omitted
        override = request.drug_overrides.get(drug.drug_id) or request.drug_overrides.get(drug.drug_name)
        if override and override.omit:
            return False
        
        return True
    
    def _calculate_dose(
        self,
        drug: ProtocolDrug,
        patient: PatientData,
        bsa: float,
        request: ProtocolRequest,
        modification_rules: list[DoseModificationRule]
    ) -> tuple[Optional[CalculatedDose], list[Warning], list[str]]:
        """Calculate the actual dose for a drug"""
        
        warnings: list[Warning] = []
        modifications: list[str] = []
        
        # Get override if any
        override = (
            request.drug_overrides.get(drug.drug_id) or
            request.drug_overrides.get(drug.drug_name)
        )
        
        # Calculate base dose
        base_dose = drug.dose
        dose_unit = drug.dose_unit
        
        # Apply BSA/weight-based calculation
        if dose_unit == DoseUnit.MG_M2:
            calculated_dose = base_dose * bsa
            final_unit = "mg"
        elif dose_unit == DoseUnit.G_M2:
            calculated_dose = base_dose * bsa
            final_unit = "g"
        elif dose_unit == DoseUnit.MG_KG:
            calculated_dose = base_dose * patient.weight_kg
            final_unit = "mg"
        elif dose_unit == DoseUnit.UNITS_M2:
            calculated_dose = base_dose * bsa
            final_unit = "units"
        elif dose_unit == DoseUnit.MCG_M2:
            calculated_dose = base_dose * bsa
            final_unit = "mcg"
        else:
            # Flat dose
            calculated_dose = base_dose
            final_unit = dose_unit.value if hasattr(dose_unit, 'value') else str(dose_unit)
        
        # Apply max dose cap if specified
        if drug.max_dose:
            if calculated_dose > drug.max_dose:
                warnings.append(Warning(
                    level="info",
                    message=f"{drug.drug_name}: dose capped at {drug.max_dose}{drug.max_dose_unit or final_unit} (calculated: {calculated_dose:.1f})",
                    drug_id=drug.drug_id
                ))
                calculated_dose = drug.max_dose
        
        dose_modified = False
        modification_reason = None
        modification_percent = None
        
        # Apply dose modifications based on lab values
        for rule in modification_rules:
            if drug.drug_id in rule.affected_drugs or drug.drug_name in rule.affected_drugs:
                mod_applied, mod_factor, mod_desc = self._apply_modification_rule(
                    rule, patient
                )
                if mod_applied:
                    if mod_factor == 0:
                        # Omit drug
                        return None, [Warning(
                            level="warning",
                            message=f"{drug.drug_name} omitted: {mod_desc}",
                            drug_id=drug.drug_id
                        )], [f"{drug.drug_name}: {mod_desc}"]
                    
                    calculated_dose *= mod_factor
                    dose_modified = True
                    modification_reason = mod_desc
                    modification_percent = int(mod_factor * 100)
                    modifications.append(f"{drug.drug_name}: {mod_desc}")
        
        # Apply manual override
        if override:
            if override.custom_dose is not None:
                calculated_dose = override.custom_dose
                dose_modified = True
                modification_reason = "Manual override"
            elif override.dose_percent is not None:
                calculated_dose *= (override.dose_percent / 100)
                dose_modified = True
                modification_reason = f"Manual override ({override.dose_percent}%)"
                modification_percent = override.dose_percent
        
        # Round dose appropriately
        calculated_dose = self._round_dose(calculated_dose, final_unit)
        
        # Apply dose banding if applicable
        banded_dose = self._apply_dose_banding(calculated_dose, drug.drug_name, final_unit)
        
        return CalculatedDose(
            drug_id=drug.drug_id,
            drug_name=drug.drug_name,
            original_dose=drug.dose,
            original_dose_unit=str(dose_unit.value) if hasattr(dose_unit, 'value') else str(dose_unit),
            calculated_dose=calculated_dose,
            calculated_dose_unit=final_unit,
            route=str(drug.route.value) if hasattr(drug.route, 'value') else str(drug.route),
            days=drug.days,
            duration_minutes=drug.duration_minutes,
            diluent=drug.diluent,
            diluent_volume_ml=drug.diluent_volume_ml,
            timing=drug.timing,
            frequency=drug.frequency,
            special_instructions=drug.special_instructions,
            prn=drug.prn,
            dose_modified=dose_modified,
            modification_reason=modification_reason,
            modification_percent=modification_percent,
            banded_dose=banded_dose
        ), warnings, modifications
    
    def _apply_modification_rule(
        self, rule: DoseModificationRule, patient: PatientData
    ) -> tuple[bool, float, str]:
        """Apply a dose modification rule, returns (applied, factor, description)"""
        
        # Get the patient value for the parameter
        param_map = {
            "neutrophils": patient.neutrophils,
            "platelets": patient.platelets,
            "bilirubin": patient.bilirubin,
            "creatinine_clearance": patient.creatinine_clearance,
            "ast": patient.ast,
            "alt": patient.alt,
            "hemoglobin": patient.hemoglobin
        }
        
        value = param_map.get(rule.parameter.lower())
        if value is None:
            return False, 1.0, ""
        
        # Parse the condition
        condition = rule.condition.strip()
        condition_met = False
        
        # Handle different condition formats
        if condition.startswith("<"):
            threshold = float(condition[1:].strip())
            condition_met = value < threshold
        elif condition.startswith(">"):
            threshold = float(condition[1:].strip())
            condition_met = value > threshold
        elif condition.startswith("<="):
            threshold = float(condition[2:].strip())
            condition_met = value <= threshold
        elif condition.startswith(">="):
            threshold = float(condition[2:].strip())
            condition_met = value >= threshold
        elif "-" in condition:
            # Range like "20-50"
            parts = condition.split("-")
            low, high = float(parts[0]), float(parts[1])
            condition_met = low <= value <= high
        
        if not condition_met:
            return False, 1.0, ""
        
        # Determine modification factor
        mod = rule.modification.lower()
        if "omit" in mod:
            return True, 0, rule.description
        elif rule.modification_percent:
            return True, rule.modification_percent / 100, rule.description
        elif "50" in mod:
            return True, 0.5, rule.description
        elif "75" in mod:
            return True, 0.75, rule.description
        elif "70" in mod:
            return True, 0.7, rule.description
        elif "25" in mod:
            return True, 0.25, rule.description
        
        return True, 1.0, rule.description
    
    def _round_dose(self, dose: float, unit: str) -> float:
        """Round dose to appropriate precision"""
        if unit in ["g", "G"]:
            return round(dose, 2)
        elif unit in ["mcg", "MCG"]:
            return round(dose, 0)
        elif dose >= 100:
            return round(dose, 0)
        elif dose >= 10:
            return round(dose, 1)
        else:
            return round(dose, 2)
    
    def _apply_dose_banding(
        self, dose: float, drug_name: str, unit: str
    ) -> Optional[float]:
        """Apply dose banding for certain drugs (national standards)"""
        
        # Standard dose bands for common drugs
        # Based on NHS dose banding guidance
        
        drug_lower = drug_name.lower()
        
        if "rituximab" in drug_lower:
            # Rituximab rounded to nearest 100mg
            if unit == "mg":
                remainder = dose % 100
                if remainder >= 50:
                    return dose + (100 - remainder)
                return dose - remainder
        
        # Other drugs can be added here
        return None
    
    def _generate_standard_warnings(
        self, patient: PatientData, protocol: Protocol
    ) -> list[Warning]:
        """Generate standard warnings based on patient parameters"""
        warnings = []
        
        # Low neutrophils
        if patient.neutrophils is not None and patient.neutrophils < 1.0:
            warnings.append(Warning(
                level="warning",
                message=f"Low neutrophil count ({patient.neutrophils} x10⁹/L). Consider delaying treatment."
            ))
        
        # Low platelets
        if patient.platelets is not None and patient.platelets < 100:
            warnings.append(Warning(
                level="warning",
                message=f"Low platelet count ({patient.platelets} x10⁹/L). Consider delaying treatment."
            ))
        
        # Elevated bilirubin
        if patient.bilirubin is not None and patient.bilirubin > 30:
            warnings.append(Warning(
                level="warning",
                message=f"Elevated bilirubin ({patient.bilirubin} µmol/L). Review hepatic dose modifications."
            ))
        
        # Low CrCl
        if patient.creatinine_clearance is not None and patient.creatinine_clearance < 30:
            warnings.append(Warning(
                level="critical",
                message=f"Severely reduced renal function (CrCl {patient.creatinine_clearance} ml/min). Review renal dose modifications."
            ))
        
        # Low hemoglobin
        if patient.hemoglobin is not None and patient.hemoglobin < 8:
            warnings.append(Warning(
                level="info",
                message=f"Low hemoglobin ({patient.hemoglobin} g/dL). Consider blood transfusion."
            ))
        
        return warnings
    
    def search_protocols(self, query: str) -> list[Protocol]:
        """Search protocols by name, code, or drug"""
        query_lower = query.lower()
        results = []
        
        for protocol in self.protocols.values():
            # Match on code
            if query_lower in protocol.code.lower():
                results.append(protocol)
                continue
            
            # Match on name
            if query_lower in protocol.name.lower():
                results.append(protocol)
                continue
            
            # Match on drugs
            for drug in protocol.drugs:
                if query_lower in drug.drug_name.lower():
                    results.append(protocol)
                    break
        
        return results
    
    def get_all_drugs(self) -> list[str]:
        """Get list of all unique drugs across protocols"""
        drugs = set()
        for protocol in self.protocols.values():
            for drug in protocol.drugs:
                drugs.add(drug.drug_name)
        return sorted(list(drugs))


def calculate_bsa_mosteller(height_cm: float, weight_kg: float) -> float:
    """Calculate BSA using Mosteller formula"""
    import math
    return math.sqrt((height_cm * weight_kg) / 3600)


def calculate_bsa_dubois(height_cm: float, weight_kg: float) -> float:
    """Calculate BSA using Du Bois formula"""
    return 0.007184 * (height_cm ** 0.725) * (weight_kg ** 0.425)


def calculate_creatinine_clearance(
    creatinine: float,  # µmol/L
    age: int,
    weight_kg: float,
    female: bool = False
) -> float:
    """Calculate CrCl using Cockcroft-Gault formula"""
    # Convert creatinine from µmol/L to mg/dL
    creatinine_mg = creatinine / 88.4
    
    crcl = ((140 - age) * weight_kg) / (72 * creatinine_mg)
    if female:
        crcl *= 0.85
    
    return round(crcl, 1)
