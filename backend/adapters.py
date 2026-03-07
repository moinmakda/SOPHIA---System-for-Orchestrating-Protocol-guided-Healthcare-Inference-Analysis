"""
Patient State Adapter
Converts external 'Patient Journey' JSONs (e.g. from mobile app / WhatsApp forms)
into strict PatientData objects for use in the engine.
Handles data cleaning, unit conversion, and cycle-state logic.
"""

import re
from typing import Any, Dict, Optional
from models import PatientData, ECOGPerformanceStatus, LabUnitSystem


class PatientStateAdapter:

    @staticmethod
    def _parse_range_value(value: Any) -> Optional[float]:
        """
        Parse values like "0.5-<1", "10-20", or raw floats.
        Returns the LOWER bound (conservative) for safety checks.
        Returns None if unparseable.
        """
        if isinstance(value, (int, float)):
            return float(value)
        if not value or not isinstance(value, str):
            return None
        matches = re.findall(r"(\d+\.?\d*)", str(value).strip())
        if matches:
            return float(min(matches, key=float))
        return None

    @staticmethod
    def _get_latest_completed_cycle(data: Dict[str, Any]) -> int:
        """Find the index of the last completed cycle."""
        cycle = 0
        while data.get(f"cycle{cycle + 1}_complete") is True:
            cycle += 1
        return cycle

    @staticmethod
    def adapt(data: Dict[str, Any], target_cycle: Optional[int] = None) -> PatientData:
        """
        Convert an external patient JSON dict to a PatientData model instance.

        Args:
            data: Source JSON dict (from mobile app, WhatsApp form, etc.)
            target_cycle: Which cycle to generate for. Inferred from completion flags if None.

        Raises:
            ValueError: If mandatory fields are missing/invalid.
        """
        last_completed = PatientStateAdapter._get_latest_completed_cycle(data)
        current_cycle = target_cycle if target_cycle is not None else (last_completed + 1)

        # Determine lab source prefix (post-cycle labs vs baseline)
        prefix = ""
        if current_cycle > 1:
            candidate = f"post{last_completed}"
            if f"{candidate}neutrophils" in data:
                prefix = candidate

        def get(key: str, default=None):
            val = data.get(f"{prefix}{key}")
            if val is not None and val != "":
                return val
            return data.get(key, default)

        p = PatientStateAdapter._parse_range_value

        # ---- Mandatory demographics ----
        weight = p(get("weight")) or p(data.get("weight_kg"))
        height = p(get("height")) or p(data.get("height_cm"))
        age = int(data.get("age", data.get("age_years", 0)))

        if not weight or weight <= 0:
            raise ValueError("Patient weight is missing or invalid")
        if not height or height <= 0:
            raise ValueError("Patient height is missing or invalid")

        # ---- Mandatory labs ----
        neutrophils = p(get("neutrophils"))
        platelets = p(get("platelets"))
        hb = p(get("hemoglobin")) or p(get("hb"))
        bilirubin = p(get("bilirubin"))
        crcl = (
            p(get("creatinine_clearance"))
            or p(get("gfr"))
            or p(get(f"post{last_completed}crcl") if last_completed else None)
            or p(get("post1crcl"))
        )

        if neutrophils is None:
            raise ValueError("Neutrophil count is required")
        if platelets is None:
            raise ValueError("Platelet count is required")
        if hb is None:
            raise ValueError("Haemoglobin is required")
        if bilirubin is None:
            raise ValueError("Bilirubin is required")
        if crcl is None:
            raise ValueError("Creatinine clearance / GFR is required")

        # ---- Performance status ----
        ps_raw = data.get("performance_status", 0)
        try:
            ps = ECOGPerformanceStatus(int(ps_raw))
        except (ValueError, KeyError):
            ps = ECOGPerformanceStatus.FULLY_ACTIVE

        # ---- Optional labs ----
        def opt_float(val):
            return p(val) if val is not None else None

        kwargs: Dict[str, Any] = dict(
            weight_kg=weight,
            height_cm=height,
            age_years=age,
            performance_status=ps,
            neutrophils=neutrophils,
            platelets=platelets,
            hemoglobin=hb,
            creatinine_clearance=crcl,
            bilirubin=bilirubin,
            lab_unit_system=LabUnitSystem.SI,
            known_allergies=[],
            cycles_completed=last_completed,
        )

        # Optional scalar labs
        for src, dest in [
            ("ast",        "ast"),
            ("alt",        "alt"),
            ("alp",        "alp"),
            ("ldh",        "ldh"),
            ("esr",        "esr"),
            ("urate",      "urate"),
            ("calcium",    "calcium"),
            ("vitamind",   "vitamin_d"),
            ("magnesium",  "magnesium"),
            ("creatinine", "creatinine"),
            ("b2microglobulin", "beta2_microglobulin"),
            ("hba1c",      "baseline_hba1c"),
            ("glucose",    "baseline_glucose"),
        ]:
            val = opt_float(get(src))
            if val is not None:
                kwargs[dest] = val

        # Post-cycle values
        for src, dest in [
            (f"post{last_completed}gfr",        "post_cycle_gfr"),
            (f"post{last_completed}bilirubin",   "post_cycle_bilirubin"),
            (f"post{last_completed}neutrophils",  "post_cycle_neutrophils"),
            (f"post{last_completed}platelets",    "post_cycle_platelets"),
            (f"post{last_completed}hba1c",        "post_cycle_hba1c"),
            (f"post{last_completed}glucose",      "post_cycle_glucose"),
        ]:
            val = opt_float(data.get(src))
            if val is not None:
                kwargs[dest] = val

        # Boolean post-cycle flags
        if data.get(f"post{last_completed}motor_weakness"):
            kwargs["post_cycle_motor_weakness"] = True
        if data.get(f"post{last_completed}gross_hematuria"):
            kwargs["post_cycle_gross_hematuria"] = True

        # Disease characterisation
        for src, dest in [
            ("histology",  "histology"),
            ("dstage",     "disease_stage"),
            ("ct",         "ct_result"),
            ("igs",        "immunoglobulins"),
        ]:
            val = data.get(src)
            if val:
                kwargs[dest] = str(val)

        # Virology
        viro_map = {
            "hepbsurface":  "hep_b_surface_antigen",
            "hepbcore":     "hep_b_core_antibody",
            "hepcantibody": "hep_c_antibody",
            "hiv":          "hiv_status",
            "hlv1":         "htlv1_status",
            "ebv":          "ebv_status",
            "cmv":          "cmv_status",
            "vzv":          "vzv_status",
        }
        for src, dest in viro_map.items():
            val = data.get(src)
            if val in ("positive", "negative", "unknown"):
                kwargs[dest] = val

        # G6PD
        g6pd = data.get("g6pd")
        if g6pd in ("normal", "deficient", "unknown"):
            kwargs["g6pd_status"] = g6pd

        # Cardiac / prior treatment
        if data.get("heartDisease"):
            kwargs["heart_disease"] = bool(data["heartDisease"])
            kwargs["prior_cardiac_history"] = bool(data["heartDisease"])
        if data.get("lifetimedoxorubicin") is not None:
            val = opt_float(data["lifetimedoxorubicin"])
            if val is not None:
                kwargs["prior_anthracycline_dose_mg_m2"] = val

        # Lung function / smoking
        if data.get("lungFunction") is not None:
            val = opt_float(data["lungFunction"])
            if val is not None:
                kwargs["lung_function_fev1"] = val
        if data.get("smoker") is not None:
            kwargs["smoker"] = bool(data["smoker"])

        return PatientData(**kwargs)


# ---- Quick test ----
if __name__ == "__main__":
    example = {
        "name": "Test Patient",
        "age": 58,
        "height": 172,
        "weight": 80,
        "bilirubin": 12,
        "gfr": 75,
        "neutrophils": 2.1,
        "platelets": 145,
        "hemoglobin": 11.5,
        "ldh": 320,
        "hepbsurface": "negative",
        "hepbcore": "positive",
        "hiv": "negative",
        "histology": "DLBCL",
        "dstage": "Ann Arbor IV",
        "g6pd": "normal",
        "heartDisease": False,
        "lifetimedoxorubicin": 150,
        "cycle1_complete": True,
        "post1neutrophils": "0.8-<1",
        "post1platelets": 110,
        "post1bilirubin": 14,
        "post1crcl": 70,
    }
    try:
        patient = PatientStateAdapter.adapt(example)
        print("Adapted successfully:")
        print(f"  BSA: {patient.capped_bsa:.2f} m²")
        print(f"  Neutrophils (post-cycle): {patient.neutrophils}")
        print(f"  HBcAb: {patient.hep_b_core_antibody}")
        print(f"  Histology: {patient.histology}")
        print(f"  Cycles completed: {patient.cycles_completed}")
    except Exception as e:
        print(f"Failed: {e}")
