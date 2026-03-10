"""
SOPHIA JSON Protocol Loader
Loads all protocols from protocol_jsons_normalized/ and converts them
into Protocol model objects compatible with the engine.

Reads from protocol_jsons_normalized/ (normalized, safe copies).
Never touches originals in protocol_jsons/.
"""

import json
import os
import re
from pathlib import Path
from typing import Optional

from models import (
    Protocol, ProtocolDrug, DoseModificationRule,
    DoseUnit, RouteOfAdministration
)

NORMALIZED_DIR = Path(__file__).parent / "protocol_jsons_normalized"

# Map dose_unit strings to DoseUnit enum values
DOSE_UNIT_MAP = {
    "mg": DoseUnit.MG,
    "mg/m²": DoseUnit.MG_M2,
    "mg/m2": DoseUnit.MG_M2,
    "mg/kg": DoseUnit.MG_KG,
    "g": DoseUnit.G,
    "g/m²": DoseUnit.G_M2,
    "g/m2": DoseUnit.G_M2,
    "AUC": "AUC",  # handled specially
    "units": DoseUnit.UNITS,
    "units/m²": DoseUnit.UNITS_M2,
    "units/m2": DoseUnit.UNITS_M2,
    "IU/m²": DoseUnit.UNITS_M2,
    "IU/m2": DoseUnit.UNITS_M2,
    "IU": DoseUnit.UNITS,
    "mcg": DoseUnit.MCG,
    "mcg/m²": DoseUnit.MCG_M2,
    "mcg/m2": DoseUnit.MCG_M2,
    "ml": DoseUnit.ML,
}

# Map route strings to RouteOfAdministration enum values
ROUTE_MAP = {
    "IV bolus": RouteOfAdministration.IV_BOLUS,
    "IV infusion": RouteOfAdministration.IV_INFUSION,
    "Oral": RouteOfAdministration.ORAL,
    "Subcutaneous": RouteOfAdministration.SC,
    "Intramuscular": RouteOfAdministration.IM,
    "Nebulised": RouteOfAdministration.NEBULISED,
}


def _slugify(name: str) -> str:
    """Convert drug name to a safe slug for drug_id."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _map_dose_unit(raw: Optional[str]) -> str:
    if not raw:
        return DoseUnit.MG.value
    mapped = DOSE_UNIT_MAP.get(raw)
    if mapped:
        return mapped.value if hasattr(mapped, "value") else str(mapped)
    return DoseUnit.MG.value


def _map_route(raw: Optional[str]) -> str:
    if not raw:
        return RouteOfAdministration.IV_INFUSION.value
    mapped = ROUTE_MAP.get(raw)
    if mapped:
        return mapped.value
    # Fuzzy fallback
    r = raw.lower()
    if "oral" in r:
        return RouteOfAdministration.ORAL.value
    if "bolus" in r:
        return RouteOfAdministration.IV_BOLUS.value
    if "iv" in r or "intravenous" in r:
        return RouteOfAdministration.IV_INFUSION.value
    if "subcutaneous" in r or "sc" in r:
        return RouteOfAdministration.SC.value
    if "intramuscular" in r or "im" in r:
        return RouteOfAdministration.IM.value
    return RouteOfAdministration.IV_INFUSION.value


_DILUENT_NAME_MAP = {
    # sodium chloride variants
    r"sodium\s+chloride\s+0\.9%":   "Sodium chloride 0.9%",
    r"nacl\s+0\.9%":                "Sodium chloride 0.9%",
    r"normal\s+saline":             "Sodium chloride 0.9%",
    r"\bns\b":                      "Sodium chloride 0.9%",
    r"sodium\s+chloride\s+0\.45%":  "Sodium chloride 0.45%",
    # glucose / dextrose
    r"glucose\s+5%":                "Glucose 5%",
    r"dextrose\s+5%":               "Glucose 5%",
    r"5%\s+dextrose":               "Glucose 5%",
    r"glucose\s+10%":               "Glucose 10%",
    # water for injection
    r"water\s+for\s+injection":     "Water for injection",
    r"\bwfi\b":                     "Water for injection",
    # hartmann's / ringer's
    r"hartmann":                    "Hartmann's solution",
    r"ringer":                      "Ringer's lactate",
}

_DILUENT_VOL_PATTERN = re.compile(
    r'\bin\s+(\d+)\s*ml\s+(' +
    r'sodium\s+chloride\s*0\.9%|sodium\s+chloride\s*0\.45%|'
    r'nacl\s*0\.9%|normal\s+saline|glucose\s*5%|glucose\s*10%|'
    r'dextrose\s*5%|5%\s+dextrose|water\s+for\s+injection|'
    r'hartmann|ringer|ns\b)',
    re.IGNORECASE,
)


def _parse_diluent_from_notes(notes: str):
    """
    Extract (diluent_name, volume_ml) from a notes string like
    'IV infusion in 250ml sodium chloride 0.9% over 30 minutes'.
    Returns (None, None) if not found.
    """
    if not notes:
        return None, None
    m = _DILUENT_VOL_PATTERN.search(notes)
    if not m:
        return None, None
    vol = int(m.group(1))
    raw_name = m.group(2).strip()
    # Normalise name
    for pattern, canonical in _DILUENT_NAME_MAP.items():
        if re.search(pattern, raw_name, re.IGNORECASE):
            return canonical, vol
    return raw_name.capitalize(), vol


# Maps common antiemetic/premedication names to structured data
_PREMED_STRING_PATTERNS = [
    # (regex, drug_name, dose, dose_unit, route)
    (re.compile(r'aprepitant\s+125\s*mg', re.I),       'Aprepitant',       125,  'mg',  'Oral'),
    (re.compile(r'fosaprepitant\s+150\s*mg', re.I),    'Fosaprepitant',    150,  'mg',  'IV infusion'),
    (re.compile(r'ondansetron\s+8\s*mg', re.I),        'Ondansetron',      8,    'mg',  'IV bolus'),
    (re.compile(r'ondansetron\s+4\s*mg', re.I),        'Ondansetron',      4,    'mg',  'IV bolus'),
    (re.compile(r'granisetron\s+1\s*mg', re.I),        'Granisetron',      1,    'mg',  'IV bolus'),
    (re.compile(r'granisetron\s+2\s*mg', re.I),        'Granisetron',      2,    'mg',  'IV bolus'),
    (re.compile(r'dexamethasone\s+20\s*mg', re.I),     'Dexamethasone',    20,   'mg',  'IV bolus'),
    (re.compile(r'dexamethasone\s+12\s*mg', re.I),     'Dexamethasone',    12,   'mg',  'IV bolus'),
    (re.compile(r'dexamethasone\s+8\s*mg', re.I),      'Dexamethasone',    8,    'mg',  'IV bolus'),
    (re.compile(r'dexamethasone\s+4\s*mg', re.I),      'Dexamethasone',    4,    'mg',  'Oral'),
    (re.compile(r'prednisolone\s+100\s*mg', re.I),     'Prednisolone',     100,  'mg',  'Oral'),
    (re.compile(r'prednisolone\s+50\s*mg', re.I),      'Prednisolone',     50,   'mg',  'Oral'),
    (re.compile(r'prednisolone\s+40\s*mg', re.I),      'Prednisolone',     40,   'mg',  'Oral'),
    (re.compile(r'chlorphenamine\s+10\s*mg', re.I),    'Chlorphenamine',   10,   'mg',  'IV bolus'),
    (re.compile(r'chlorphenamine\s+4\s*mg', re.I),     'Chlorphenamine',   4,    'mg',  'Oral'),
    (re.compile(r'paracetamol\s+1000\s*mg', re.I),     'Paracetamol',      1000, 'mg',  'Oral'),
    (re.compile(r'paracetamol\s+500\s*mg', re.I),      'Paracetamol',      500,  'mg',  'Oral'),
    (re.compile(r'hydrocortisone\s+100\s*mg', re.I),   'Hydrocortisone',   100,  'mg',  'IV bolus'),
    (re.compile(r'ranitidine\s+50\s*mg', re.I),        'Ranitidine',       50,   'mg',  'IV bolus'),
    (re.compile(r'famotidine\s+20\s*mg', re.I),        'Famotidine',       20,   'mg',  'Oral'),
    (re.compile(r'loratadine\s+10\s*mg', re.I),        'Loratadine',       10,   'mg',  'Oral'),
    (re.compile(r'promethazine\s+25\s*mg', re.I),      'Promethazine',     25,   'mg',  'IV bolus'),
    (re.compile(r'metoclopramide\s+10\s*mg', re.I),    'Metoclopramide',   10,   'mg',  'Oral'),
    (re.compile(r'allopurinol\s+300\s*mg', re.I),      'Allopurinol',      300,  'mg',  'Oral'),
    (re.compile(r'allopurinol\s+100\s*mg', re.I),      'Allopurinol',      100,  'mg',  'Oral'),
    (re.compile(r'aciclovir\s+400\s*mg', re.I),        'Aciclovir',        400,  'mg',  'Oral'),
    (re.compile(r'co.trimoxazole\s+960\s*mg', re.I),   'Co-trimoxazole',   960,  'mg',  'Oral'),
    (re.compile(r'co.trimoxazole\s+480\s*mg', re.I),   'Co-trimoxazole',   480,  'mg',  'Oral'),
    (re.compile(r'fluconazole\s+50\s*mg', re.I),       'Fluconazole',      50,   'mg',  'Oral'),
    (re.compile(r'loperamide\s+4\s*mg', re.I),         'Loperamide',       4,    'mg',  'Oral'),
    (re.compile(r'atropine\s+250\s*mcg', re.I),        'Atropine',         250,  'mcg', 'Subcutaneous'),
    (re.compile(r'pethidine\s+25\s*mg', re.I),         'Pethidine',        25,   'mg',  'IV bolus'),
    (re.compile(r'pethidine\s+12\.5\s*mg', re.I),      'Pethidine',        12.5, 'mg',  'IV bolus'),
    (re.compile(r'salbutamol\s+2\.5\s*mg', re.I),      'Salbutamol',       2.5,  'mg',  'Nebulised'),
    (re.compile(r'salbutamol\s+5\s*mg', re.I),         'Salbutamol',       5,    'mg',  'Nebulised'),
]

# Timing/frequency patterns for string premeds
_PREMED_TIMING_RE = re.compile(
    r'(\d+[-–]\d+\s*minutes?\s+prior|prior\s+to\s+chemo\w*|before\s+chemo\w*|'
    r'stat|once\s+only|once\s+daily|bd|tds|qds|\d+\s*hrly)',
    re.I,
)

def _parse_premed_string(text: str) -> Optional[ProtocolDrug]:
    """
    Convert a free-text pre-medication string into a ProtocolDrug.
    e.g. "Ondansetron 8mg oral or IV 15-30 minutes prior to chemotherapy"
    Returns None if the string can't be parsed into a known drug.
    """
    if not text or not isinstance(text, str):
        return None
    text = text.strip()

    for pattern, drug_name, dose, dose_unit, default_route in _PREMED_STRING_PATTERNS:
        if pattern.search(text):
            # Detect route override from text
            route = default_route
            tl = text.lower()
            if 'oral' in tl:
                route = 'Oral'
            elif 'nebulised' in tl or 'nebulized' in tl:
                route = 'Nebulised'
            elif 'subcutaneous' in tl or ' sc ' in tl:
                route = 'Subcutaneous'
            elif 'intravenous' in tl or ' iv ' in tl or tl.startswith('iv'):
                route = 'IV bolus'

            # Only override to IV infusion if the drug itself is described as an infusion
            # (avoid matching "prior to ... infusion" where infusion = the chemo, not this drug)
            if re.search(r'over\s+\d+\s*min', tl):
                route = 'IV infusion'

            # Extract timing as special_instructions
            timing_m = _PREMED_TIMING_RE.search(text)
            instructions = text  # preserve full text as instruction

            return ProtocolDrug(
                drug_id=_slugify(drug_name),
                drug_name=drug_name,
                dose=float(dose),
                dose_unit=_map_dose_unit(dose_unit),
                route=_map_route(route),
                days=[1],
                duration_minutes=30 if route == 'IV infusion' else None,
                diluent='Sodium chloride 0.9%' if route == 'IV infusion' else None,
                diluent_volume_ml=100 if route == 'IV infusion' else None,
                is_core_drug=False,
                special_instructions=instructions,
                frequency=None,
            )

    # Couldn't match — return None (will be skipped)
    return None


def _convert_drug(d: dict, is_premed: bool = False) -> ProtocolDrug:
    """Convert a drug dict from JSON to a ProtocolDrug model."""
    drug_name = d.get("drug_name", "Unknown")
    dose_raw = d.get("dose") or 0.0
    dose = float(dose_raw) if dose_raw is not None else 0.0

    # Duration: prefer infusion_duration_hours; fall back to duration_minutes
    duration_hours = d.get("infusion_duration_hours")
    if duration_hours is None:
        duration_min = d.get("duration_minutes")
        if duration_min is not None:
            duration_hours = duration_min / 60
    duration_minutes = int(round(duration_hours * 60)) if duration_hours is not None else None

    # Notes: prefer 'notes', then merge special_instructions + frequency
    notes = d.get("notes")
    if not notes:
        parts = []
        freq = d.get("frequency")
        si = d.get("special_instructions")
        if freq:
            parts.append(freq)
        if si:
            parts.append(si)
        notes = " | ".join(parts) if parts else None

    # Diluent: use explicit JSON fields if present; otherwise parse from notes
    diluent = d.get("diluent")
    diluent_volume_ml = d.get("diluent_volume_ml")
    if (diluent is None or diluent_volume_ml is None) and notes:
        parsed_name, parsed_vol = _parse_diluent_from_notes(notes)
        if parsed_name and diluent is None:
            diluent = parsed_name
        if parsed_vol and diluent_volume_ml is None:
            diluent_volume_ml = parsed_vol

    return ProtocolDrug(
        drug_id=_slugify(drug_name),
        drug_name=drug_name,
        dose=dose,
        dose_unit=_map_dose_unit(d.get("dose_unit")),
        route=_map_route(d.get("route")),
        days=d.get("days") or [1],
        duration_minutes=duration_minutes,
        diluent=diluent,
        diluent_volume_ml=diluent_volume_ml,
        is_core_drug=not is_premed,
        max_dose=d.get("max_dose"),
        max_dose_unit=d.get("max_dose_unit"),
        special_instructions=notes,
        frequency=d.get("frequency"),
    )


def _parse_threshold_from_substr(substr: str, uln: float = 40.0) -> dict:
    """
    Extract a single threshold (>, <, range) from a substring.
    Handles ×ULN / xULN notation by multiplying by uln (default 40 for AST/ALT).
    Returns partial dict with condition_type + threshold fields, or {} if nothing found.
    """
    # Handle N×ULN range: e.g. "2-3×uln" or "2–3×uln"
    uln_range_m = re.search(r'(\d+(?:\.\d+)?)\s*[-]\s*(\d+(?:\.\d+)?)\s*[x×]\s*uln', substr, re.I)
    uln_gt_m    = re.search(r'>(\d+(?:\.\d+)?)\s*[x×]\s*uln', substr, re.I)
    uln_lt_m    = re.search(r'<(\d+(?:\.\d+)?)\s*[x×]\s*uln', substr, re.I)
    if uln_range_m:
        lo = float(uln_range_m.group(1)) * uln
        hi = float(uln_range_m.group(2)) * uln
        return dict(condition_type="range", threshold_low=lo, threshold_high=hi,
                    threshold_value=None)
    elif uln_gt_m:
        return dict(condition_type="greater_than", threshold_value=float(uln_gt_m.group(1)) * uln,
                    threshold_low=None, threshold_high=None)
    elif uln_lt_m:
        return dict(condition_type="less_than", threshold_value=float(uln_lt_m.group(1)) * uln,
                    threshold_low=None, threshold_high=None)

    gt_m = re.search(r'>(\d+(?:\.\d+)?)', substr)
    lt_m = re.search(r'<(\d+(?:\.\d+)?)', substr)
    range_m = re.search(r'(\d{2,}(?:\.\d+)?)\s*[-]\s*(\d{2,}(?:\.\d+)?)', substr)

    if range_m and not lt_m and not gt_m:
        lo, hi = float(range_m.group(1)), float(range_m.group(2))
        return dict(condition_type="range", threshold_low=lo, threshold_high=hi,
                    threshold_value=None)
    elif lt_m:
        return dict(condition_type="less_than", threshold_value=float(lt_m.group(1)),
                    threshold_low=None, threshold_high=None)
    elif gt_m:
        return dict(condition_type="greater_than", threshold_value=float(gt_m.group(1)),
                    threshold_low=None, threshold_high=None)
    elif "normal" in substr:
        return dict(condition_type="normal", threshold_value=None,
                    threshold_low=None, threshold_high=None)
    return {}


def _parse_dm_condition(condition_str: str) -> dict:
    """
    Parse a free-text dose modification condition string to extract structured fields.
    Handles compound AND/OR clauses, e.g.:
      "Bilirubin <30 AND AST/ALT 2-3×ULN"
      "Bilirubin >51 AND AST/ALT normal"
      "Bilirubin 30-51 OR AST/ALT 60-180"
      "Bilirubin >85 µmol/L"
      "CrCl 10-20 ml/min"
      "Neutrophils <1×10⁹/L"

    Returns dict with primary + optional secondary condition fields.
    """
    # Normalise unicode dashes and spaces
    s = condition_str.replace('–', '-').replace('—', ' ').lower()

    PARAM_KEYWORDS = [
        ('bilirubin', 'bilirubin'),
        ('crcl', 'creatinine_clearance'),
        ('creatinine clearance', 'creatinine_clearance'),
        ('gfr', 'creatinine_clearance'),
        ('neutrophil', 'neutrophils'),
        ('platelet', 'platelets'),
        ('haemoglobin', 'hemoglobin'),
        ('hemoglobin', 'hemoglobin'),
        ('ast/alt', 'ast'),   # must come before 'ast' and 'alt'
        ('ast', 'ast'),
        ('alt', 'alt'),
    ]

    parameter = ""
    for kw, canonical in PARAM_KEYWORDS:
        if kw in s:
            parameter = canonical
            break

    if not parameter:
        return {}

    result = {"parameter": parameter}

    # Locate the primary parameter in the string
    param_kw_variants = [
        parameter.replace("_", " "),
        parameter.replace("creatinine_clearance", "crcl"),
        "ast/alt" if parameter == "ast" and "ast/alt" in s else parameter,
        parameter,
    ]
    param_pos = -1
    for kw in param_kw_variants:
        p = s.find(kw)
        if p >= 0:
            param_pos = p
            break
    substr_full = s[param_pos:] if param_pos >= 0 else s

    # Detect AND / OR / AND/OR connector
    connector = ""
    andor_m = re.search(r'\s+(and/or)\s+', substr_full)
    and_m   = re.search(r'\s+(and)\s+', substr_full)
    or_m    = re.search(r'\s+(or)\s+',  substr_full)
    connector_m = None
    if andor_m:
        connector = "OR"   # AND/OR treated as OR (either condition triggers the rule)
        connector_m = andor_m
    elif and_m and (not or_m or and_m.start() < or_m.start()):
        connector = "AND"
        connector_m = and_m
    elif or_m:
        connector = "OR"
        connector_m = or_m

    # Primary clause: everything up to the connector (or full string if no connector)
    if connector_m:
        primary_substr = substr_full[:connector_m.start()]
        secondary_substr = substr_full[connector_m.end():]
    else:
        primary_substr = substr_full
        secondary_substr = ""

    # Parse primary threshold
    primary_thresh = _parse_threshold_from_substr(primary_substr)
    result.update(primary_thresh)

    # Parse secondary clause if present
    if connector and secondary_substr:
        # Identify secondary parameter
        sec_param = ""
        for kw, canonical in PARAM_KEYWORDS:
            if kw in secondary_substr:
                sec_param = canonical
                break
        if sec_param:
            sec_thresh = _parse_threshold_from_substr(secondary_substr)
            result["secondary_parameter"] = sec_param
            result["secondary_connector"] = connector
            result["secondary_condition_type"] = sec_thresh.get("condition_type", "")
            result["secondary_threshold_value"] = sec_thresh.get("threshold_value")
            result["secondary_threshold_low"] = sec_thresh.get("threshold_low")
            result["secondary_threshold_high"] = sec_thresh.get("threshold_high")

    return result


def _convert_dose_modification(dm: dict) -> DoseModificationRule:
    """Convert a dose modification dict from JSON to a DoseModificationRule model."""
    # Early-batch format: parameter, condition, affected_drugs, action, factor, notes
    # Late-batch format: condition, drug_name, factor, notes
    affected = dm.get("affected_drugs") or []
    if not affected:
        drug_name = dm.get("drug_name")
        if drug_name:
            affected = [drug_name]

    factor = dm.get("factor", 1.0)
    if factor is None:
        factor = 1.0

    if factor == 0:
        mod_type = "omit"
    elif factor < 1.0:
        mod_type = "reduce"
    else:
        mod_type = "delay"

    description = dm.get("notes", "") or dm.get("condition", "") or ""
    condition_raw = dm.get("condition", "") or ""
    parameter = dm.get("parameter", "") or ""

    # If no explicit parameter field, parse from the condition string
    parsed = {}
    if not parameter and condition_raw:
        parsed = _parse_dm_condition(condition_raw)
        parameter = parsed.get("parameter", "")

    return DoseModificationRule(
        rule_id="",
        parameter=parameter,
        condition=condition_raw,
        condition_type=parsed.get("condition_type", "less_than"),
        threshold_value=parsed.get("threshold_value"),
        threshold_low=parsed.get("threshold_low"),
        threshold_high=parsed.get("threshold_high"),
        affected_drugs=affected,
        modification_type=mod_type,
        modification_percent=int(round(factor * 100)) if factor < 1.0 else None,
        description=description,
        action_text=description,
        secondary_parameter=parsed.get("secondary_parameter", ""),
        secondary_connector=parsed.get("secondary_connector", ""),
        secondary_condition_type=parsed.get("secondary_condition_type", ""),
        secondary_threshold_value=parsed.get("secondary_threshold_value"),
        secondary_threshold_low=parsed.get("secondary_threshold_low"),
        secondary_threshold_high=parsed.get("secondary_threshold_high"),
    )


def _convert_protocol(p: dict, source_file: str) -> Optional[Protocol]:
    """Convert a single protocol dict to a Protocol model. Returns None on failure."""
    try:
        code = p.get("protocol_code", "")
        name = p.get("protocol_name", "")
        protocol_id = p.get("protocol_id") or _slugify(code or name)

        # Drugs: use 'drugs' key (normalized files always have this)
        raw_drugs = p.get("drugs") or p.get("chemotherapy_drugs") or []
        drugs = []
        for d in raw_drugs:
            try:
                drugs.append(_convert_drug(d))
            except Exception:
                pass  # Skip malformed drug entries

        # Pre-medications — entries may be dicts (structured) or strings (free-text)
        raw_premeds = p.get("pre_medications") or []
        premeds = []
        for d in raw_premeds:
            try:
                if isinstance(d, dict):
                    premeds.append(_convert_drug(d, is_premed=True))
                elif isinstance(d, str):
                    parsed = _parse_premed_string(d)
                    if parsed:
                        premeds.append(parsed)
            except Exception:
                pass

        # Take-home medicines — same dual-format handling
        raw_takehome = p.get("take_home_medicines") or []
        take_home = []
        for d in raw_takehome:
            try:
                if isinstance(d, dict):
                    take_home.append(_convert_drug(d, is_premed=True))
                elif isinstance(d, str):
                    parsed = _parse_premed_string(d)
                    if parsed:
                        take_home.append(parsed)
            except Exception:
                pass

        # Rescue medications — same dual-format handling
        raw_rescue = p.get("rescue_medications") or []
        rescue = []
        for d in raw_rescue:
            try:
                if isinstance(d, dict):
                    rescue.append(_convert_drug(d, is_premed=True))
                elif isinstance(d, str):
                    parsed = _parse_premed_string(d)
                    if parsed:
                        rescue.append(parsed)
            except Exception:
                pass

        # Dose modifications
        raw_dm = p.get("dose_modifications") or []
        dose_mods = []
        for dm in raw_dm:
            try:
                dose_mods.append(_convert_dose_modification(dm))
            except Exception:
                pass

        # Warnings
        warnings = p.get("special_warnings") or []
        if isinstance(warnings, str):
            warnings = [warnings]

        # Cycle count
        num_cycles = p.get("number_of_cycles") or p.get("total_cycles") or 6
        if num_cycles is None:
            num_cycles = 6

        # Required patient fields — values may be bool (early-batch) or str
        rpf_raw = p.get("required_patient_fields") or {}
        if isinstance(rpf_raw, list):
            rpf = {item: "" for item in rpf_raw}
        elif isinstance(rpf_raw, dict):
            rpf = {k: str(v) if not isinstance(v, str) else v for k, v in rpf_raw.items()}
        else:
            rpf = {}

        protocol = Protocol(
            protocol_id=protocol_id,
            protocol_name=name,
            protocol_code=code,
            indication=p.get("indication", ""),
            cycle_length_days=p.get("cycle_length_days") or 21,
            total_cycles=int(num_cycles) if num_cycles else 6,
            treatment_intent=p.get("treatment_intent", ""),
            drugs=drugs,
            pre_medications=premeds,
            take_home_medicines=take_home,
            rescue_medications=rescue,
            dose_modifications=dose_mods,
            warnings=warnings,
            required_patient_fields=rpf,
            is_ai_generated=True,
            source_file=source_file,
        )
        return protocol
    except Exception as e:
        print(f"[JSON LOADER] Failed to convert {p.get('protocol_code', '?')}: {e}")
        return None


def load_all_json_protocols() -> dict[str, Protocol]:
    """
    Load all protocols from protocol_jsons_normalized/.
    Returns dict keyed by protocol_code.
    """
    if not NORMALIZED_DIR.exists():
        print(f"[JSON LOADER] Normalized dir not found: {NORMALIZED_DIR}")
        return {}

    result: dict[str, Protocol] = {}
    json_files = sorted(NORMALIZED_DIR.glob("*.json"))
    loaded = 0
    skipped = 0

    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                continue
            for p in data:
                protocol = _convert_protocol(p, source_file=json_file.name)
                if protocol and protocol.code:
                    result[protocol.code] = protocol
                    loaded += 1
                else:
                    skipped += 1
        except Exception as e:
            print(f"[JSON LOADER] Error reading {json_file.name}: {e}")

    print(f"[JSON LOADER] Loaded {loaded} protocols from {len(json_files)} files ({skipped} skipped)")
    return result
