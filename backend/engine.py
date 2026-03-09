"""
Chemotherapy Protocol Engine - Core Logic
Handles dose calculations, modifications, and drug selection

SAFETY CRITICAL: This module contains life-critical dose calculation logic.
All changes must be reviewed by a clinical pharmacist and oncologist.

Key Safety Features:
- BSA capping at 2.0 m² for obese patients (ASCO guidelines)
- Hard stops for contraindicated lab values
- CRITICAL alerts for max dose caps (especially vincristine)
- Allergy cross-checking
- Performance status and age-based modifications
"""

from typing import Optional
import re
from datetime import datetime
from datetime import timedelta
from models import (
    Protocol, ProtocolDrug, PatientData, ProtocolRequest, ProtocolResponse,
    CalculatedDose, Warning, DoseModificationRule, DoseUnit, CycleVariation,
    BSA_CAP_OBESE, NEUTROPHIL_DELAY_THRESHOLD, PLATELET_DELAY_THRESHOLD,
    ECOGPerformanceStatus, HematologicalToxicityRule, NonHematologicalToxicityRule,
    AgeBasedModification, CumulativeToxicityTracking, MetabolicMonitoringRule,
    CustomRegimenRequest, CustomRegimenDrug, BlinatumomabBagEntry
)


# Drugs with CRITICAL max dose requirements (overdose = death/permanent injury)
CRITICAL_MAX_DOSE_DRUGS = {
    'vincristine': {'max_mg': 2.0, 'reason': 'Overdose causes permanent paralysis and death'},
    'vinblastine': {'max_mg': None, 'reason': 'Vesicant with severe toxicity'},
}

# Drugs requiring irradiated blood products permanently
IRRADIATED_BLOOD_DRUGS = ['bendamustine', 'fludarabine', 'cladribine', 'clofarabine']

# Common drug allergy cross-reactivity groups
ALLERGY_CROSS_REACTIVITY = {
    'platinum': ['cisplatin', 'carboplatin', 'oxaliplatin'],
    'taxane': ['paclitaxel', 'docetaxel'],
    'anthracycline': ['doxorubicin', 'daunorubicin', 'epirubicin', 'idarubicin'],
}

# Anthracycline equivalent conversion factors (to doxorubicin equivalent)
ANTHRACYCLINE_EQUIVALENCE = {
    'doxorubicin': 1.0,
    'daunorubicin': 0.83,  # 60mg daunorubicin ≈ 50mg doxorubicin
    'epirubicin': 0.5,     # More cardiotoxic at same dose
    'idarubicin': 5.0,     # Much more potent
}


# ============= HELPER FUNCTIONS FOR DOSE CALCULATIONS =============

def evaluate_condition(value: float, rule: DoseModificationRule) -> bool:
    """
    Evaluate if a lab value meets a dose modification condition.
    Supports: less_than, greater_than, range, less_equal, greater_equal, equals
    """
    if value is None:
        return False
    
    cond_type = rule.condition_type.lower().replace("_", "")
    
    # Range condition (e.g., 10-29)
    if cond_type == "range":
        if rule.threshold_low is not None and rule.threshold_high is not None:
            return rule.threshold_low <= value <= rule.threshold_high
        # Fallback: parse from condition string like "10-29"
        if "-" in rule.condition:
            parts = rule.condition.split("-")
            try:
                low, high = float(parts[0].strip()), float(parts[1].strip())
                return low <= value <= high
            except (ValueError, IndexError):
                pass
        return False
    
    # Single threshold conditions
    threshold = rule.threshold_value
    if threshold is None:
        # Try to parse from condition string
        condition = rule.condition.strip()
        try:
            if condition.startswith("<="):
                threshold = float(condition[2:].strip())
                cond_type = "lessequal"
            elif condition.startswith(">="):
                threshold = float(condition[2:].strip())
                cond_type = "greaterequal"
            elif condition.startswith("<"):
                threshold = float(condition[1:].strip())
                cond_type = "lessthan"
            elif condition.startswith(">"):
                threshold = float(condition[1:].strip())
                cond_type = "greaterthan"
            elif condition.startswith("="):
                threshold = float(condition[1:].strip())
                cond_type = "equals"
        except ValueError:
            return False
    
    if threshold is None:
        return False
    
    if cond_type in ("lessthan", "lt", "<"):
        return value < threshold
    elif cond_type in ("lessequal", "lte", "le", "<="):
        return value <= threshold
    elif cond_type in ("greaterthan", "gt", ">"):
        return value > threshold
    elif cond_type in ("greaterequal", "gte", "ge", ">="):
        return value >= threshold
    elif cond_type in ("equals", "eq", "="):
        return abs(value - threshold) < 0.001
    
    return False


def get_modification_factor(rule: DoseModificationRule) -> float:
    """Get the dose modification factor (0 = omit, 0.5 = 50%, 0.75 = 75%, 1.0 = no change)"""
    mod_type = rule.modification_type.lower() if rule.modification_type else ""
    
    if mod_type == "omit" or rule.modification_percent == 0:
        return 0.0
    
    if rule.modification_percent is not None:
        return rule.modification_percent / 100.0
    
    # Parse from modification string like "reduce_50"
    mod_str = (rule.modification or "").lower()
    if "omit" in mod_str:
        return 0.0
    
    # Look for percentage in modification string
    import re
    match = re.search(r'(\d+)', mod_str)
    if match:
        percent = int(match.group(1))
        # "reduce_50" means give 50% of dose
        # "reduce by 25%" means give 75% of dose
        if "by" in mod_str:
            return (100 - percent) / 100.0
        return percent / 100.0
    
    return 1.0


def calculate_cumulative_anthracycline_dose(
    prior_dose_mg_m2: float,
    current_protocol_doses: list[tuple[str, float]],  # List of (drug_name, dose_mg_m2)
    num_cycles: int,
    bsa: float
) -> tuple[float, float]:
    """
    Calculate cumulative anthracycline dose in doxorubicin equivalents.
    Returns (projected_total_dose, projected_dose_after_protocol)
    """
    # Convert prior dose (assume already in doxorubicin equivalent)
    total_dose = prior_dose_mg_m2
    
    # Add current protocol doses
    protocol_anthracycline_per_cycle = 0.0
    for drug_name, dose_mg_m2 in current_protocol_doses:
        drug_lower = drug_name.lower()
        if drug_lower in ANTHRACYCLINE_EQUIVALENCE:
            protocol_anthracycline_per_cycle += dose_mg_m2 * ANTHRACYCLINE_EQUIVALENCE[drug_lower]
    
    projected_protocol_total = protocol_anthracycline_per_cycle * num_cycles
    projected_total = total_dose + projected_protocol_total
    
    return (total_dose, projected_total)


def check_anthracycline_limit(
    patient_age: int,
    prior_anthracycline_mg_m2: float,
    projected_total_mg_m2: float,
    has_cardiac_history: bool = False,
    has_mediastinal_radiation: bool = False
) -> tuple[bool, str, float]:
    """
    Check if anthracycline lifetime limit would be exceeded.
    Returns (limit_exceeded, warning_message, applicable_limit)
    """
    # Determine applicable limit
    if has_cardiac_history:
        limit = 400
        reason = "cardiac history"
    elif patient_age >= 70:
        limit = 400
        reason = "age ≥70"
    elif has_mediastinal_radiation:
        limit = 350
        reason = "prior mediastinal radiation"
    else:
        limit = 450
        reason = "standard limit"
    
    if projected_total_mg_m2 > limit:
        return (True, f"Lifetime anthracycline limit ({limit} mg/m² due to {reason}) will be exceeded. "
                      f"Projected total: {projected_total_mg_m2:.1f} mg/m²", limit)
    
    # Warning at 80% of limit
    if projected_total_mg_m2 > limit * 0.8:
        return (False, f"Approaching anthracycline lifetime limit. "
                       f"Prior: {prior_anthracycline_mg_m2:.1f} mg/m², "
                       f"Projected: {projected_total_mg_m2:.1f} mg/m² (limit: {limit} mg/m²)", limit)
    
    return (False, "", limit)


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
        """
        Generate a personalized protocol based on request.
        
        SAFETY CRITICAL: This method includes multiple safety checks:
        1. Treatment delay validation
        2. Allergy cross-checking
        3. BSA capping for obese patients
        4. Age and performance status modifications
        5. Cumulative toxicity warnings
        """
        
        protocol = self.get_protocol(request.protocol_code)
        if not protocol:
            raise ValueError(f"Protocol not found: {request.protocol_code}")
        
        patient = request.patient
        # SAFETY: Use capped BSA (2.0 m² max) to prevent overdosing in obese patients.
        # Round to 2dp so the dose calculation always matches the BSA shown in the header.
        bsa = round(patient.capped_bsa, 2)
        warnings: list[Warning] = []
        modifications_applied: list[str] = []
        
        # SAFETY CHECK 1: Treatment delay required?
        if patient.requires_delay:
            for reason in patient.delay_reasons:
                warnings.append(Warning(
                    level="critical",
                    message=f"⚠️ TREATMENT DELAY RECOMMENDED: {reason}. Consider postponing until values recover."
                ))
        
        # Determine if this protocol has any BSA-based drugs
        all_drugs = protocol.drugs + protocol.pre_medications + protocol.take_home_medicines
        has_bsa_drug = any(
            d.dose_unit in ("mg/m²", "mcg/m²", "g/m²", "units/m²", "IU/m²", "mg/m2", "IU/m2")
            for d in all_drugs
        )

        # SAFETY CHECK 2: BSA capping notification — only relevant for BSA-dosed protocols
        if patient.bsa_was_capped and has_bsa_drug:
            warnings.append(Warning(
                level="warning",
                message=f"BSA capped at {BSA_CAP_OBESE} m² (actual: {patient.calculated_bsa:.2f} m²) per ASCO guidelines for obese patients."
            ))
            modifications_applied.append(f"BSA capped: {patient.calculated_bsa:.2f} → {BSA_CAP_OBESE} m²")

        # SAFETY CHECK 3: Elderly patient note — only relevant for BSA-dosed protocols
        # Flat-dose drugs (e.g. blinatumomab) have no dose adjustment in elderly per their SPC
        if patient.elderly_patient and has_bsa_drug:
            warnings.append(Warning(
                level="info",
                message=(
                    f"Patient age {patient.age_years} years — protocol may recommend dose reduction. "
                    f"Review per-drug warnings below. Prescriber must confirm all doses."
                )
            ))
        
        # SAFETY CHECK 4: Poor performance status
        if patient.poor_performance_status:
            warnings.append(Warning(
                level="critical",
                message=f"ECOG Performance Status {patient.performance_status.value} - Full-dose chemotherapy may not be appropriate. Consider dose reduction or alternative treatment."
            ))

        # SAFETY CHECK 5: Haematological hard stops (moved from Pydantic to engine so response is a
        # clinical warning, not an HTTP 422 error — clinicians still need to be able to model doses)
        if patient.neutrophils is not None and patient.neutrophils < 0.5:
            warnings.insert(0, Warning(
                level="critical",
                message=f"TREATMENT CONTRAINDICATED: Neutrophils {patient.neutrophils} ×10⁹/L — below absolute contraindication threshold (<0.5). Severe sepsis risk. Do not administer chemotherapy."
            ))
        elif patient.neutrophils is not None and patient.neutrophils < 1.0:
            warnings.append(Warning(
                level="critical",
                message=f"TREATMENT DELAY: Neutrophils {patient.neutrophils} ×10⁹/L (<1.0). Delay until ≥1.0×10⁹/L. Consider G-CSF prophylaxis."
            ))

        if patient.platelets is not None and patient.platelets < 50:
            warnings.insert(0, Warning(
                level="critical",
                message=f"TREATMENT CONTRAINDICATED: Platelets {patient.platelets} ×10⁹/L — below absolute contraindication threshold (<50). Severe haemorrhage risk. Do not administer chemotherapy."
            ))
        elif patient.platelets is not None and patient.platelets < 100:
            warnings.append(Warning(
                level="critical",
                message=f"TREATMENT DELAY: Platelets {patient.platelets} ×10⁹/L (<100). Delay until ≥100×10⁹/L."
            ))

        if patient.creatinine_clearance is not None and patient.creatinine_clearance < 10:
            warnings.insert(0, Warning(
                level="critical",
                message=f"SEVERE RENAL FAILURE: CrCl {patient.creatinine_clearance} ml/min. Nephrotoxic drugs must be dose-reduced or omitted. Nephrology review required before proceeding."
            ))

        # SAFETY CHECK 6: Active infection — treatment must be delayed
        if patient.active_infection:
            warnings.append(Warning(
                level="critical",
                message="TREATMENT DELAY REQUIRED: Active infection or fever present. Chemotherapy must not proceed until infection is treated and patient is afebrile."
            ))

        # SAFETY CHECK 6: Pregnancy — teratogenic drugs
        if patient.pregnancy_status == "pregnant":
            warnings.append(Warning(
                level="critical",
                message="PREGNANCY: Patient is pregnant. All cytotoxic chemotherapy is potentially teratogenic. Specialist oncology and obstetric review mandatory before proceeding."
            ))

        # SAFETY CHECK 7: HBV reactivation risk with rituximab
        protocol_drug_names = [d.drug_name.lower() for d in protocol.drugs]
        # HBV reactivation risk applies to rituximab AND blinatumomab (any immunosuppressive agent)
        HBV_RISK_DRUGS = ("rituximab", "blinatumomab", "obinutuzumab", "ofatumumab",
                          "ocrelizumab", "alemtuzumab")
        uses_immunosuppressive = any(
            any(d in n for d in HBV_RISK_DRUGS) for n in protocol_drug_names
        )
        if uses_immunosuppressive:
            if patient.hep_b_surface_antigen == "positive":
                if not patient.hbv_prophylaxis_started:
                    warnings.append(Warning(
                        level="critical",
                        message="HBsAg POSITIVE: Fatal HBV reactivation risk with rituximab. Antiviral prophylaxis (entecavir) MUST be started before rituximab and continued for 12 months after last dose. Confirm prophylaxis is prescribed."
                    ))
                else:
                    warnings.append(Warning(
                        level="warning",
                        message="HBsAg positive — HBV prophylaxis confirmed started. Monitor HBV DNA every 3 months during and for 12 months after rituximab."
                    ))
            elif patient.hep_b_core_antibody == "positive":
                if not patient.hbv_prophylaxis_started:
                    warnings.append(Warning(
                        level="warning",
                        message="Anti-HBc POSITIVE (HBsAg negative): Prior HBV exposure — reactivation risk with rituximab. Antiviral prophylaxis or close HBV DNA monitoring required. Confirm management plan."
                    ))
                else:
                    warnings.append(Warning(
                        level="info",
                        message="Anti-HBc positive — HBV prophylaxis confirmed started. Monitor HBV DNA during rituximab therapy."
                    ))
            elif patient.hep_b_surface_antigen is None or patient.hep_b_core_antibody is None:
                warnings.append(Warning(
                    level="warning",
                    message="HBV serology (HBsAg, Anti-HBc) not recorded — required before rituximab due to fatal reactivation risk. Ensure screening is completed."
                ))

        # SAFETY CHECK 8: Baseline LVEF before anthracyclines
        uses_anthracycline = any(
            n in protocol_drug_names
            for n in ("doxorubicin", "epirubicin", "daunorubicin", "idarubicin", "mitoxantrone")
        )
        if uses_anthracycline:
            needs_echo = (
                patient.prior_cardiac_history
                or patient.age_years >= 70
                or (patient.prior_anthracycline_dose_mg_m2 and patient.prior_anthracycline_dose_mg_m2 > 0)
            )
            if needs_echo:
                if patient.lvef_percent is None:
                    warnings.append(Warning(
                        level="warning",
                        message="BASELINE ECHO REQUIRED: Patient has cardiac risk factors (age ≥70, cardiac history, or prior anthracyclines). Baseline LVEF must be documented before doxorubicin."
                    ))
                elif patient.lvef_percent < 50:
                    warnings.append(Warning(
                        level="critical",
                        message=f"REDUCED LVEF {patient.lvef_percent:.0f}%: Doxorubicin use requires cardiology review. Contraindicated if LVEF <40%. Do not proceed without specialist input."
                    ))
                elif patient.lvef_percent < 55:
                    warnings.append(Warning(
                        level="warning",
                        message=f"BORDERLINE LVEF {patient.lvef_percent:.0f}%: Monitor cardiac function closely during anthracycline therapy."
                    ))

        # SAFETY CHECK 9: Peripheral neuropathy grading before vincristine
        uses_vincristine = any("vincristine" in n for n in protocol_drug_names)
        if uses_vincristine and patient.peripheral_neuropathy_grade is not None:
            if patient.peripheral_neuropathy_grade >= 3:
                warnings.append(Warning(
                    level="critical",
                    message=f"PERIPHERAL NEUROPATHY GRADE {patient.peripheral_neuropathy_grade}: Vincristine MUST be omitted (Grade ≥3). Discuss with consultant."
                ))
            elif patient.peripheral_neuropathy_grade == 2:
                warnings.append(Warning(
                    level="warning",
                    message="PERIPHERAL NEUROPATHY GRADE 2: Vincristine dose reduction required (reduce to 1mg or consider omission). Review with consultant."
                ))
            elif patient.peripheral_neuropathy_grade == 1:
                warnings.append(Warning(
                    level="info",
                    message="PERIPHERAL NEUROPATHY GRADE 1: Monitor closely. Reduce vincristine dose at grade 2."
                ))

        # SAFETY CHECK 10: Tumor lysis risk
        if patient.tls_risk == "high":
            warnings.append(Warning(
                level="critical",
                message="HIGH TLS RISK: Rasburicase and aggressive IV hydration required. Ensure urate, creatinine, phosphate, potassium and calcium monitoring in place. Allopurinol is NOT sufficient."
            ))
        elif patient.tls_risk == "intermediate":
            warnings.append(Warning(
                level="warning",
                message="INTERMEDIATE TLS RISK: Allopurinol prophylaxis and IV hydration required. Monitor electrolytes and urate closely."
            ))

        # SAFETY CHECK 11: Check for allergies to protocol drugs
        allergy_warnings = self._check_allergies(protocol, patient)
        warnings.extend(allergy_warnings)

        # SAFETY CHECK 12: Cumulative toxicity warnings
        cumulative_warnings = self._check_cumulative_toxicity(protocol, patient)
        warnings.extend(cumulative_warnings)

        # SAFETY CHECK 13: Irradiated blood products
        irradiated_warnings = self._check_irradiated_blood(protocol)
        warnings.extend(irradiated_warnings)
        
        # Get cycle-specific drugs
        cycle_drugs, cycle_take_home, cycle_instructions = self._get_cycle_specific_content(
            protocol, request.cycle_number
        )
        
        # Calculate doses for core drugs
        chemo_doses = []
        for drug in cycle_drugs:
            if self._should_include_drug(drug, request, patient):
                calc_dose, drug_warnings, mods = self._calculate_dose(
                    drug, patient, bsa, request, protocol.dose_modifications, protocol
                )
                warnings.extend(drug_warnings)
                modifications_applied.extend(mods)
                if calc_dose:
                    chemo_doses.append(calc_dose)

        # Calculate pre-medication doses (apply cycle-1-only filtering same as chemo drugs)
        cycle_premeds = self._adjust_days_for_cycle(protocol.pre_medications, request.cycle_number)
        premed_doses = []
        if request.include_premeds:
            for drug in cycle_premeds:
                if self._should_include_drug(drug, request, patient):
                    calc_dose, drug_warnings, mods = self._calculate_dose(
                        drug, patient, bsa, request, [], protocol
                    )
                    if calc_dose:
                        premed_doses.append(calc_dose)
                        warnings.extend(drug_warnings)

        # Calculate take-home medicine doses
        take_home_doses = []
        if request.include_take_home:
            for drug in cycle_take_home:
                if self._should_include_drug(drug, request, patient):
                    calc_dose, drug_warnings, mods = self._calculate_dose(
                        drug, patient, bsa, request, [], protocol
                    )
                    if calc_dose:
                        take_home_doses.append(calc_dose)
                        warnings.extend(drug_warnings)

        # Calculate rescue medication doses
        rescue_doses = []
        if request.include_rescue:
            for drug in protocol.rescue_medications:
                if self._should_include_drug(drug, request, patient):
                    calc_dose, drug_warnings, mods = self._calculate_dose(
                        drug, patient, bsa, request, [], protocol
                    )
                    if calc_dose:
                        rescue_doses.append(calc_dose)
                        warnings.extend(drug_warnings)
        
        # Add standard warnings
        warnings.extend(self._generate_standard_warnings(patient, protocol))

        # Combine special instructions — filter cycle-specific past instructions
        filtered_instructions = self._filter_cycle_specific_instructions(
            protocol.warnings, request.cycle_number
        )
        all_instructions = filtered_instructions + cycle_instructions

        # Check for mandatory concurrent medications mentioned in warnings
        # (e.g. LHRH agonist mandatory for ribociclib in pre/peri-menopausal patients)
        mandatory_concurrent = self._extract_mandatory_concurrent_meds(protocol.warnings, request.cycle_number)
        if mandatory_concurrent:
            warnings.extend(mandatory_concurrent)

        # Add safety disclaimer as first instruction
        all_instructions = [
            "⚠️ SAFETY NOTICE: This protocol is generated by SOPHIA for clinical decision support only. "
            "Independent verification by prescriber and pharmacist is REQUIRED before administration."
        ] + all_instructions

        # Blinatumomab-specific checks and bag schedule
        blina_schedule = None
        if "blinatumomab" in protocol.code.lower() or "blina" in protocol.code.lower():
            # Blast count pre-phase assessment (cycle 1 only)
            if request.cycle_number == 1:
                pb = patient.peripheral_blast_percent
                bm = patient.bone_marrow_blast_percent
                if pb is not None and pb > 15:
                    warnings.insert(0, Warning(
                        level="critical",
                        message=(
                            f"PRE-PHASE REQUIRED: Peripheral blast count {pb:.0f}% (>15%). "
                            f"Dexamethasone pre-phase (up to 5 days) must be completed before starting "
                            f"blinatumomab to reduce tumour load and CRS/neurotoxicity risk."
                        )
                    ))
                elif bm is not None and bm > 50:
                    warnings.insert(0, Warning(
                        level="critical",
                        message=(
                            f"PRE-PHASE REQUIRED: Bone marrow blasts {bm:.0f}% (>50%). "
                            f"Dexamethasone pre-phase (up to 5 days) must be completed before starting "
                            f"blinatumomab to reduce tumour load and CRS/neurotoxicity risk."
                        )
                    ))
                elif pb is None and bm is None:
                    warnings.append(Warning(
                        level="warning",
                        message=(
                            "BLAST COUNT NOT RECORDED: Peripheral blast % and bone marrow blast % "
                            "must be assessed before cycle 1 blinatumomab. Pre-phase dexamethasone "
                            "is required if peripheral blasts >15% or bone marrow blasts >50%."
                        )
                    ))

            blina_schedule, blina_date_warning = self._generate_blinatumomab_bag_schedule(request, request.cycle_number)
            if blina_date_warning:
                warnings.insert(0, Warning(level="critical", message=blina_date_warning))

        return ProtocolResponse(
            protocol_id=protocol.id,
            protocol_name=protocol.name,
            protocol_code=protocol.code,
            indication=protocol.indication,
            cycle_number=request.cycle_number,
            cycle_length_days=protocol.cycle_length_days,
            total_cycles=protocol.total_cycles,
            patient_bsa=round(bsa, 2),
            patient_bsa_actual=round(patient.calculated_bsa, 2),
            patient_bsa_capped=patient.bsa_was_capped,
            patient_weight=patient.weight_kg,
            patient_age=patient.age_years,
            patient_performance_status=patient.performance_status.value,
            pre_medications=premed_doses,
            chemotherapy_drugs=chemo_doses,
            take_home_medicines=take_home_doses,
            rescue_medications=rescue_doses,
            monitoring_requirements=protocol.monitoring,
            special_instructions=all_instructions,
            warnings=warnings,
            dose_modifications_applied=modifications_applied,
            # Audit trail
            generated_at=datetime.now().isoformat(),
            protocol_version=protocol.version,
            treatment_delay_recommended=patient.requires_delay,
            delay_reasons=patient.delay_reasons if patient.requires_delay else [],
            is_ai_generated=getattr(protocol, 'is_ai_generated', False),
            blinatumomab_bag_schedule=blina_schedule,
        )

    def generate_custom_regimen(self, request: CustomRegimenRequest) -> ProtocolResponse:
        """
        Generate a protocol from a fully custom drug list built by the clinician.
        Applies the same safety checks (BSA capping, delay detection, allergy alerts)
        but does NOT apply protocol-level dose modification rules — the clinician has
        already made those decisions when they built the regimen.
        """
        patient = request.patient
        bsa = round(patient.capped_bsa, 2)
        warnings: list[Warning] = []
        modifications_applied: list[str] = []

        # Standard safety checks
        if patient.requires_delay:
            for reason in patient.delay_reasons:
                warnings.append(Warning(
                    level="critical",
                    message=f"⚠️ TREATMENT DELAY RECOMMENDED: {reason}."
                ))

        if patient.bsa_was_capped:
            warnings.append(Warning(
                level="warning",
                message=f"BSA capped at {BSA_CAP_OBESE} m² (actual: {patient.calculated_bsa:.2f} m²) per ASCO guidelines."
            ))
            modifications_applied.append(f"BSA capped: {patient.calculated_bsa:.2f} → {BSA_CAP_OBESE} m²")

        if patient.elderly_patient:
            warnings.append(Warning(
                level="warning",
                message=f"Patient age {patient.age_years} years — consider dose reduction."
            ))

        if patient.poor_performance_status:
            warnings.append(Warning(
                level="critical",
                message=f"ECOG {patient.performance_status.value} — full-dose chemotherapy may not be appropriate."
            ))

        # Allergy checks against custom drugs
        for drug in request.drugs:
            if patient.has_allergy_to(drug.drug_name):
                warnings.append(Warning(
                    level="critical",
                    message=f"⚠️ ALLERGY ALERT: Patient has documented allergy to {drug.drug_name}."
                ))
            # Cross-reactivity
            drug_lower = drug.drug_name.lower()
            for group, members in ALLERGY_CROSS_REACTIVITY.items():
                if drug_lower in [m.lower() for m in members]:
                    for allergy in patient.known_allergies:
                        if allergy.lower() in [m.lower() for m in members] and allergy.lower() != drug_lower:
                            warnings.append(Warning(
                                level="critical",
                                message=f"⚠️ CROSS-REACTIVITY: Patient allergic to {allergy}, {drug.drug_name} is in same class ({group})."
                            ))

        # Vincristine hard cap
        for drug in request.drugs:
            if 'vincristine' in drug.drug_name.lower():
                unit = drug.dose_unit.lower().replace(" ", "")
                is_bsa_unit = 'mg/m' in unit or 'mgm' in unit
                calc = drug.dose * bsa if is_bsa_unit else drug.dose
                if calc > 2.0:
                    warnings.append(Warning(
                        level="critical",
                        message=f"⚠️ VINCRISTINE HARD CAP: Calculated dose {calc:.2f}mg exceeds 2mg cap. Will be limited to 2mg."
                    ))
                    modifications_applied.append("Vincristine capped at 2mg (absolute max)")

        # Calculate doses
        chemo_doses: list[CalculatedDose] = []
        for drug in request.drugs:
            unit = drug.dose_unit.lower().replace(" ", "")
            is_bsa_unit = 'mg/m' in unit or 'mgm' in unit
            is_weight_unit = 'mg/kg' in unit or 'mgkg' in unit

            if is_bsa_unit:
                calc = round(drug.dose * bsa, 1)
            elif is_weight_unit:
                calc = round(drug.dose * patient.weight_kg, 1)
            else:
                calc = drug.dose

            # Vincristine 2mg absolute cap
            if 'vincristine' in drug.drug_name.lower():
                calc = min(calc, 2.0)

            # Apply max_dose cap if specified
            if drug.max_dose and calc > drug.max_dose:
                calc = drug.max_dose
                modifications_applied.append(f"{drug.drug_name}: capped at max dose {drug.max_dose} {drug.dose_unit}")

            calc_unit = "mg" if drug.dose_unit != "units/m²" else "units"
            if drug.dose_unit in ("units", "mcg", "g", "mg"):
                calc_unit = drug.dose_unit

            chemo_doses.append(CalculatedDose(
                drug_id=drug.drug_name.lower().replace(" ", "_"),
                drug_name=drug.drug_name,
                original_dose=drug.dose,
                original_dose_unit=drug.dose_unit,
                calculated_dose=calc,
                calculated_dose_unit=calc_unit,
                route=drug.route,
                days=drug.days,
                duration_minutes=drug.duration_minutes,
                diluent=drug.diluent,
                diluent_volume_ml=drug.diluent_volume_ml,
                frequency=drug.frequency,
                special_instructions=drug.special_instructions,
                prn=drug.prn,
                dose_modified=False,
            ))

        all_instructions = [
            "⚠️ CUSTOM REGIMEN — This is a clinician-built combination, not a validated standard protocol. "
            "Independent verification by prescriber and pharmacist is MANDATORY before administration.",
            "⚠️ SOPHIA applies BSA/weight calculations and hard caps only. All other dose decisions are the clinician's responsibility."
        ]

        return ProtocolResponse(
            protocol_id="custom",
            protocol_name=request.regimen_name,
            protocol_code="CUSTOM",
            indication="Custom clinician-built regimen",
            cycle_number=request.cycle_number,
            cycle_length_days=request.cycle_length_days,
            total_cycles=request.total_cycles,
            patient_bsa=round(bsa, 2),
            patient_bsa_actual=round(patient.calculated_bsa, 2),
            patient_bsa_capped=patient.bsa_was_capped,
            patient_weight=patient.weight_kg,
            patient_age=patient.age_years,
            patient_performance_status=patient.performance_status.value,
            pre_medications=[],
            chemotherapy_drugs=chemo_doses,
            take_home_medicines=[],
            rescue_medications=[],
            monitoring_requirements=["Regular FBC, LFTs, renal function as clinically indicated"],
            special_instructions=all_instructions,
            warnings=warnings,
            dose_modifications_applied=modifications_applied,
            generated_at=datetime.now().isoformat(),
            protocol_version="custom",
            treatment_delay_recommended=patient.requires_delay,
            delay_reasons=patient.delay_reasons if patient.requires_delay else [],
            is_ai_generated=True,  # Treat as requiring pharmacist verification
        )

    def _check_allergies(self, protocol: Protocol, patient: PatientData) -> list[Warning]:
        """Check for allergies to protocol drugs"""
        warnings = []
        all_drugs = protocol.drugs + protocol.pre_medications
        
        for drug in all_drugs:
            drug_name_lower = drug.drug_name.lower()
            
            # Check direct allergy
            if patient.has_allergy_to(drug.drug_name):
                warnings.append(Warning(
                    level="critical",
                    message=f"⚠️ ALLERGY ALERT: Patient has documented allergy to {drug.drug_name}. "
                            f"Drug MUST be omitted or desensitization considered.",
                    drug_id=drug.drug_id
                ))
            
            # Check cross-reactivity groups
            for group, drugs in ALLERGY_CROSS_REACTIVITY.items():
                if drug_name_lower in [d.lower() for d in drugs]:
                    for allergy in patient.known_allergies:
                        if allergy.lower() in [d.lower() for d in drugs] or allergy.lower() == group:
                            if allergy.lower() != drug_name_lower:  # Don't duplicate direct allergy
                                warnings.append(Warning(
                                    level="critical",
                                    message=f"⚠️ CROSS-REACTIVITY ALERT: Patient allergic to {allergy}, "
                                            f"{drug.drug_name} is in same class ({group}). Consider alternative.",
                                    drug_id=drug.drug_id
                                ))
        
        return warnings
    
    def _check_cumulative_toxicity(self, protocol: Protocol, patient: PatientData) -> list[Warning]:
        """Check for cumulative toxicity risk"""
        warnings = []
        
        # Anthracycline cumulative dose
        # prior_anthracycline_dose_mg_m2 is stored in doxorubicin-equivalent mg/m²
        # (i.e. the user should enter the doxo-equivalent, not the raw epirubicin dose)
        # Lifetime limit is 450 mg/m² doxorubicin-equivalent.
        # Per-drug limits in own units: doxorubicin 450, epirubicin 900, daunorubicin ~550, idarubicin ~90
        ANTHRACYCLINE_OWN_LIMITS = {
            'doxorubicin': 450,
            'epirubicin': 900,    # 900 mg/m² epirubicin = 450 mg/m² doxo-equivalent (factor 0.5)
            'daunorubicin': 550,
            'idarubicin': 90,
            'liposomal doxorubicin': 550,
            'pegylated liposomal doxorubicin': 550,
        }
        if patient.prior_anthracycline_dose_mg_m2:
            for drug in protocol.drugs:
                drug_lower = drug.drug_name.lower()
                equiv_factor = ANTHRACYCLINE_EQUIVALENCE.get(drug_lower)
                if equiv_factor is None:
                    # Try partial match for liposomal variants
                    for k, v in ANTHRACYCLINE_EQUIVALENCE.items():
                        if k in drug_lower:
                            equiv_factor = v
                            drug_lower = k
                            break
                if equiv_factor is None:
                    continue

                # prior dose is in doxo-equivalents; apply patient-specific limit
                prior_doxo_equiv = patient.prior_anthracycline_dose_mg_m2
                # Determine applicable doxorubicin-equivalent lifetime limit
                if patient.prior_mediastinal_radiation:
                    doxo_limit = 350
                    limit_reason = "prior mediastinal radiation"
                elif patient.prior_cardiac_history:
                    doxo_limit = 400
                    limit_reason = "cardiac history"
                elif patient.age_years and patient.age_years >= 70:
                    doxo_limit = 400
                    limit_reason = "age ≥70"
                else:
                    doxo_limit = 450
                    limit_reason = "standard limit"
                remaining_doxo = doxo_limit - prior_doxo_equiv
                # Express remaining in the current drug's own units
                own_limit = ANTHRACYCLINE_OWN_LIMITS.get(drug_lower, doxo_limit / equiv_factor)
                own_limit_adjusted = doxo_limit / equiv_factor
                remaining_own = remaining_doxo / equiv_factor

                if remaining_doxo <= 0:
                    warnings.append(Warning(
                        level="critical",
                        message=(
                            f"⚠️ CUMULATIVE ANTHRACYCLINE TOXICITY: Prior dose {prior_doxo_equiv:.0f} mg/m² "
                            f"(doxorubicin-equivalent) meets or exceeds lifetime limit of {doxo_limit} mg/m²-eq "
                            f"({limit_reason}) = {own_limit_adjusted:.0f} mg/m² {drug.drug_name}. "
                            f"Cardiac toxicity risk is very high. Do NOT administer without MDT review."
                        ),
                        drug_id=drug.drug_id
                    ))
                elif remaining_own < (own_limit_adjusted * 0.15):
                    # Warn when <15% of adjusted limit remains
                    warnings.append(Warning(
                        level="warning",
                        message=(
                            f"Approaching {drug.drug_name} lifetime limit ({limit_reason}). "
                            f"Prior anthracycline: {prior_doxo_equiv:.0f} mg/m² doxorubicin-equivalent. "
                            f"Adjusted {drug.drug_name} lifetime limit: {own_limit_adjusted:.0f} mg/m²; "
                            f"estimated remaining: {remaining_own:.0f} mg/m². "
                            f"Monitor cardiac function (LVEF) closely."
                        ),
                        drug_id=drug.drug_id
                    ))
        
        # Bleomycin cumulative dose
        if patient.prior_bleomycin_units:
            for drug in protocol.drugs:
                if drug.drug_name.lower() == 'bleomycin':
                    remaining = 400000 - patient.prior_bleomycin_units
                    if remaining <= 0:
                        warnings.append(Warning(
                            level="critical",
                            message=f"⚠️ CUMULATIVE TOXICITY: Patient has received {patient.prior_bleomycin_units} units "
                                    f"prior bleomycin. Lifetime limit (400,000 units) EXCEEDED. Pulmonary fibrosis risk is very high.",
                            drug_id=drug.drug_id
                        ))
        
        return warnings
    
    def _check_irradiated_blood(self, protocol: Protocol) -> list[Warning]:
        """Check if protocol requires irradiated blood products"""
        warnings = []
        
        for drug in protocol.drugs:
            if drug.drug_name.lower() in IRRADIATED_BLOOD_DRUGS:
                warnings.append(Warning(
                    level="critical",
                    message=f"⚠️ IRRADIATED BLOOD REQUIRED: {drug.drug_name} causes permanent T-cell immunosuppression. "
                            f"Patient requires IRRADIATED BLOOD PRODUCTS FOR LIFE. Alert transfusion department and issue patient card."
                ))
        
        return warnings
    
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
        
        # Default: use main protocol drugs, but apply cycle-aware day trimming
        adjusted_drugs = self._adjust_days_for_cycle(protocol.drugs, cycle_number)
        adjusted_take_home = self._adjust_days_for_cycle(protocol.take_home_medicines, cycle_number)
        return (adjusted_drugs, adjusted_take_home, [])

    def _adjust_days_for_cycle(
        self, drugs: list[ProtocolDrug], cycle_number: int
    ) -> list[ProtocolDrug]:
        """
        Filter and adjust drug list for the current cycle number.

        Two operations:
        1. Omit drug entries that are explicitly "Cycle 1 only" when cycle > 1
           (e.g. loading doses of Pertuzumab, Trastuzumab, Rituximab 375mg CLL,
            Cetuximab 400mg loading, Blinatumomab 9mcg step-up, Calcium Carbonate
            phosphate binder during ramp-up).
        2. Trim drug.days arrays when notes specify a cycle-specific day pattern
           (e.g. Fulvestrant Day 1+15 cycle 1 → Day 1 only cycle 2+).
        """
        import re, copy

        # Patterns that definitively mark a drug entry as cycle-1-only.
        # U+2013 en-dash, U+2014 em-dash included alongside ASCII hyphen.
        CYCLE1_ONLY_PATTERNS = [
            # Notes/name START with "CYCLE 1 ONLY:" / "Cycle 1 only." / "Cycle 1 only —"
            re.compile(r'^\s*cycle\s+1\s+only\s*[:\.\-\u2013\u2014]', re.IGNORECASE),
            # Notes start with "LOADING DOSE - Cycle 1"
            re.compile(r'^\s*loading\s+dose\s*[\-\u2013\u2014]\s*cycle\s+1', re.IGNORECASE),
            # Notes start with "Cycle 1 (week 1) loading dose"
            re.compile(r'^\s*cycle\s+1\s*\([^)]*\)\s*loading\s+dose', re.IGNORECASE),
            # Drug name contains "loading dose - Cycle 1"
            re.compile(r'loading\s+dose\s*[\-\u2013\u2014]\s*cycle\s+1', re.IGNORECASE),
            # "cycle 1 only" ends/closes the first sentence
            # e.g. "Calcium carbonate ... starting on day 1 of cycle 1 only."
            # Split on '. [Capital]' to get first sentence, then check end of it.
            # (Cannot use [^.;] because doses like "1.5g" contain periods.)
            re.compile(r'cycle\s+1\s+only\W*$', re.IGNORECASE),
        ]

        adjusted = []
        for drug in drugs:
            notes = (drug.special_instructions or "") + " " + (getattr(drug, "notes", "") or "")
            drug_name_lower = drug.drug_name.lower()

            # --- Step 1: Omit cycle-1-only drug entries for cycle > 1 ---
            if cycle_number >= 2:
                is_cycle1_only = False
                # Extract first sentence from notes for sentence-end pattern (#4)
                first_sentence = re.split(r'\.\s+[A-Z]', notes)[0] if notes.strip() else ""
                for pattern in CYCLE1_ONLY_PATTERNS[:-1]:
                    if pattern.search(notes) or pattern.search(drug.drug_name):
                        is_cycle1_only = True
                        break
                # Last pattern: "cycle 1 only" at end of first sentence only
                if not is_cycle1_only and CYCLE1_ONLY_PATTERNS[-1].search(first_sentence):
                    is_cycle1_only = True
                if is_cycle1_only:
                    continue  # Drop this drug entry entirely for cycles > 1

            # --- Step 2: Trim days for "Cycle 1 only: D1+D15; Cycle 2 onwards: D1" ---
            if cycle_number >= 2:
                notes_lower = notes.lower()
                onwards_match = re.search(
                    r'cycle\s+2\s+onwards?\s*:?\s*(?:given\s+on\s+)?day\s+1\b',
                    notes_lower
                )
                cycle1_days_match = re.search(
                    r'cycle\s+1\s+only\s*:?\s*(?:given\s+on\s+days?\s+[\d,\s]+and\s+\d+)',
                    notes_lower
                )
                if onwards_match and cycle1_days_match and drug.days and len(drug.days) > 1:
                    drug = copy.copy(drug)
                    drug.days = [1]

            adjusted.append(drug)
        return adjusted

    def _cycle_in_range(self, cycle: int, range_str: str) -> bool:
        """Check if cycle number is in range like '2-5' or '6+'"""
        if '+' in range_str:
            start = int(range_str.replace('+', ''))
            return cycle >= start
        if '-' in range_str:
            parts = range_str.split('-')
            return int(parts[0]) <= cycle <= int(parts[1])
        return cycle == int(range_str)
    
    def _should_include_drug(
        self, drug: ProtocolDrug, request: ProtocolRequest, patient: PatientData = None
    ) -> bool:
        """
        Check if a drug should be included based on request filters and safety.
        
        Note: Allergy checking is done separately to provide proper warnings.
        This method handles administrative exclusions.
        """
        
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
        modification_rules: list[DoseModificationRule],
        protocol: Optional["Protocol"] = None
    ) -> tuple[Optional[CalculatedDose], list[Warning], list[str]]:
        """
        Calculate the actual dose for a drug.
        
        SAFETY CRITICAL: Max dose caps for certain drugs (e.g., vincristine)
        are life-critical and must trigger CRITICAL alerts, not info.
        """
        
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

        # Zero/null dose — drug is dosed "per label" (e.g. CAR-T products, "H2 antagonist per local formulary")
        # Return as-is with unit "per label"; no arithmetic possible
        if not base_dose:
            note = drug.special_instructions or "Dose per prescriber / product label"
            return CalculatedDose(
                drug_id=drug.drug_id,
                drug_name=drug.drug_name,
                original_dose=0,
                original_dose_unit=str(dose_unit.value) if hasattr(dose_unit, 'value') else str(dose_unit),
                calculated_dose=0,
                calculated_dose_unit="per label",
                route=str(drug.route.value) if hasattr(drug.route, 'value') else str(drug.route),
                days=drug.days,
                duration_minutes=drug.duration_minutes,
                diluent=drug.diluent,
                diluent_volume_ml=drug.diluent_volume_ml,
                timing=drug.timing,
                frequency=drug.frequency,
                special_instructions=note,
                prn=drug.prn,
                dose_modified=False,
                modification_reason=None,
                modification_percent=None,
                banded_dose=None,
            ), warnings, modifications

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
        
        dose_modified = False
        modification_reason = None
        modification_percent = None

        # SAFETY: Apply max dose cap if specified
        # CRITICAL for drugs like vincristine where overdose = death/permanent injury
        if drug.max_dose:
            if calculated_dose > drug.max_dose + 1e-9:  # epsilon for floating point
                drug_name_lower = drug.drug_name.lower()
                pre_cap_dose = calculated_dose

                # Determine if this is a CRITICAL max dose drug
                is_critical = drug_name_lower in CRITICAL_MAX_DOSE_DRUGS

                # Cap unit: always use the flat unit (mg), not mg/m²
                cap_unit = drug.max_dose_unit or final_unit

                if is_critical:
                    critical_info = CRITICAL_MAX_DOSE_DRUGS[drug_name_lower]
                    warnings.append(Warning(
                        level="critical",
                        message=f"⚠️ CRITICAL MAX DOSE CAP: {drug.drug_name} capped at {drug.max_dose} {cap_unit} "
                                f"(calculated: {pre_cap_dose:.3f} {cap_unit} from {drug.dose}{drug.dose_unit.value if hasattr(drug.dose_unit,'value') else drug.dose_unit} × BSA). "
                                f"{critical_info['reason']}. VERIFY this cap is appropriate for this patient.",
                        drug_id=drug.drug_id
                    ))
                else:
                    warnings.append(Warning(
                        level="warning",
                        message=f"{drug.drug_name}: dose capped at {drug.max_dose} {cap_unit} "
                                f"(calculated: {pre_cap_dose:.1f} {cap_unit})",
                        drug_id=drug.drug_id
                    ))

                # HARD CAP
                calculated_dose = drug.max_dose
                effective_max_dose = drug.max_dose
                # Record this as a modification so the output is transparent
                dose_modified = True
                modification_reason = f"Max dose cap: {drug.max_dose} {cap_unit} (calculated: {pre_cap_dose:.1f} {cap_unit})"
                modification_percent = round((drug.max_dose / pre_cap_dose) * 100)
                modifications.append(f"{drug.drug_name}: capped at {drug.max_dose}{cap_unit} (was {pre_cap_dose:.1f}{cap_unit})")
        else:
            effective_max_dose = None
        
        # Apply dose modifications based on lab values
        # SAFETY: Use "most conservative" approach for multiple modifications
        best_mod_factor = 1.0
        best_mod_desc = None
        all_mod_reasons = []
        
        def _drug_matches_rule(drug_id: str, drug_name: str, affected: list) -> bool:
            """Normalised match: handles 'all', case differences, AI-extraction variants."""
            if not affected:
                return False
            id_norm = drug_id.lower().replace(" ", "_").replace("-", "_")
            name_norm = drug_name.lower().replace(" ", "_").replace("-", "_")
            for d in affected:
                d_norm = str(d).lower().replace(" ", "_").replace("-", "_")
                if d_norm == "all":
                    return True
                if d_norm in (id_norm, name_norm):
                    return True
                if d_norm in id_norm or d_norm in name_norm:
                    return True
            return False

        for rule in modification_rules:
            if _drug_matches_rule(drug.drug_id, drug.drug_name, rule.affected_drugs):
                mod_applied, mod_factor, mod_desc = self._apply_modification_rule(
                    rule, patient
                )
                if mod_applied:
                    if mod_factor == 0:
                        # Omit drug - this takes precedence over everything
                        return None, [Warning(
                            level="critical",
                            message=f"⚠️ {drug.drug_name} OMITTED: {mod_desc}",
                            drug_id=drug.drug_id
                        )], [f"{drug.drug_name}: OMITTED - {mod_desc}"]
                    
                    # SAFETY: Use "most conservative" approach
                    # Take the lowest (most aggressive reduction) factor
                    all_mod_reasons.append(mod_desc)
                    if mod_factor < best_mod_factor:
                        best_mod_factor = mod_factor
                        best_mod_desc = mod_desc
        
        # Apply the single most conservative dose modification
        if best_mod_factor < 1.0:
            calculated_dose *= best_mod_factor
            dose_modified = True
            modification_reason = best_mod_desc
            modification_percent = int(best_mod_factor * 100)
            modifications.append(f"{drug.drug_name}: {best_mod_desc}")

            # If multiple modifications applied, warn about using most conservative
            if len(all_mod_reasons) > 1:
                warnings.append(Warning(
                    level="info",
                    message=f"{drug.drug_name}: Multiple dose modifications applicable ({', '.join(all_mod_reasons)}). "
                            f"Using most conservative: {best_mod_desc} ({modification_percent}% of dose).",
                    drug_id=drug.drug_id
                ))

        # Apply age-based modifications (structured rules from protocol)
        if protocol is not None and protocol.age_based_modifications:
            calculated_dose, age_warnings, age_mods = self._apply_age_based_modifications(
                drug, patient, calculated_dose, protocol, bsa
            )
            if age_mods:
                dose_modified = True
                modification_reason = age_mods[-1]
                modification_percent = None  # set by the method if applicable
                modifications.extend(age_mods)
                warnings.extend(age_warnings)

        # Elderly fallback: protocol says "consider dose reduction" but specifies no percentage.
        # SOPHIA must NOT invent a specific reduction factor — emit a warning and leave dose unchanged.
        elif (
            protocol is not None
            and patient.elderly_patient
            and not protocol.age_based_modifications
            and dose_unit in (DoseUnit.MG_M2, DoseUnit.G_M2, DoseUnit.MCG_M2, DoseUnit.UNITS_M2)
            and drug.is_core_drug
        ):
            warnings.append(Warning(
                level="warning",
                message=(
                    f"{drug.drug_name}: patient age {patient.age_years} years — protocol recommends "
                    f"considering dose reduction in patients >70 but specifies no percentage. "
                    f"Full dose calculated. Prescriber must decide whether to reduce."
                ),
                drug_id=drug.drug_id
            ))

        # Apply manual override
        if override:
            if override.custom_dose is not None:
                # SAFETY: Prevent override from exceeding max dose
                if effective_max_dose and override.custom_dose > effective_max_dose:
                     drug_name_lower = drug.drug_name.lower()
                     if drug_name_lower in CRITICAL_MAX_DOSE_DRUGS:
                         # CRITICAL: Reject override
                         warnings.append(Warning(
                             level="critical",
                             message=f"FAILED OVERRIDE: Cannot override {drug.drug_name} to {override.custom_dose}. "
                                     f"Strict safety cap is {effective_max_dose}. Keeping capped dose.",
                             drug_id=drug.drug_id
                         ))
                         # Do NOT apply the override
                         dose_modified = True # It IS modified from original calc, but it stands at max
                     else:
                         # Soft cap - warn but maybe allow? Plan says "HARD CAP with no override".
                         # We will enforce hard cap for consistency in this safety pass.
                         warnings.append(Warning(
                             level="critical",
                             message=f"SAFETY OVERRIDE BLOCKED: {drug.drug_name} cannot exceed max dose of {effective_max_dose}. "
                                     f"Override to {override.custom_dose} ignored.",
                             drug_id=drug.drug_id
                         ))
                         # Keep calculated_dose as effective_max_dose
                else:
                    calculated_dose = override.custom_dose
                    dose_modified = True
                    modification_reason = "Manual override"
                    warnings.append(Warning(
                        level="warning",
                        message=f"{drug.drug_name}: Manual override applied. Dose set to {override.custom_dose}. Verify appropriateness.",
                        drug_id=drug.drug_id
                    ))
            elif override.dose_percent is not None:
                calculated_dose *= (override.dose_percent / 100)
                dose_modified = True
                modification_reason = f"Manual override ({override.dose_percent}%)"
                modification_percent = override.dose_percent
        
        # Round dose appropriately
        calculated_dose = self._round_dose(calculated_dose, final_unit)

        # Apply dose banding if applicable
        banded_dose = self._apply_dose_banding(calculated_dose, drug.drug_name, final_unit)

        # Strip cycle-prior instruction blocks from drug notes for later cycles.
        # e.g. Venetoclax notes contain "CYCLE 1 RAMP-UP (days 1-28): ... CYCLE 2 ONWARDS: ..."
        # For cycle ≥ 2 the ramp-up block is irrelevant and creates cognitive load on the printed sheet.
        drug_instructions = self._filter_cycle_instructions(
            drug.special_instructions, request.cycle_number
        )

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
            special_instructions=drug_instructions,
            prn=drug.prn,
            dose_modified=dose_modified,
            modification_reason=modification_reason,
            modification_percent=modification_percent,
            banded_dose=banded_dose
        ), warnings, modifications
    
    def _apply_modification_rule(
        self, rule: DoseModificationRule, patient: PatientData
    ) -> tuple[bool, float, str]:
        """
        Apply a dose modification rule, returns (applied, factor, description).
        Enhanced to support new comprehensive rule format from Gemini extraction.
        """
        
        # Get the patient value for the parameter
        param_map = {
            "neutrophils": patient.neutrophils,
            "platelets": patient.platelets,
            "bilirubin": patient.bilirubin,
            "creatinine_clearance": patient.creatinine_clearance,
            "gfr": patient.creatinine_clearance,  # GFR alias
            "creatinine": getattr(patient, 'creatinine', None),
            "ast": patient.ast,
            "alt": patient.alt,
            "hemoglobin": patient.hemoglobin,
            "wbc": getattr(patient, 'wbc', None),
            "lymphocytes": getattr(patient, 'lymphocytes', None),
        }
        
        param_key = rule.parameter.lower().replace(" ", "_")
        value = param_map.get(param_key)
        if value is None:
            return False, 1.0, ""
        
        # Use enhanced condition evaluation
        condition_met = evaluate_condition(value, rule)
        
        if not condition_met:
            return False, 1.0, ""
        
        # Get modification factor using enhanced function
        factor = get_modification_factor(rule)
        
        # Use action_text if available (more nurse-friendly), fallback to description
        description = rule.action_text if rule.action_text else rule.description
        if not description:
            # Generate description from modification type
            if factor == 0:
                description = f"{rule.parameter} {rule.condition}: drug omitted"
            elif factor < 1.0:
                description = f"{rule.parameter} {rule.condition}: dose reduced to {int(factor * 100)}%"
            else:
                description = f"{rule.parameter} condition met"
        
        return True, factor, description
    
    def _round_dose(self, dose: float, unit: str) -> float:
        """
        Round dose to appropriate precision.
        SAFETY FIX: Always use 2 decimal places for mg/units to avoid rounding errors.
        Pharmacy can round further if needed for specific products.
        """
        return round(dose, 2)
    
    def _apply_dose_banding(
        self, dose: float, drug_name: str, unit: str
    ) -> Optional[float]:
        """Apply dose banding for certain drugs (national standards).
        Based on NHS dose banding guidance — pharmacy dispenses banded doses."""

        drug_lower = drug_name.lower()

        def band_to(dose: float, increment: float) -> float:
            """Round to nearest increment; never round down to zero."""
            banded = round(round(dose / increment) * increment, 2)
            return banded if banded > 0 else increment

        if "rituximab" in drug_lower:
            # Rituximab: nearest 100mg
            if unit == "mg":
                remainder = dose % 100
                if remainder >= 50:
                    return dose + (100 - remainder)
                return dose - remainder

        if "azacitidine" in drug_lower:
            # Azacitidine: national bands in 25mg increments (100mg vials)
            if unit == "mg":
                return band_to(dose, 25)

        if "gemcitabine" in drug_lower:
            # Gemcitabine: nearest 200mg
            if unit == "mg":
                return band_to(dose, 200)

        if "carboplatin" in drug_lower:
            # Carboplatin: nearest 50mg
            if unit == "mg":
                return band_to(dose, 50)

        if "oxaliplatin" in drug_lower:
            # Oxaliplatin: nearest 5mg
            if unit == "mg":
                return band_to(dose, 5)

        if "cisplatin" in drug_lower:
            # Cisplatin: nearest 10mg
            if unit == "mg":
                return band_to(dose, 10)

        if "docetaxel" in drug_lower or "paclitaxel" in drug_lower:
            # Taxanes: nearest 5mg
            if unit == "mg":
                return band_to(dose, 5)

        if "cyclophosphamide" in drug_lower:
            # Cyclophosphamide: nearest 100mg
            if unit == "mg":
                return band_to(dose, 100)

        if "doxorubicin" in drug_lower or "epirubicin" in drug_lower:
            # Anthracyclines: nearest 5mg
            if unit == "mg":
                return band_to(dose, 5)

        if "pemetrexed" in drug_lower:
            # Pemetrexed: nearest 50mg
            if unit == "mg":
                return band_to(dose, 50)

        if "irinotecan" in drug_lower:
            # Irinotecan: nearest 10mg
            if unit == "mg":
                return band_to(dose, 10)

        if "etoposide" in drug_lower:
            # Etoposide: nearest 25mg
            if unit == "mg":
                return band_to(dose, 25)

        if "fluorouracil" in drug_lower or "5-fu" in drug_lower:
            # 5-FU: nearest 50mg (high doses) or 25mg; use 50mg as standard
            if unit == "mg":
                return band_to(dose, 50)

        if "methotrexate" in drug_lower:
            # Methotrexate: nearest 50mg (high-dose), 5mg (low-dose <100mg)
            if unit == "mg":
                if dose >= 100:
                    return band_to(dose, 50)
                return band_to(dose, 5)

        if "cytarabine" in drug_lower:
            # Cytarabine: nearest 50mg (standard dose), 100mg (high dose)
            if unit == "mg":
                if dose >= 500:
                    return band_to(dose, 100)
                return band_to(dose, 50)

        if "fludarabine" in drug_lower:
            # Fludarabine IV: nearest 10mg
            if unit == "mg":
                return band_to(dose, 10)

        if "vincristine" in drug_lower or "vinblastine" in drug_lower or "vinorelbine" in drug_lower:
            # Vinca alkaloids: nearest 0.5mg; minimum 0.5mg (cannot draw <0.5mg accurately)
            if unit == "mg":
                banded = band_to(dose, 0.5)
                return max(banded, 0.5)

        if "melphalan" in drug_lower:
            # Melphalan: nearest 10mg
            if unit == "mg":
                return band_to(dose, 10)

        if "ifosfamide" in drug_lower or "mesna" in drug_lower:
            # Ifosfamide/Mesna: nearest 500mg for high doses, 100mg for small doses
            # (Mesna can be given as small fractionated doses e.g. 120 mg/m² priming)
            if unit == "mg":
                if dose >= 250:
                    return band_to(dose, 500)
                return band_to(dose, 100)
            if unit == "g":
                return band_to(dose, 0.5)

        if "bendamustine" in drug_lower:
            # Bendamustine: nearest 25mg
            if unit == "mg":
                return band_to(dose, 25)

        if "cetuximab" in drug_lower or "bevacizumab" in drug_lower or "trastuzumab" in drug_lower:
            # Monoclonal antibodies: nearest 50mg
            if unit == "mg":
                return band_to(dose, 50)

        if "topotecan" in drug_lower:
            # Topotecan: nearest 0.5mg
            if unit == "mg":
                return band_to(dose, 0.5)

        if "mitomycin" in drug_lower:
            # Mitomycin: nearest 2mg
            if unit == "mg":
                return band_to(dose, 2)

        if "daunorubicin" in drug_lower or "liposomal" in drug_lower:
            # Daunorubicin / liposomal doxorubicin: nearest 5mg
            if unit == "mg":
                return band_to(dose, 5)

        if "temozolomide" in drug_lower:
            # Temozolomide oral: nearest 5mg
            if unit == "mg":
                return band_to(dose, 5)

        if "chlorambucil" in drug_lower:
            # Chlorambucil: nearest 2mg
            if unit == "mg":
                return band_to(dose, 2)

        return None

    def _filter_cycle_instructions(
        self, instructions: Optional[str], cycle_number: int
    ) -> Optional[str]:
        """
        Strip past-cycle instruction blocks from drug special_instructions.

        Handles the pattern:
          "CYCLE 1 RAMP-UP (days 1-28): ... CYCLE 2 ONWARDS (days 1-28): ..."

        For cycle >= 2, remove the CYCLE 1 block entirely and keep only the
        CYCLE 2 ONWARDS portion (and any trailing general instructions).
        For cycle == 1, return instructions unchanged.
        """
        if not instructions or cycle_number <= 1:
            return instructions

        import re

        # Pattern: "CYCLE 1 <label> (<...>): <text up to next CYCLE N block>"
        # We look for any "CYCLE <n> ..." header where n < current cycle and strip it.
        # Strategy: split on CYCLE N headers, keep only blocks whose cycle >= current cycle
        # or blocks that have no cycle header (general instructions appended after).

        # Split text on "CYCLE <n>" headers (case-insensitive)
        parts = re.split(r'(CYCLE\s+\d+[^:]*:)', instructions, flags=re.IGNORECASE)
        # parts alternates: [pre_text, header1, body1, header2, body2, ...]

        if len(parts) <= 1:
            # No CYCLE headers found — nothing to filter
            return instructions

        result_parts = []

        # First element is any text before the first CYCLE header
        pre_text = parts[0].strip()

        i = 1
        while i < len(parts):
            header = parts[i]
            body = parts[i + 1] if i + 1 < len(parts) else ""
            i += 2

            # Extract cycle number from this header
            m = re.search(r'CYCLE\s+(\d+)', header, re.IGNORECASE)
            if not m:
                result_parts.append(header + body)
                continue

            block_cycle = int(m.group(1))

            # Check for "ONWARDS" — this block applies to cycle block_cycle and beyond
            is_onwards = bool(re.search(r'onwards?', header, re.IGNORECASE))

            if is_onwards:
                # Include if current cycle >= block_cycle
                if cycle_number >= block_cycle:
                    result_parts.append(header + body)
            else:
                # Exact cycle block — include only if current cycle == block_cycle
                if cycle_number == block_cycle:
                    result_parts.append(header + body)
                # else: skip this past-cycle block

        # Reassemble
        kept = "".join(result_parts).strip()

        # Always include any general instructions that follow the last CYCLE block
        # (already captured in the body of the last matched part)

        if pre_text and kept:
            return pre_text + " " + kept
        return kept or pre_text or instructions

    def _apply_age_based_modifications(
        self, drug: ProtocolDrug, patient: PatientData, calculated_dose: float, 
        protocol: Protocol, bsa: float
    ) -> tuple[float, list[Warning], list[str]]:
        """
        Apply age-based modifications from protocol's age_based_modifications.
        Returns (modified_dose, warnings, modifications_applied)
        """
        warnings = []
        modifications = []
        
        for rule in protocol.age_based_modifications:
            # Check if this drug is affected
            if rule.affected_drugs and drug.drug_id not in rule.affected_drugs and drug.drug_name not in rule.affected_drugs:
                continue
            
            # Check age condition
            age = patient.age_years
            age_threshold = rule.age_threshold
            op = rule.operator
            
            age_matches = False
            if op == ">" and age > age_threshold:
                age_matches = True
            elif op == ">=" and age >= age_threshold:
                age_matches = True
            elif op == "<" and age < age_threshold:
                age_matches = True
            elif op == "<=" and age <= age_threshold:
                age_matches = True
            
            if not age_matches:
                continue
            
            # Apply modification
            if rule.modification_type == "cap" and rule.cap_dose is not None:
                if calculated_dose > rule.cap_dose:
                    old_dose = calculated_dose
                    calculated_dose = rule.cap_dose
                    cap_unit = rule.cap_unit or "mg"
                    modifications.append(f"{drug.drug_name}: capped at {rule.cap_dose}{cap_unit} due to age >{age_threshold}")
                    warnings.append(Warning(
                        level="warning",
                        message=f"{drug.drug_name}: dose capped at {rule.cap_dose}{cap_unit} "
                               f"(calculated: {old_dose:.1f}) for patient age {age}. {rule.description}",
                        drug_id=drug.drug_id
                    ))
            
            elif rule.modification_type == "reduce" and rule.reduction_percent is not None:
                factor = (100 - rule.reduction_percent) / 100.0
                old_dose = calculated_dose
                calculated_dose *= factor
                modifications.append(f"{drug.drug_name}: reduced by {rule.reduction_percent}% due to age")
                warnings.append(Warning(
                    level="warning",
                    message=f"{drug.drug_name}: dose reduced by {rule.reduction_percent}% "
                           f"(from {old_dose:.1f} to {calculated_dose:.1f}) for patient age {age}. {rule.description}",
                    drug_id=drug.drug_id
                ))
            
            # Check for cardioprotectant recommendation
            if rule.recommendation == "cardioprotectant" and rule.cardioprotectant_drug:
                # Check if cumulative anthracycline trigger condition is met
                if rule.trigger_condition:
                    # Simple check for anthracycline drugs
                    drug_lower = drug.drug_name.lower()
                    if drug_lower in ANTHRACYCLINE_EQUIVALENCE:
                        warnings.append(Warning(
                            level="warning",
                            message=f"Patient age {age} < 26: Consider {rule.cardioprotectant_drug} as cardioprotectant "
                                   f"if cumulative anthracycline exceeds 300 mg/m². {rule.description}",
                            drug_id=drug.drug_id
                        ))
        
        return calculated_dose, warnings, modifications
    
    def _check_non_hematological_toxicities(
        self, protocol: Protocol, patient_toxicities: dict
    ) -> list[Warning]:
        """
        Check for non-hematological toxicities that affect dosing.
        patient_toxicities is a dict like {"motor_weakness": True, "gross_hematuria": False}
        """
        warnings = []
        
        for rule in protocol.non_hematological_toxicity_rules:
            toxicity_key = rule.toxicity_type.lower().replace(" ", "_")
            has_toxicity = patient_toxicities.get(toxicity_key, False)
            
            if has_toxicity:
                affected_str = ", ".join(rule.affected_drugs) if rule.affected_drugs else "affected drugs"
                action_text = rule.action_text if rule.action_text else f"Consider {rule.action} for {affected_str}"
                
                level = "warning"
                if rule.action in ("omit", "hold"):
                    level = "critical"
                
                warnings.append(Warning(
                    level=level,
                    message=f"⚠️ {rule.toxicity_type.upper()}: {action_text}"
                ))
        
        return warnings
    
    def _check_metabolic_monitoring(
        self, protocol: Protocol, baseline_values: dict, current_values: dict
    ) -> list[Warning]:
        """
        Check for metabolic changes (HbA1c, glucose) that exceed thresholds.
        """
        warnings = []
        
        for rule in protocol.metabolic_monitoring:
            param = rule.parameter.lower()
            baseline = baseline_values.get(param)
            current = current_values.get(param)
            
            if baseline is None or current is None or baseline == 0:
                continue
            
            change_percent = abs(current - baseline) / baseline * 100
            
            if rule.change_threshold_percent and change_percent >= rule.change_threshold_percent:
                action_text = rule.action_text if rule.action_text else f"{param} has changed by ≥{rule.change_threshold_percent}% from baseline"
                warnings.append(Warning(
                    level="warning",
                    message=action_text
                ))
        
        return warnings
    
    def _check_cumulative_toxicity_limits(
        self, protocol: Protocol, patient: PatientData, bsa: float
    ) -> list[Warning]:
        """
        Check cumulative toxicity limits (anthracyclines, bleomycin) and generate warnings.
        """
        warnings = []
        
        for tracking in protocol.cumulative_toxicity_tracking:
            # Identify which drugs in protocol are affected
            affected_drugs_in_protocol = []
            for drug in protocol.drugs:
                drug_lower = drug.drug_name.lower()
                if tracking.drug and drug_lower == tracking.drug.lower():
                    affected_drugs_in_protocol.append(drug)
                elif tracking.drugs and drug_lower in [d.lower() for d in tracking.drugs]:
                    affected_drugs_in_protocol.append(drug)
            
            if not affected_drugs_in_protocol:
                continue
            
            # Calculate projected cumulative dose
            prior_dose = getattr(patient, 'prior_anthracycline_dose_mg_m2', 0) or 0
            
            # Calculate dose per cycle for this protocol
            dose_per_cycle = 0
            for drug in affected_drugs_in_protocol:
                if drug.dose_unit == DoseUnit.MG_M2:
                    dose_per_cycle += drug.dose * len(drug.days)  # Sum all days in a cycle
                elif drug.dose_unit == DoseUnit.MG:
                    dose_per_cycle += drug.dose / bsa * len(drug.days)  # Convert flat to mg/m2
            
            projected_total = prior_dose + (dose_per_cycle * protocol.total_cycles)
            
            # Check against limits
            limit = tracking.standard_limit_mg_m2 or tracking.lifetime_limit or 450
            
            # Check reduced limits
            for reduced in tracking.reduced_limits:
                if "cardiac" in reduced.condition.lower() and getattr(patient, 'prior_cardiac_history', False):
                    limit = min(limit, reduced.limit)
                elif "age" in reduced.condition.lower() and ">70" in reduced.condition and patient.age_years > 70:
                    limit = min(limit, reduced.limit)
                elif "age" in reduced.condition.lower() and "> 70" in reduced.condition and patient.age_years > 70:
                    limit = min(limit, reduced.limit)
            
            if projected_total > limit:
                warnings.append(Warning(
                    level="critical",
                    message=f"⚠️ CUMULATIVE TOXICITY EXCEEDED: {tracking.drug_class or tracking.drug} "
                           f"limit ({limit} {tracking.limit_unit}) will be exceeded. "
                           f"Prior: {prior_dose:.1f}, Projected total: {projected_total:.1f} {tracking.limit_unit}. "
                           f"{tracking.alert_text}"
                ))
            elif projected_total > limit * (tracking.warning_at_percent / 100):
                warnings.append(Warning(
                    level="warning",
                    message=f"Approaching {tracking.drug_class or tracking.drug} lifetime limit. "
                           f"Prior: {prior_dose:.1f} {tracking.limit_unit}, "
                           f"Projected: {projected_total:.1f} {tracking.limit_unit} (limit: {limit}). "
                           f"{tracking.alert_text}"
                ))
        
        return warnings

    def _filter_cycle_specific_instructions(
        self, instructions: list[str], cycle_number: int
    ) -> list[str]:
        """
        Filter out special instructions that only apply to past cycles.
        e.g. 'ECG at day 14 of cycle 1 and start of cycle 2' should not appear on cycle 6.
        Keeps the instruction if it is general (no specific cycle mentioned) or
        if it references a cycle >= the current cycle_number.
        """
        filtered = []
        import re

        # Patterns that indicate a cycle-specific past instruction
        # Match "cycle 1", "cycle 2", "first cycle", "second cycle", "cycles 1-2" etc.
        cycle_ref_pattern = re.compile(
            r'cycle[s]?\s+(\d+)(?:\s*[-–]\s*(\d+))?|'
            r'(first|second|third)\s+cycle[s]?|'
            r'day\s+14\s+of\s+cycle\s+(\d+)',
            re.IGNORECASE
        )

        for instruction in instructions:
            matches = list(cycle_ref_pattern.finditer(instruction))
            if not matches:
                # No cycle reference — always relevant
                filtered.append(instruction)
                continue

            # Find the highest cycle number referenced in this instruction
            max_referenced_cycle = 0
            for m in matches:
                # "cycle N" or "cycles N-M"
                if m.group(1):
                    max_referenced_cycle = max(max_referenced_cycle, int(m.group(1)))
                if m.group(2):
                    max_referenced_cycle = max(max_referenced_cycle, int(m.group(2)))
                # "day 14 of cycle N"
                if m.group(4):
                    max_referenced_cycle = max(max_referenced_cycle, int(m.group(4)))
                # "first/second/third cycle"
                word_map = {"first": 1, "second": 2, "third": 3}
                if m.group(3):
                    max_referenced_cycle = max(max_referenced_cycle, word_map.get(m.group(3).lower(), 0))

            if max_referenced_cycle == 0 or max_referenced_cycle >= cycle_number:
                # Either can't determine or still relevant for current/future cycle
                filtered.append(instruction)
            # else: all cycle references are in the past — omit this instruction

        return filtered

    def _extract_mandatory_concurrent_meds(
        self, instructions: list[str], cycle_number: int
    ) -> list[Warning]:
        """
        Detect warnings about mandatory concurrent medications that are NOT in the
        protocol drug list (e.g. LHRH agonist for ribociclib in pre/peri-menopausal).
        Returns Warning objects so the clinician sees them in the warnings panel,
        not just buried in instructions.
        """
        warnings = []
        lhrh_keywords = ["lhrh agonist", "gnrh agonist", "ovarian suppression", "ovarian ablation"]

        for instruction in instructions:
            instr_lower = instruction.lower()
            if any(kw in instr_lower for kw in lhrh_keywords):
                if "mandatory" in instr_lower or "required" in instr_lower or "must" in instr_lower:
                    warnings.append(Warning(
                        level="critical",
                        message=(
                            "⚠️ MANDATORY CONCURRENT MEDICATION: LHRH agonist / ovarian suppression "
                            "is required for pre- or peri-menopausal patients on this regimen. "
                            "Confirm this is prescribed and being administered. "
                            "It is NOT included in this protocol output."
                        )
                    ))
                    break  # Only add once even if mentioned multiple times

        return warnings

    def _generate_blinatumomab_bag_schedule(
        self, request: ProtocolRequest, cycle_number: int
    ) -> list[BlinatumomabBagEntry]:
        """
        Generate the alternating 72/96-hour bag-change schedule for blinatumomab.

        Per NHS UHS protocol (Blinatumomab 3,4 day schedule):
          - Volume: 275 ml sodium chloride 0.9%
          - Rate: 2.5 ml/hr
          - Bag content: 9mcg/day = 41.25mcg in 275ml; 28mcg/day = 133.75mcg in 275ml
          - Bags alternate: ODD bags (1st, 3rd, 5th, 7th) run 72 hours then DISCARD
                            EVEN bags (2nd, 4th, 6th, 8th) run 96 hours
          - Treatment must start Monday, Tuesday or Friday

        Schedule:
          Cycle 1 : Days 1–7  at 9mcg  (bags 1–4: 72h, 96h, 72h, 96h = 3+4+3+4=14 days?
                                         actually 7 days = bag1 72h + bag2 partial...)
                    Days 8–28 at 28mcg
          Cycles 2+: Days 1–28 at 28mcg

        Alternating pattern over 28 days:
          Bag 1: days 1–3   (72h)   ODD  → discard at 72h
          Bag 2: days 4–7   (96h)   EVEN → run full 96h
          Bag 3: days 8–10  (72h)   ODD  → discard at 72h
          Bag 4: days 11–14 (96h)   EVEN → run full 96h
          Bag 5: days 15–17 (72h)   ODD  → discard at 72h
          Bag 6: days 18–21 (96h)   EVEN → run full 96h
          Bag 7: days 22–24 (72h)   ODD  → discard at 72h
          Bag 8: days 25–28 (96h)   EVEN → run full 96h
          Total: 8 bags covering 28 days exactly

        Returns a list of BlinatumomabBagEntry objects.
        """
        # NHS standard: 275ml bag, 2.5ml/hr
        TOTAL_VOL_ML = 275.0
        RATE = 2.5

        # Drug content per bag per NHS PDF
        BAG_CONFIGS = {
            9.0:  {"total_mcg": 41.25},
            28.0: {"total_mcg": 133.75},
        }

        # Alternating bag durations: odd=72h (3 days), even=96h (4 days)
        # Pattern repeats: [3, 4, 3, 4, 3, 4, 3, 4] = 28 days, 8 bags
        BAG_PATTERN = [3, 4, 3, 4, 3, 4, 3, 4]

        # Cycle 1 dose per day: days 1-7 at 9mcg, days 8-28 at 28mcg
        # Cycle 2+: all 28 days at 28mcg
        def dose_for_day(day_1indexed: int) -> float:
            if cycle_number == 1:
                return 9.0 if day_1indexed <= 7 else 28.0
            return 28.0

        # Parse start date and enforce Mon/Tue/Fri rule
        start_date = None
        start_date_warning = None
        VALID_WEEKDAYS = {0: "Monday", 1: "Tuesday", 4: "Friday"}  # Mon=0, Tue=1, Fri=4
        NEXT_VALID = {
            # Wed → Fri (+2), Thu → Fri (+1), Sat → Mon (+2), Sun → Mon (+1)
            2: 2, 3: 1, 5: 2, 6: 1
        }
        if request.treatment_start_date:
            try:
                from datetime import date as date_cls
                start_date = date_cls.fromisoformat(request.treatment_start_date)
                wd = start_date.weekday()
                if wd not in VALID_WEEKDAYS:
                    advance = NEXT_VALID[wd]
                    corrected = start_date + timedelta(days=advance)
                    start_date_warning = (
                        f"START DATE ERROR: {start_date.strftime('%d.%m.%Y')} is a "
                        f"{start_date.strftime('%A')}. Blinatumomab must start on a "
                        f"Monday, Tuesday or Friday (bag-change logistics). "
                        f"Nearest valid date is {corrected.strftime('%A %d.%m.%Y')}. "
                        f"Bag schedule below uses the corrected date."
                    )
                    start_date = corrected
            except ValueError:
                pass

        bags = []
        current_day_offset = 0  # 0-indexed day offset from treatment start

        for bag_idx, bag_days in enumerate(BAG_PATTERN):
            bag_number = bag_idx + 1
            is_odd = (bag_number % 2 == 1)
            duration_h = 72 if is_odd else 96

            # Dominant dose = dose at first day of this bag
            day_1indexed = current_day_offset + 1
            dose_mcg = dose_for_day(day_1indexed)
            cfg = BAG_CONFIGS[dose_mcg]

            if start_date:
                bag_start = start_date + timedelta(days=current_day_offset)
                bag_end = bag_start + timedelta(days=bag_days)
                date_start_str = bag_start.strftime("%d.%m.%y")
                date_end_str = bag_end.strftime("%d.%m.%y")
            else:
                d1 = current_day_offset + 1
                d2 = current_day_offset + bag_days
                date_start_str = f"Day {d1}"
                date_end_str = f"Day {d2}"

            bags.append(BlinatumomabBagEntry(
                bag_number=bag_number,
                date_start=date_start_str,
                date_end=date_end_str,
                dose_mcg_per_day=dose_mcg,
                total_dose_mcg=cfg["total_mcg"],
                vials=0,  # not applicable — prepared by pharmacy to exact mcg
                ns_volume_ml=TOTAL_VOL_ML,
                stabilizer_volume_ml=0.0,
                total_volume_ml=TOTAL_VOL_ML,
                rate_ml_per_hr=RATE,
                duration_hours=duration_h,
            ))
            current_day_offset += bag_days

        return bags, start_date_warning

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
        
        # Elevated bilirubin — tiered severity
        if patient.bilirubin is not None:
            bili = patient.bilirubin
            # Check if protocol contains hepatically-metabolised drugs
            hepatic_drugs = [d.drug_name for d in protocol.drugs
                             if any(x in d.drug_name.lower() for x in
                                    ['doxorubicin', 'epirubicin', 'daunorubicin', 'idarubicin',
                                     'vincristine', 'vinblastine', 'vinorelbine', 'paclitaxel',
                                     'docetaxel', 'irinotecan', 'etoposide', 'fluorouracil',
                                     'oxaliplatin', 'cyclophosphamide'])]
            if bili > 85:
                warnings.append(Warning(
                    level="critical",
                    message=(
                        f"⚠️ SEVERE HEPATIC IMPAIRMENT: Bilirubin {bili:.0f} µmol/L (>85). "
                        f"Hepatically-metabolised drugs may be contraindicated. "
                        f"{'Drugs affected: ' + ', '.join(hepatic_drugs) + '. ' if hepatic_drugs else ''}"
                        f"Review individual drug SPCs. Consider dose omission for anthracyclines and vinca alkaloids. "
                        f"PRESCRIBER MUST REVIEW BEFORE DISPENSING."
                    )
                ))
            elif bili > 51:
                warnings.append(Warning(
                    level="critical",
                    message=(
                        f"⚠️ SIGNIFICANT HEPATIC IMPAIRMENT: Bilirubin {bili:.0f} µmol/L (>51). "
                        f"Dose reductions required for hepatically-metabolised drugs "
                        f"({'including: ' + ', '.join(hepatic_drugs) if hepatic_drugs else 'review protocol'}). "
                        f"Typical reductions: anthracyclines 50-75%, vinca alkaloids 50%. REVIEW BEFORE DISPENSING."
                    )
                ))
            elif bili > 30:
                warnings.append(Warning(
                    level="warning",
                    message=(
                        f"Elevated bilirubin ({bili:.0f} µmol/L). "
                        f"Review hepatic dose modifications for protocol drugs."
                    )
                ))

        # Low CrCl — tiered severity
        if patient.creatinine_clearance is not None:
            crcl = patient.creatinine_clearance
            # Check for renally-excreted drugs in this protocol
            renal_drugs = [d.drug_name for d in protocol.drugs
                           if any(x in d.drug_name.lower() for x in
                                  ['cisplatin', 'carboplatin', 'methotrexate', 'bleomycin',
                                   'pemetrexed', 'gemcitabine', 'capecitabine', 'fludarabine',
                                   'melphalan', 'cyclophosphamide', 'ifosfamide', 'etoposide'])]
            if crcl < 30:
                warnings.append(Warning(
                    level="critical",
                    message=(
                        f"⚠️ SEVERE RENAL IMPAIRMENT: CrCl {crcl:.0f} ml/min (<30). "
                        f"{'Cisplatin is CONTRAINDICATED at CrCl <60 ml/min. ' if any('cisplatin' in d.lower() for d in renal_drugs) else ''}"
                        f"{'Renally-cleared drugs in this protocol: ' + ', '.join(renal_drugs) + '. ' if renal_drugs else ''}"
                        f"Dose reductions or omissions required. PRESCRIBER MUST REVIEW BEFORE DISPENSING."
                    )
                ))
            elif crcl < 60:
                # Only critical if cisplatin involved
                if any('cisplatin' in d.lower() for d in renal_drugs):
                    warnings.append(Warning(
                        level="critical",
                        message=(
                            f"⚠️ RENAL IMPAIRMENT: CrCl {crcl:.0f} ml/min. "
                            f"Cisplatin is CONTRAINDICATED at CrCl <60 ml/min. PRESCRIBER MUST REVIEW."
                        )
                    ))
                elif renal_drugs:
                    warnings.append(Warning(
                        level="warning",
                        message=(
                            f"Reduced renal function (CrCl {crcl:.0f} ml/min). "
                            f"Review dose modifications for: {', '.join(renal_drugs)}."
                        )
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
