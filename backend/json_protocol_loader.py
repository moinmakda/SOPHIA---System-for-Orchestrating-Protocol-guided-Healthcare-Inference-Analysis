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

    return ProtocolDrug(
        drug_id=_slugify(drug_name),
        drug_name=drug_name,
        dose=dose,
        dose_unit=_map_dose_unit(d.get("dose_unit")),
        route=_map_route(d.get("route")),
        days=d.get("days") or [1],
        duration_minutes=duration_minutes,
        diluent=d.get("diluent"),
        diluent_volume_ml=d.get("diluent_volume_ml"),
        is_core_drug=not is_premed,
        max_dose=d.get("max_dose"),
        max_dose_unit=d.get("max_dose_unit"),
        special_instructions=notes,
        frequency=d.get("frequency"),
    )


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

    action = dm.get("action", "delay")
    if factor == 0:
        mod_type = "omit"
    elif factor < 1.0:
        mod_type = "reduce"
    else:
        mod_type = "delay"

    description = dm.get("notes", "") or dm.get("condition", "") or ""
    condition = dm.get("condition", "") or ""
    parameter = dm.get("parameter", "") or ""

    return DoseModificationRule(
        rule_id="",
        parameter=parameter,
        condition=condition,
        affected_drugs=affected,
        modification_type=mod_type,
        modification_percent=int(round(factor * 100)) if factor < 1.0 else None,
        description=description,
        action_text=description,
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

        # Pre-medications
        raw_premeds = p.get("pre_medications") or []
        premeds = []
        for d in raw_premeds:
            try:
                premeds.append(_convert_drug(d, is_premed=True))
            except Exception:
                pass

        # Take-home medicines
        raw_takehome = p.get("take_home_medicines") or []
        take_home = []
        for d in raw_takehome:
            try:
                take_home.append(_convert_drug(d, is_premed=True))
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
