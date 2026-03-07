"""
NHS Lymphoma Protocol Data
Extracted and structured from NHS chemotherapy protocol PDFs
"""

from models import (
    Protocol, ProtocolDrug, DoseModificationRule, Toxicity,
    CycleVariation, DoseUnit, RouteOfAdministration, Drug, DrugCategory
)


# ============= DRUG DEFINITIONS =============

DRUGS = {
    "rituximab": Drug(
        id="rituximab",
        name="Rituximab",
        generic_name="Rituximab",
        category=DrugCategory.IMMUNOTHERAPY,
        aliases=["Rituxan", "MabThera"],
        requires_bsa=True,
        special_warnings=[
            "Check hepatitis B status before starting",
            "Risk of cytokine release syndrome",
            "Risk of progressive multifocal leukoencephalopathy (PML)"
        ]
    ),
    "cyclophosphamide": Drug(
        id="cyclophosphamide",
        name="Cyclophosphamide",
        generic_name="Cyclophosphamide",
        category=DrugCategory.CHEMOTHERAPY,
        aliases=["Cytoxan", "Endoxan"],
        requires_bsa=True,
        special_warnings=["Risk of haemorrhagic cystitis", "Ensure adequate hydration"]
    ),
    "doxorubicin": Drug(
        id="doxorubicin",
        name="Doxorubicin",
        generic_name="Doxorubicin",
        category=DrugCategory.CHEMOTHERAPY,
        aliases=["Adriamycin"],
        vesicant=True,
        requires_bsa=True,
        special_warnings=[
            "Cardiotoxic - monitor LVEF",
            "Discontinue if cardiac failure develops",
            "Cumulative dose limit applies"
        ]
    ),
    "vincristine": Drug(
        id="vincristine",
        name="Vincristine",
        generic_name="Vincristine",
        category=DrugCategory.CHEMOTHERAPY,
        aliases=["Oncovin"],
        vesicant=True,
        requires_bsa=True,
        max_dose=2.0,
        max_dose_unit="mg",
        special_warnings=["Risk of peripheral neuropathy", "Max single dose 2mg"]
    ),
    "prednisolone": Drug(
        id="prednisolone",
        name="Prednisolone",
        generic_name="Prednisolone",
        category=DrugCategory.STEROID,
        aliases=["Prednisone"],
        default_route=RouteOfAdministration.ORAL,
        requires_bsa=False
    ),
    "bendamustine": Drug(
        id="bendamustine",
        name="Bendamustine",
        generic_name="Bendamustine",
        category=DrugCategory.CHEMOTHERAPY,
        aliases=["Treanda", "Levact"],
        vesicant=True,
        requires_bsa=True,
        special_warnings=[
            "Lifelong requirement for irradiated blood products",
            "Risk of Stevens-Johnson syndrome with allopurinol"
        ]
    ),
    "etoposide": Drug(
        id="etoposide",
        name="Etoposide",
        generic_name="Etoposide",
        category=DrugCategory.CHEMOTHERAPY,
        aliases=["VP-16", "Vepesid"],
        requires_bsa=True
    ),
    "obinutuzumab": Drug(
        id="obinutuzumab",
        name="Obinutuzumab",
        generic_name="Obinutuzumab",
        category=DrugCategory.IMMUNOTHERAPY,
        aliases=["Gazyva"],
        requires_bsa=False,
        special_warnings=["High risk of infusion reactions on first dose"]
    ),
    "chlorphenamine": Drug(
        id="chlorphenamine",
        name="Chlorphenamine",
        generic_name="Chlorphenamine",
        category=DrugCategory.PREMEDICATION,
        default_route=RouteOfAdministration.IV_BOLUS,
        requires_bsa=False
    ),
    "paracetamol": Drug(
        id="paracetamol",
        name="Paracetamol",
        generic_name="Paracetamol",
        category=DrugCategory.PREMEDICATION,
        default_route=RouteOfAdministration.ORAL,
        requires_bsa=False
    ),
    "ondansetron": Drug(
        id="ondansetron",
        name="Ondansetron",
        generic_name="Ondansetron",
        category=DrugCategory.ANTIEMETIC,
        aliases=["Zofran"],
        requires_bsa=False
    ),
    "metoclopramide": Drug(
        id="metoclopramide",
        name="Metoclopramide",
        generic_name="Metoclopramide",
        category=DrugCategory.ANTIEMETIC,
        aliases=["Maxolon"],
        default_route=RouteOfAdministration.ORAL,
        requires_bsa=False
    ),
    "hydrocortisone": Drug(
        id="hydrocortisone",
        name="Hydrocortisone",
        generic_name="Hydrocortisone",
        category=DrugCategory.STEROID,
        requires_bsa=False
    ),
    "allopurinol": Drug(
        id="allopurinol",
        name="Allopurinol",
        generic_name="Allopurinol",
        category=DrugCategory.SUPPORTIVE,
        default_route=RouteOfAdministration.ORAL,
        requires_bsa=False
    ),
    "cotrimoxazole": Drug(
        id="cotrimoxazole",
        name="Co-trimoxazole",
        generic_name="Sulfamethoxazole/Trimethoprim",
        category=DrugCategory.SUPPORTIVE,
        default_route=RouteOfAdministration.ORAL,
        requires_bsa=False,
        special_warnings=["PCP prophylaxis"]
    ),
    "salbutamol": Drug(
        id="salbutamol",
        name="Salbutamol",
        generic_name="Salbutamol",
        category=DrugCategory.RESCUE,
        default_route=RouteOfAdministration.NEBULISED,
        requires_bsa=False
    ),
    "gemcitabine": Drug(
        id="gemcitabine",
        name="Gemcitabine",
        generic_name="Gemcitabine",
        category=DrugCategory.CHEMOTHERAPY,
        aliases=["Gemzar"],
        requires_bsa=True
    ),
    "cisplatin": Drug(
        id="cisplatin",
        name="Cisplatin",
        generic_name="Cisplatin",
        category=DrugCategory.CHEMOTHERAPY,
        aliases=["Platinol"],
        requires_bsa=True,
        special_warnings=["Nephrotoxic - ensure adequate hydration", "Ototoxic"]
    ),
    "carboplatin": Drug(
        id="carboplatin",
        name="Carboplatin",
        generic_name="Carboplatin",
        category=DrugCategory.CHEMOTHERAPY,
        aliases=["Paraplatin"],
        requires_bsa=True
    ),
    "dexamethasone": Drug(
        id="dexamethasone",
        name="Dexamethasone",
        generic_name="Dexamethasone",
        category=DrugCategory.STEROID,
        default_route=RouteOfAdministration.ORAL,
        requires_bsa=False
    ),
    "ifosfamide": Drug(
        id="ifosfamide",
        name="Ifosfamide",
        generic_name="Ifosfamide",
        category=DrugCategory.CHEMOTHERAPY,
        aliases=["Ifex"],
        requires_bsa=True,
        special_warnings=["Requires mesna for uroprotection"]
    ),
    "bleomycin": Drug(
        id="bleomycin",
        name="Bleomycin",
        generic_name="Bleomycin",
        category=DrugCategory.CHEMOTHERAPY,
        requires_bsa=True,
        special_warnings=["Pulmonary toxicity - monitor lung function"]
    ),
    "dacarbazine": Drug(
        id="dacarbazine",
        name="Dacarbazine",
        generic_name="Dacarbazine",
        category=DrugCategory.CHEMOTHERAPY,
        aliases=["DTIC"],
        requires_bsa=True
    ),
    "vinblastine": Drug(
        id="vinblastine",
        name="Vinblastine",
        generic_name="Vinblastine",
        category=DrugCategory.CHEMOTHERAPY,
        vesicant=True,
        requires_bsa=True
    ),
    "brentuximab": Drug(
        id="brentuximab",
        name="Brentuximab vedotin",
        generic_name="Brentuximab vedotin",
        category=DrugCategory.TARGETED,
        aliases=["Adcetris"],
        requires_bsa=True,
        special_warnings=["Risk of peripheral neuropathy", "Risk of PML"]
    ),
    "polatuzumab": Drug(
        id="polatuzumab",
        name="Polatuzumab vedotin",
        generic_name="Polatuzumab vedotin",
        category=DrugCategory.TARGETED,
        aliases=["Polivy"],
        requires_bsa=True
    ),
    # --- Supportive / Prophylaxis ---
    "fluconazole": Drug(
        id="fluconazole",
        name="Fluconazole",
        generic_name="Fluconazole",
        category=DrugCategory.SUPPORTIVE,
        aliases=["Diflucan"],
        requires_bsa=False,
        special_warnings=["Check for CYP2C9/CYP3A4 drug interactions", "Monitor LFTs on prolonged use"]
    ),
    "aciclovir": Drug(
        id="aciclovir",
        name="Aciclovir",
        generic_name="Aciclovir",
        category=DrugCategory.SUPPORTIVE,
        aliases=["Acyclovir", "Zovirax"],
        requires_bsa=False,
        special_warnings=["Dose-adjust for renal impairment", "Maintain adequate hydration"]
    ),
    "mesna": Drug(
        id="mesna",
        name="Mesna",
        generic_name="Mesna",
        category=DrugCategory.SUPPORTIVE,
        aliases=["Uromitexan"],
        requires_bsa=True,
        special_warnings=["Uroprotectant — administer with ifosfamide or high-dose cyclophosphamide"]
    ),
    "gcsf": Drug(
        id="gcsf",
        name="G-CSF (Filgrastim / Pegfilgrastim)",
        generic_name="Filgrastim",
        category=DrugCategory.SUPPORTIVE,
        aliases=["Filgrastim", "Pegfilgrastim", "Neupogen", "Neulasta", "G-CSF"],
        requires_bsa=False,
        special_warnings=["Do not give within 24h before or after cytotoxic chemotherapy", "Monitor FBC"]
    ),
    "omeprazole": Drug(
        id="omeprazole",
        name="Omeprazole",
        generic_name="Omeprazole",
        category=DrugCategory.SUPPORTIVE,
        aliases=["Losec"],
        requires_bsa=False
    ),
    "aspirin": Drug(
        id="aspirin",
        name="Aspirin",
        generic_name="Aspirin",
        category=DrugCategory.SUPPORTIVE,
        aliases=["Acetylsalicylic acid"],
        requires_bsa=False
    ),
    "loperamide": Drug(
        id="loperamide",
        name="Loperamide",
        generic_name="Loperamide",
        category=DrugCategory.SUPPORTIVE,
        aliases=["Imodium"],
        requires_bsa=False
    ),
    "rasburicase": Drug(
        id="rasburicase",
        name="Rasburicase",
        generic_name="Rasburicase",
        category=DrugCategory.SUPPORTIVE,
        aliases=["Fasturtec"],
        requires_bsa=True,
        special_warnings=["Contraindicated in G6PD deficiency — can cause haemolytic anaemia", "Check G6PD before prescribing"]
    ),
    "leucovorin": Drug(
        id="leucovorin",
        name="Leucovorin (Folinic acid)",
        generic_name="Folinic acid",
        category=DrugCategory.SUPPORTIVE,
        aliases=["Folinic acid", "Calcium folinate", "Leucovorin rescue"],
        requires_bsa=False,
        special_warnings=["Mandatory rescue after high-dose methotrexate — timing is critical"]
    ),
    # --- Alkylating agents ---
    "chlorambucil": Drug(
        id="chlorambucil",
        name="Chlorambucil",
        generic_name="Chlorambucil",
        category=DrugCategory.CHEMOTHERAPY,
        aliases=["Leukeran"],
        requires_bsa=False,
        special_warnings=["Oral — take on empty stomach", "Myelosuppression — monitor FBC weekly"]
    ),
    "ifosfamide_hd": Drug(
        id="ifosfamide_hd",
        name="Ifosfamide (high-dose)",
        generic_name="Ifosfamide",
        category=DrugCategory.CHEMOTHERAPY,
        aliases=["Mitoxana"],
        requires_bsa=True,
        special_warnings=["Always co-prescribe MESNA uroprotection", "Risk of encephalopathy — monitor neurological status", "Dose-adjust for renal impairment"]
    ),
    # --- Antimetabolites ---
    "cytarabine": Drug(
        id="cytarabine",
        name="Cytarabine (Ara-C)",
        generic_name="Cytarabine",
        category=DrugCategory.CHEMOTHERAPY,
        aliases=["Ara-C", "AraC", "cytosine arabinoside"],
        requires_bsa=True,
        special_warnings=["High-dose: mandatory prophylactic steroid eye drops", "Risk of cerebellar toxicity at high doses — check coordination daily", "Severe myelosuppression"]
    ),
    "cytarabine_hd": Drug(
        id="cytarabine_hd",
        name="Cytarabine (High-Dose, HiDAC)",
        generic_name="Cytarabine",
        category=DrugCategory.CHEMOTHERAPY,
        aliases=["HiDAC", "HIDAC", "high-dose Ara-C"],
        requires_bsa=True,
        special_warnings=["MANDATORY steroid eye drops (dexamethasone 0.1%)", "Cerebellar toxicity — daily coordination checks (finger-nose test)", "Severe myelosuppression — requires inpatient admission"]
    ),
    "idarubicin": Drug(
        id="idarubicin",
        name="Idarubicin",
        generic_name="Idarubicin",
        category=DrugCategory.CHEMOTHERAPY,
        aliases=["Zavedos"],
        requires_bsa=True,
        special_warnings=["Anthracycline — track cumulative dose (lifetime limit ~135 mg/m²)", "Cardiotoxic — ECHO before treatment", "Vesicant — confirm central line patency"]
    ),
    "daunorubicin": Drug(
        id="daunorubicin",
        name="Daunorubicin",
        generic_name="Daunorubicin",
        category=DrugCategory.CHEMOTHERAPY,
        aliases=["Cerubidin", "daunomycin"],
        requires_bsa=True,
        special_warnings=["Anthracycline — track cumulative dose (lifetime limit ~550 mg/m²)", "Cardiotoxic — ECHO before treatment", "Vesicant — confirm central line patency"]
    ),
    "fludarabine": Drug(
        id="fludarabine",
        name="Fludarabine",
        generic_name="Fludarabine",
        category=DrugCategory.CHEMOTHERAPY,
        aliases=["Fludara"],
        requires_bsa=True,
        special_warnings=["Profoundly immunosuppressive — irradiated blood products required for life", "TLS risk — allopurinol prophylaxis mandatory", "Dose-adjust for renal impairment"]
    ),
    "methotrexate_hd": Drug(
        id="methotrexate_hd",
        name="Methotrexate (High-Dose)",
        generic_name="Methotrexate",
        category=DrugCategory.CHEMOTHERAPY,
        aliases=["HD-MTX", "HDMTX", "high-dose methotrexate"],
        requires_bsa=True,
        special_warnings=["MANDATORY leucovorin rescue — timing critical", "Urinary alkalinisation required (pH >7)", "Monitor MTX levels at 24h, 48h, 72h post-infusion", "Renal impairment prolongs elimination — dose-adjust or avoid"]
    ),
    # --- Targeted / Novel agents ---
    "imatinib": Drug(
        id="imatinib",
        name="Imatinib",
        generic_name="Imatinib",
        category=DrugCategory.TARGETED,
        aliases=["Gleevec", "Glivec", "STI571"],
        requires_bsa=False,
        special_warnings=["TKI — check BCR-ABL mutation status", "CYP3A4 substrate: many drug interactions", "QTc monitoring", "Oedema — monitor weight and fluid status"]
    ),
    "venetoclax": Drug(
        id="venetoclax",
        name="Venetoclax",
        generic_name="Venetoclax",
        category=DrugCategory.TARGETED,
        aliases=["Venclyxto", "ABT-199"],
        requires_bsa=False,
        special_warnings=["HIGH RISK of Tumour Lysis Syndrome — mandatory ramp-up schedule", "Strong CYP3A4 inhibitors increase venetoclax levels — check ALL drugs", "Antifungals (esp. posaconazole/voriconazole) require dose reduction to 70mg", "TLS prophylaxis mandatory (allopurinol ± rasburicase)", "Hospitalisation for ramp-up in high-risk patients"]
    ),
    "azacitidine": Drug(
        id="azacitidine",
        name="Azacitidine",
        generic_name="Azacitidine",
        category=DrugCategory.CHEMOTHERAPY,
        aliases=["Vidaza", "5-azacitidine", "5-AZA"],
        requires_bsa=True,
        special_warnings=["Subcutaneous injection — rotate sites", "Myelosuppression — FBC before each cycle", "Hepatic impairment: use caution", "Renal impairment: monitor BUN/creatinine"]
    ),
    "gilteritinib": Drug(
        id="gilteritinib",
        name="Gilteritinib",
        generic_name="Gilteritinib",
        category=DrugCategory.TARGETED,
        aliases=["Xospata"],
        requires_bsa=False,
        special_warnings=["FLT3 inhibitor — confirm FLT3 mutation (ITD or TKD)", "Risk of differentiation syndrome — monitor for fever/dyspnoea/hypoxia", "QTc prolongation — baseline and periodic ECG", "CYP3A4 substrate"]
    ),
    "midostaurin": Drug(
        id="midostaurin",
        name="Midostaurin",
        generic_name="Midostaurin",
        category=DrugCategory.TARGETED,
        aliases=["Rydapt"],
        requires_bsa=False,
        special_warnings=["FLT3 inhibitor — confirm FLT3 mutation", "Strong CYP3A4 inhibitors increase exposure", "Take with food to reduce GI toxicity", "QTc monitoring"]
    ),
    "bortezomib": Drug(
        id="bortezomib",
        name="Bortezomib",
        generic_name="Bortezomib",
        category=DrugCategory.TARGETED,
        aliases=["Velcade"],
        requires_bsa=True,
        special_warnings=["Peripheral neuropathy — use subcutaneous route to reduce neurotoxicity", "VZV reactivation — mandatory aciclovir prophylaxis", "Thrombocytopenia — monitor platelets before each dose"]
    ),
    # --- Enzymes ---
    "peg_asparaginase": Drug(
        id="peg_asparaginase",
        name="Pegaspargase (PEG-Asparaginase)",
        generic_name="Pegaspargase",
        category=DrugCategory.CHEMOTHERAPY,
        aliases=["Oncaspar", "PEG-ASP", "PEG-L-asparaginase"],
        requires_bsa=True,
        special_warnings=["Risk of anaphylaxis — 30-min observation post-infusion", "Risk of pancreatitis — check amylase/lipase if abdominal pain", "Thrombosis risk — check fibrinogen and coagulation", "Hepatotoxicity — monitor LFTs", "Hyperglycaemia — monitor blood glucose"]
    ),
    # --- Ophthalmic prophylaxis ---
    "prednisolone_eyedrops": Drug(
        id="prednisolone_eyedrops",
        name="Prednisolone 0.5% eye drops",
        generic_name="Prednisolone acetate",
        category=DrugCategory.SUPPORTIVE,
        aliases=["dexamethasone eye drops", "steroid eye drops"],
        requires_bsa=False,
        special_warnings=["Mandatory during and 48h after high-dose cytarabine to prevent chemical conjunctivitis"]
    ),
}


# ============= PROTOCOL DEFINITIONS =============

PROTOCOLS = {
    # R-CHOP 21
    "rchop21": Protocol(
        id="rchop21",
        name="R-CHOP 21",
        code="RCHOP21",
        full_name="Rituximab-Cyclophosphamide-Doxorubicin-Vincristine-Prednisolone (21-day cycle)",
        indication="CD20 positive Non-Hodgkin's Lymphoma",
        cycle_length_days=21,
        total_cycles=6,
        version="1.2",
        
        drugs=[
            ProtocolDrug(
                drug_id="rituximab",
                drug_name="Rituximab",
                dose=375,
                dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION,
                days=[1],
                diluent="Sodium chloride 0.9%",
                diluent_volume_ml=500,
                administration_order=1,
                special_instructions="Administer as per rituximab administration guidelines"
            ),
            ProtocolDrug(
                drug_id="doxorubicin",
                drug_name="Doxorubicin",
                dose=50,
                dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_BOLUS,
                days=[1],
                duration_minutes=10,
                administration_order=2
            ),
            ProtocolDrug(
                drug_id="vincristine",
                drug_name="Vincristine",
                dose=1.4,
                dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_BOLUS,
                days=[1],
                duration_minutes=10,
                diluent="Sodium chloride 0.9%",
                diluent_volume_ml=50,
                administration_order=3,
                max_dose=2.0,
                max_dose_unit="mg"
            ),
            ProtocolDrug(
                drug_id="cyclophosphamide",
                drug_name="Cyclophosphamide",
                dose=750,
                dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_BOLUS,
                days=[1],
                duration_minutes=10,
                administration_order=4
            ),
        ],
        
        pre_medications=[
            ProtocolDrug(
                drug_id="chlorphenamine",
                drug_name="Chlorphenamine",
                dose=10,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_BOLUS,
                days=[1],
                administration_order=1,
                is_core_drug=False
            ),
            ProtocolDrug(
                drug_id="paracetamol",
                drug_name="Paracetamol",
                dose=1000,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[1],
                administration_order=2,
                is_core_drug=False
            ),
            ProtocolDrug(
                drug_id="ondansetron",
                drug_name="Ondansetron",
                dose=8,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[1],
                administration_order=3,
                is_core_drug=False,
                special_instructions="Can give IV if oral not tolerated"
            ),
            ProtocolDrug(
                drug_id="prednisolone",
                drug_name="Prednisolone",
                dose=100,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[1],
                administration_order=0,
                is_core_drug=False,
                timing="Morning of treatment day",
                special_instructions="Check patient has taken dose before rituximab"
            ),
        ],
        
        take_home_medicines=[
            ProtocolDrug(
                drug_id="prednisolone",
                drug_name="Prednisolone",
                dose=100,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[2, 3, 4, 5],
                frequency="Once daily",
                is_core_drug=False
            ),
            ProtocolDrug(
                drug_id="ondansetron",
                drug_name="Ondansetron",
                dose=8,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[1, 2, 3],
                frequency="Twice daily",
                is_core_drug=False,
                special_instructions="Start on evening of day 1"
            ),
            ProtocolDrug(
                drug_id="metoclopramide",
                drug_name="Metoclopramide",
                dose=10,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[1, 2, 3, 4, 5, 6, 7],
                frequency="Three times daily when required",
                is_core_drug=False,
                prn=True
            ),
            ProtocolDrug(
                drug_id="allopurinol",
                drug_name="Allopurinol",
                dose=300,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=list(range(1, 22)),
                frequency="Once daily",
                is_core_drug=False,
                special_instructions="For tumour lysis prophylaxis"
            ),
        ],
        
        rescue_medications=[
            ProtocolDrug(
                drug_id="hydrocortisone",
                drug_name="Hydrocortisone",
                dose=100,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_BOLUS,
                days=[1],
                is_core_drug=False,
                prn=True,
                special_instructions="For rituximab infusion reactions"
            ),
            ProtocolDrug(
                drug_id="salbutamol",
                drug_name="Salbutamol",
                dose=2.5,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.NEBULISED,
                days=[1],
                is_core_drug=False,
                prn=True,
                special_instructions="For rituximab-related bronchospasm"
            ),
        ],
        
        dose_modifications=[
            # Neutrophil modifications
            DoseModificationRule(
                parameter="neutrophils",
                condition="< 1",
                affected_drugs=["cyclophosphamide", "doxorubicin"],
                modification="delay",
                description="Delay until neutrophils ≥ 1.0 x10⁹/L"
            ),
            # Platelet modifications
            DoseModificationRule(
                parameter="platelets",
                condition="< 100",
                affected_drugs=["cyclophosphamide", "doxorubicin"],
                modification="delay",
                description="Delay until platelets ≥ 100 x10⁹/L"
            ),
            # Hepatic - Doxorubicin (FIXED: Added missing 50-85 rule, standardized boundaries)
            DoseModificationRule(
                parameter="bilirubin",
                condition="30-50",
                affected_drugs=["doxorubicin"],
                modification="reduce_50",
                modification_percent=50,
                description="Bilirubin 30-50 µmol/L: reduce doxorubicin to 50%"
            ),
            # SAFETY FIX: Previously missing rule for bilirubin 51-85 range
            DoseModificationRule(
                parameter="bilirubin",
                condition="51-85",
                affected_drugs=["doxorubicin"],
                modification="reduce_25",
                modification_percent=25,
                description="Bilirubin 51-85 µmol/L: reduce doxorubicin to 25%"
            ),
            DoseModificationRule(
                parameter="bilirubin",
                condition="> 85",
                affected_drugs=["doxorubicin"],
                modification="omit",
                description="Bilirubin > 85 µmol/L: omit doxorubicin"
            ),
            # Hepatic - Vincristine (FIXED: Standardized boundary to match doxorubicin)
            DoseModificationRule(
                parameter="bilirubin",
                condition="30-50",
                affected_drugs=["vincristine"],
                modification="reduce_50",
                modification_percent=50,
                description="Bilirubin 30-50 µmol/L: reduce vincristine to 50%"
            ),
            DoseModificationRule(
                parameter="bilirubin",
                condition="> 50",
                affected_drugs=["vincristine"],
                modification="omit",
                description="Bilirubin > 50 µmol/L: omit vincristine"
            ),
            # Renal - Cyclophosphamide
            DoseModificationRule(
                parameter="creatinine_clearance",
                condition="< 20",
                affected_drugs=["cyclophosphamide"],
                modification="reduce_75",
                modification_percent=75,
                description="CrCl 10-20 ml/min: reduce cyclophosphamide to 75%"
            ),
        ],
        
        toxicities=[
            Toxicity(drug_id="cyclophosphamide", adverse_effects=[
                "Dysuria", "Haemorrhagic cystitis (rare)", "Taste disturbances"
            ]),
            Toxicity(drug_id="doxorubicin", adverse_effects=[
                "Cardiomyopathy", "Alopecia", "Urinary discolouration (red)"
            ]),
            Toxicity(drug_id="prednisolone", adverse_effects=[
                "Weight gain", "GI disturbances", "Hyperglycaemia",
                "CNS disturbances", "Cushingoid changes", "Glucose intolerance"
            ]),
            Toxicity(drug_id="rituximab", adverse_effects=[
                "Severe cytokine release syndrome",
                "Increased incidence of infective complications",
                "Progressive multifocal leukoencephalopathy"
            ]),
            Toxicity(drug_id="vincristine", adverse_effects=[
                "Peripheral neuropathy", "Constipation", "Jaw pain"
            ]),
        ],
        
        monitoring=[
            "FBC, LFTs and U&Es prior to day one of treatment",
            "Check hepatitis B status before starting rituximab",
            "Baseline LVEF in patients with cardiac history or risk factors",
            "Discontinue doxorubicin if cardiac failure develops"
        ],
        
        warnings=[
            "Check patient has taken prednisolone 100mg on morning of treatment",
            "Consider initial dose reduction in patients over 70 years",
            "Ensure adequate cardiac function before starting doxorubicin"
        ],
        
        source_file="RCHOP21-Cyclophosphamide-Doxorubicin-Prednisolone-Rituximab-Vincristine-21-Ver-1.2.pdf"
    ),
    
    # Bendamustine-Rituximab
    "br": Protocol(
        id="br",
        name="Bendamustine-Rituximab",
        code="BR",
        full_name="Bendamustine-Rituximab",
        indication="Relapsed or refractory Non-Hodgkin Lymphoma; Relapsed or refractory Mantle Cell Lymphoma",
        cycle_length_days=28,
        total_cycles=6,
        version="1.4",
        
        drugs=[
            ProtocolDrug(
                drug_id="rituximab",
                drug_name="Rituximab",
                dose=375,
                dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION,
                days=[1],
                diluent="Sodium chloride 0.9%",
                diluent_volume_ml=500,
                administration_order=1
            ),
            ProtocolDrug(
                drug_id="bendamustine",
                drug_name="Bendamustine",
                dose=90,
                dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION,
                days=[1, 2],
                duration_minutes=30,
                diluent="Sodium chloride 0.9%",
                diluent_volume_ml=500,
                administration_order=2
            ),
        ],
        
        pre_medications=[
            ProtocolDrug(
                drug_id="chlorphenamine",
                drug_name="Chlorphenamine",
                dose=10,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_BOLUS,
                days=[1],
                is_core_drug=False
            ),
            ProtocolDrug(
                drug_id="hydrocortisone",
                drug_name="Hydrocortisone",
                dose=100,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_BOLUS,
                days=[1],
                is_core_drug=False
            ),
            ProtocolDrug(
                drug_id="paracetamol",
                drug_name="Paracetamol",
                dose=1000,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[1],
                is_core_drug=False
            ),
            ProtocolDrug(
                drug_id="ondansetron",
                drug_name="Ondansetron",
                dose=8,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[1, 2],
                is_core_drug=False
            ),
        ],
        
        take_home_medicines=[
            ProtocolDrug(
                drug_id="ondansetron",
                drug_name="Ondansetron",
                dose=8,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[1, 2, 3],
                frequency="Twice daily",
                is_core_drug=False
            ),
            ProtocolDrug(
                drug_id="metoclopramide",
                drug_name="Metoclopramide",
                dose=10,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=list(range(1, 8)),
                frequency="Three times daily when required",
                prn=True,
                is_core_drug=False
            ),
            ProtocolDrug(
                drug_id="cotrimoxazole",
                drug_name="Co-trimoxazole",
                dose=960,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[1, 3, 5],  # Mon, Wed, Fri
                frequency="Once daily on Mon, Wed, Fri",
                is_core_drug=False,
                special_instructions="PCP prophylaxis"
            ),
        ],
        
        rescue_medications=[
            ProtocolDrug(
                drug_id="hydrocortisone",
                drug_name="Hydrocortisone",
                dose=100,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_BOLUS,
                days=[1],
                is_core_drug=False,
                prn=True,
                special_instructions="For rituximab infusion reactions"
            ),
            ProtocolDrug(
                drug_id="salbutamol",
                drug_name="Salbutamol",
                dose=2.5,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.NEBULISED,
                days=[1],
                is_core_drug=False,
                prn=True,
                special_instructions="For rituximab-related bronchospasm"
            ),
        ],
        
        dose_modifications=[
            DoseModificationRule(
                parameter="neutrophils",
                condition="< 0.5",
                affected_drugs=["bendamustine"],
                modification="reduce_75",
                modification_percent=75,
                description="Neutrophils < 0.5: 1st occurrence - reduce to 75%"
            ),
            DoseModificationRule(
                parameter="platelets",
                condition="< 25",
                affected_drugs=["bendamustine"],
                modification="reduce_75",
                modification_percent=75,
                description="Platelets < 25: 1st occurrence - reduce to 75%"
            ),
            DoseModificationRule(
                parameter="bilirubin",
                condition="21-51",
                affected_drugs=["bendamustine"],
                modification="reduce_70",
                modification_percent=70,
                description="Bilirubin 21-51 µmol/L: reduce to 70%"
            ),
        ],
        
        toxicities=[
            Toxicity(drug_id="bendamustine", adverse_effects=[
                "Transfusion related GVHD", "GI disturbances", "Fatigue",
                "Insomnia", "Cardiac dysfunction", "Hypotension/hypertension",
                "Hypersensitivity reactions", "Hypokalaemia"
            ]),
            Toxicity(drug_id="rituximab", adverse_effects=[
                "Severe cytokine release syndrome",
                "Increased incidence of infective complications",
                "Progressive multifocal leukoencephalopathy"
            ]),
        ],
        
        monitoring=[
            "FBC, LFTs and U&Es prior to day one of treatment",
            "Check hepatitis B status prior to starting treatment with rituximab",
            "Ensure close monitoring of potassium levels in patients with pre-existing cardiac disorders"
        ],
        
        warnings=[
            "CRITICAL: Patients require IRRADIATED BLOOD PRODUCTS for life after bendamustine",
            "Ensure transfusion department notified and patient issued alert card",
            "Avoid allopurinol unless high TLS risk due to Stevens-Johnson syndrome risk"
        ],
        
        source_file="Bendamustine-Rituximab.pdf"
    ),
    
    # CHOP 21 (without Rituximab)
    "chop21": Protocol(
        id="chop21",
        name="CHOP 21",
        code="CHOP21",
        full_name="Cyclophosphamide-Doxorubicin-Vincristine-Prednisolone (21-day cycle)",
        indication="Non-Hodgkin's Lymphoma",
        cycle_length_days=21,
        total_cycles=6,
        version="1.2",
        
        drugs=[
            ProtocolDrug(
                drug_id="doxorubicin",
                drug_name="Doxorubicin",
                dose=50,
                dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_BOLUS,
                days=[1],
                duration_minutes=10,
                administration_order=1
            ),
            ProtocolDrug(
                drug_id="vincristine",
                drug_name="Vincristine",
                dose=1.4,
                dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_BOLUS,
                days=[1],
                duration_minutes=10,
                diluent="Sodium chloride 0.9%",
                diluent_volume_ml=50,
                administration_order=2,
                max_dose=2.0,
                max_dose_unit="mg"
            ),
            ProtocolDrug(
                drug_id="cyclophosphamide",
                drug_name="Cyclophosphamide",
                dose=750,
                dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_BOLUS,
                days=[1],
                duration_minutes=10,
                administration_order=3
            ),
        ],
        
        pre_medications=[
            ProtocolDrug(
                drug_id="ondansetron",
                drug_name="Ondansetron",
                dose=8,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[1],
                is_core_drug=False
            ),
            ProtocolDrug(
                drug_id="prednisolone",
                drug_name="Prednisolone",
                dose=100,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[1],
                is_core_drug=False
            ),
        ],
        
        take_home_medicines=[
            ProtocolDrug(
                drug_id="prednisolone",
                drug_name="Prednisolone",
                dose=100,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[2, 3, 4, 5],
                frequency="Once daily",
                is_core_drug=False
            ),
            ProtocolDrug(
                drug_id="ondansetron",
                drug_name="Ondansetron",
                dose=8,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[1, 2, 3],
                frequency="Twice daily",
                is_core_drug=False
            ),
            ProtocolDrug(
                drug_id="metoclopramide",
                drug_name="Metoclopramide",
                dose=10,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=list(range(1, 8)),
                frequency="Three times daily when required",
                prn=True,
                is_core_drug=False
            ),
        ],
        
        dose_modifications=[
            DoseModificationRule(
                parameter="neutrophils",
                condition="< 1",
                affected_drugs=["cyclophosphamide", "doxorubicin"],
                modification="delay",
                description="Delay until neutrophils ≥ 1.0 x10⁹/L"
            ),
            DoseModificationRule(
                parameter="bilirubin",
                condition="> 85",
                affected_drugs=["doxorubicin"],
                modification="omit",
                description="Bilirubin > 85 µmol/L: omit doxorubicin"
            ),
        ],
        
        monitoring=[
            "FBC, LFTs and U&Es prior to day one of treatment",
            "Baseline LVEF in patients with cardiac history"
        ],
        
        source_file="CHOP21-Cyclophosphamide-Doxorubicin-Prednisolone-Vincristine-21-Ver-1.2.pdf"
    ),
    
    # ABVD (Hodgkin Lymphoma)
    "abvd": Protocol(
        id="abvd",
        name="ABVD",
        code="ABVD",
        full_name="Doxorubicin (Adriamycin)-Bleomycin-Vinblastine-Dacarbazine",
        indication="Hodgkin Lymphoma",
        cycle_length_days=28,
        total_cycles=6,
        version="1.2",
        
        drugs=[
            ProtocolDrug(
                drug_id="doxorubicin",
                drug_name="Doxorubicin",
                dose=25,
                dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_BOLUS,
                days=[1, 15],
                duration_minutes=10,
                administration_order=1
            ),
            ProtocolDrug(
                drug_id="bleomycin",
                drug_name="Bleomycin",
                dose=10000,
                dose_unit=DoseUnit.UNITS_M2,
                route=RouteOfAdministration.IV_BOLUS,
                days=[1, 15],
                administration_order=2
            ),
            ProtocolDrug(
                drug_id="vinblastine",
                drug_name="Vinblastine",
                dose=6,
                dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_BOLUS,
                days=[1, 15],
                administration_order=3
            ),
            ProtocolDrug(
                drug_id="dacarbazine",
                drug_name="Dacarbazine",
                dose=375,
                dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION,
                days=[1, 15],
                duration_minutes=30,
                diluent="Sodium chloride 0.9%",
                diluent_volume_ml=250,
                administration_order=4
            ),
        ],
        
        pre_medications=[
            ProtocolDrug(
                drug_id="ondansetron",
                drug_name="Ondansetron",
                dose=8,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_BOLUS,
                days=[1, 15],
                is_core_drug=False
            ),
            ProtocolDrug(
                drug_id="dexamethasone",
                drug_name="Dexamethasone",
                dose=8,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_BOLUS,
                days=[1, 15],
                is_core_drug=False
            ),
        ],
        
        take_home_medicines=[
            ProtocolDrug(
                drug_id="ondansetron",
                drug_name="Ondansetron",
                dose=8,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[1, 2, 3],
                frequency="Twice daily",
                is_core_drug=False
            ),
            ProtocolDrug(
                drug_id="metoclopramide",
                drug_name="Metoclopramide",
                dose=10,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=list(range(1, 8)),
                frequency="Three times daily when required",
                prn=True,
                is_core_drug=False
            ),
        ],
        
        toxicities=[
            Toxicity(drug_id="doxorubicin", adverse_effects=["Cardiomyopathy", "Alopecia"]),
            Toxicity(drug_id="bleomycin", adverse_effects=["Pulmonary fibrosis", "Skin reactions"]),
            Toxicity(drug_id="vinblastine", adverse_effects=["Myelosuppression", "Neuropathy"]),
            Toxicity(drug_id="dacarbazine", adverse_effects=["Nausea/vomiting", "Flu-like syndrome"]),
        ],
        
        monitoring=[
            "FBC, LFTs and U&Es prior to treatment",
            "Pulmonary function tests before starting and periodically during treatment",
            "LVEF monitoring for cardiac function"
        ],
        
        warnings=[
            "Monitor for pulmonary toxicity from bleomycin",
            "Cumulative bleomycin dose limit applies"
        ],
        
        source_file="ABVD-Bleomycin-Dacarbazine-Doxorubicin-Vinblastine-Ver-1.2.pdf"
    ),
    
    # GDP (Cisplatin-Dexamethasone-Gemcitabine)
    "gdp": Protocol(
        id="gdp",
        name="GDP",
        code="GDP",
        full_name="Gemcitabine-Dexamethasone-Cisplatin",
        indication="Relapsed/refractory Diffuse Large B-Cell Lymphoma",
        cycle_length_days=21,
        total_cycles=4,
        version="1.0",
        
        drugs=[
            ProtocolDrug(
                drug_id="gemcitabine",
                drug_name="Gemcitabine",
                dose=1000,
                dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION,
                days=[1, 8],
                duration_minutes=30,
                diluent="Sodium chloride 0.9%",
                diluent_volume_ml=250,
                administration_order=1
            ),
            ProtocolDrug(
                drug_id="cisplatin",
                drug_name="Cisplatin",
                dose=75,
                dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION,
                days=[1],
                duration_minutes=60,
                diluent="Sodium chloride 0.9%",
                diluent_volume_ml=500,
                administration_order=2,
                special_instructions="Ensure adequate hydration pre and post"
            ),
            ProtocolDrug(
                drug_id="dexamethasone",
                drug_name="Dexamethasone",
                dose=40,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[1, 2, 3, 4],
                frequency="Once daily",
                administration_order=3
            ),
        ],
        
        pre_medications=[
            ProtocolDrug(
                drug_id="ondansetron",
                drug_name="Ondansetron",
                dose=8,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_BOLUS,
                days=[1, 8],
                is_core_drug=False
            ),
        ],
        
        monitoring=[
            "FBC, LFTs and U&Es prior to each cycle",
            "Renal function - check creatinine before each cycle",
            "Audiometry if symptomatic"
        ],
        
        warnings=[
            "Ensure adequate hydration for cisplatin",
            "Monitor for nephrotoxicity and ototoxicity"
        ],
        
        source_file="GDP-Cisplatin-Dexamethasone-Gemcitabine.pdf"
    ),
    
    # Bendamustine alone
    "bendamustine": Protocol(
        id="bendamustine",
        name="Bendamustine",
        code="BENDA",
        full_name="Bendamustine monotherapy",
        indication="Indolent Non-Hodgkin Lymphoma progressed during or within 6 months of rituximab",
        cycle_length_days=28,
        total_cycles=6,
        version="1.4",
        
        drugs=[
            ProtocolDrug(
                drug_id="bendamustine",
                drug_name="Bendamustine",
                dose=120,
                dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION,
                days=[1, 2],
                duration_minutes=30,
                diluent="Sodium chloride 0.9%",
                diluent_volume_ml=500,
                administration_order=1
            ),
        ],
        
        pre_medications=[
            ProtocolDrug(
                drug_id="ondansetron",
                drug_name="Ondansetron",
                dose=8,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[1, 2],
                is_core_drug=False
            ),
        ],
        
        take_home_medicines=[
            ProtocolDrug(
                drug_id="ondansetron",
                drug_name="Ondansetron",
                dose=8,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[1, 2, 3],
                frequency="Twice daily",
                is_core_drug=False
            ),
            ProtocolDrug(
                drug_id="cotrimoxazole",
                drug_name="Co-trimoxazole",
                dose=960,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[1, 3, 5],
                frequency="Once daily Mon/Wed/Fri",
                is_core_drug=False
            ),
        ],
        
        dose_modifications=[
            DoseModificationRule(
                parameter="neutrophils",
                condition="< 0.5",
                affected_drugs=["bendamustine"],
                modification="reduce_75",
                modification_percent=75,
                description="Neutrophils < 0.5: reduce to 75%"
            ),
            DoseModificationRule(
                parameter="bilirubin",
                condition="21-51",
                affected_drugs=["bendamustine"],
                modification="reduce_70",
                modification_percent=70,
                description="Bilirubin 21-51 µmol/L: reduce to 70%"
            ),
        ],
        
        warnings=[
            "CRITICAL: Patients require IRRADIATED BLOOD PRODUCTS for life",
            "Notify transfusion department and issue patient alert card",
            "Avoid allopurinol unless high TLS risk"
        ],
        
        source_file="Bendamustine.pdf"
    ),
    
    # R-CVP
    "rcvp": Protocol(
        id="rcvp",
        name="R-CVP",
        code="RCVP",
        full_name="Rituximab-Cyclophosphamide-Vincristine-Prednisolone",
        indication="Follicular Lymphoma; Low-grade Non-Hodgkin's Lymphoma",
        cycle_length_days=21,
        total_cycles=8,
        version="1.2",
        
        drugs=[
            ProtocolDrug(
                drug_id="rituximab",
                drug_name="Rituximab",
                dose=375,
                dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION,
                days=[1],
                diluent="Sodium chloride 0.9%",
                diluent_volume_ml=500,
                administration_order=1
            ),
            ProtocolDrug(
                drug_id="cyclophosphamide",
                drug_name="Cyclophosphamide",
                dose=750,
                dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_BOLUS,
                days=[1],
                duration_minutes=10,
                administration_order=2
            ),
            ProtocolDrug(
                drug_id="vincristine",
                drug_name="Vincristine",
                dose=1.4,
                dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_BOLUS,
                days=[1],
                duration_minutes=10,
                max_dose=2.0,
                max_dose_unit="mg",
                administration_order=3
            ),
        ],
        
        pre_medications=[
            ProtocolDrug(
                drug_id="chlorphenamine",
                drug_name="Chlorphenamine",
                dose=10,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_BOLUS,
                days=[1],
                is_core_drug=False
            ),
            ProtocolDrug(
                drug_id="paracetamol",
                drug_name="Paracetamol",
                dose=1000,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[1],
                is_core_drug=False
            ),
            ProtocolDrug(
                drug_id="ondansetron",
                drug_name="Ondansetron",
                dose=8,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[1],
                is_core_drug=False
            ),
            ProtocolDrug(
                drug_id="prednisolone",
                drug_name="Prednisolone",
                dose=100,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[1],
                is_core_drug=False
            ),
        ],
        
        take_home_medicines=[
            ProtocolDrug(
                drug_id="prednisolone",
                drug_name="Prednisolone",
                dose=100,
                dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL,
                days=[2, 3, 4, 5],
                frequency="Once daily",
                is_core_drug=False
            ),
        ],
        
        monitoring=[
            "FBC, LFTs and U&Es prior to day one",
            "Check hepatitis B status before rituximab"
        ],
        
        source_file="RCVP-Cyclophosphamide-Prednisolone-Rituximab-Vincristine-Ver-1.2.pdf"
    ),

    # =========================================================
    # LYMPHOMA — ADDITIONAL PROTOCOLS
    # =========================================================

    # R-CHOP 14 (dose-dense)
    "rchop14": Protocol(
        id="rchop14",
        name="R-CHOP 14",
        code="RCHOP14",
        full_name="Rituximab-Cyclophosphamide-Doxorubicin-Vincristine-Prednisolone (14-day cycle, dose-dense)",
        indication="CD20+ Diffuse Large B-Cell Lymphoma — dose-dense arm",
        cycle_length_days=14,
        total_cycles=6,
        version="1.0",
        treatment_intent="curative",
        drugs=[
            ProtocolDrug(drug_id="rituximab", drug_name="Rituximab", dose=375, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[1], diluent="Sodium chloride 0.9%",
                diluent_volume_ml=500, administration_order=1),
            ProtocolDrug(drug_id="cyclophosphamide", drug_name="Cyclophosphamide", dose=750, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[1], duration_minutes=60,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=500, administration_order=2),
            ProtocolDrug(drug_id="doxorubicin", drug_name="Doxorubicin", dose=50, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_BOLUS, days=[1], duration_minutes=10, administration_order=3),
            ProtocolDrug(drug_id="vincristine", drug_name="Vincristine", dose=1.4, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_BOLUS, days=[1], max_dose=2.0, max_dose_unit="mg",
                administration_order=4),
        ],
        pre_medications=[
            ProtocolDrug(drug_id="chlorphenamine", drug_name="Chlorphenamine", dose=10, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_BOLUS, days=[1], is_core_drug=False),
            ProtocolDrug(drug_id="paracetamol", drug_name="Paracetamol", dose=1000, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1], is_core_drug=False),
            ProtocolDrug(drug_id="ondansetron", drug_name="Ondansetron", dose=8, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_INFUSION, days=[1], is_core_drug=False),
            ProtocolDrug(drug_id="prednisolone", drug_name="Prednisolone", dose=100, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1], is_core_drug=False, timing="Morning of day 1"),
        ],
        take_home_medicines=[
            ProtocolDrug(drug_id="prednisolone", drug_name="Prednisolone", dose=100, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[2, 3, 4, 5], frequency="Once daily", is_core_drug=False),
            ProtocolDrug(drug_id="ondansetron", drug_name="Ondansetron", dose=8, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1, 2, 3], frequency="Twice daily", is_core_drug=False),
            ProtocolDrug(drug_id="metoclopramide", drug_name="Metoclopramide", dose=10, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 8)), frequency="Three times daily PRN",
                prn=True, is_core_drug=False),
        ],
        dose_modifications=[
            DoseModificationRule(rule_id="bili_30_50_dox", parameter="bilirubin", condition_type="range",
                threshold_low=30, threshold_high=50, affected_drugs=["doxorubicin", "vincristine"],
                modification_type="reduce", modification_percent=50,
                description="Bilirubin 30–50 µmol/L: reduce doxorubicin and vincristine to 50%"),
            DoseModificationRule(rule_id="bili_gt85_dox", parameter="bilirubin", condition_type="greater_than",
                threshold_value=85, affected_drugs=["doxorubicin"],
                modification_type="omit", modification_percent=0,
                description="Bilirubin >85 µmol/L: omit doxorubicin"),
            DoseModificationRule(rule_id="bili_gt50_vcr", parameter="bilirubin", condition_type="greater_than",
                threshold_value=50, affected_drugs=["vincristine"],
                modification_type="omit", modification_percent=0,
                description="Bilirubin >50 µmol/L: omit vincristine"),
            DoseModificationRule(rule_id="crcl_lt20_cyc", parameter="creatinine_clearance",
                condition_type="less_than", threshold_value=20, affected_drugs=["cyclophosphamide"],
                modification_type="reduce", modification_percent=75,
                description="CrCl <20 ml/min: reduce cyclophosphamide to 75%"),
        ],
        monitoring=["FBC, U&E, LFTs before each cycle", "G-CSF mandatory to maintain 14-day schedule",
                    "Check hepatitis B status before rituximab", "Baseline LVEF if cardiac history"],
        warnings=["G-CSF (filgrastim/pegfilgrastim) REQUIRED to maintain 14-day interval",
                  "Vincristine 2mg absolute cap — FATAL if exceeded"],
    ),

    # CHOP-14 (without rituximab — CD20 negative or t-cell)
    "chop14": Protocol(
        id="chop14",
        name="CHOP-14",
        code="CHOP14",
        full_name="Cyclophosphamide-Doxorubicin-Vincristine-Prednisolone (14-day cycle)",
        indication="T-cell lymphoma; CD20-negative aggressive NHL",
        cycle_length_days=14,
        total_cycles=6,
        version="1.0",
        treatment_intent="curative",
        drugs=[
            ProtocolDrug(drug_id="cyclophosphamide", drug_name="Cyclophosphamide", dose=750, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[1], duration_minutes=60,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=500, administration_order=1),
            ProtocolDrug(drug_id="doxorubicin", drug_name="Doxorubicin", dose=50, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_BOLUS, days=[1], duration_minutes=10, administration_order=2),
            ProtocolDrug(drug_id="vincristine", drug_name="Vincristine", dose=1.4, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_BOLUS, days=[1], max_dose=2.0, max_dose_unit="mg",
                administration_order=3),
        ],
        pre_medications=[
            ProtocolDrug(drug_id="ondansetron", drug_name="Ondansetron", dose=8, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_INFUSION, days=[1], is_core_drug=False),
            ProtocolDrug(drug_id="prednisolone", drug_name="Prednisolone", dose=100, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1], is_core_drug=False),
        ],
        take_home_medicines=[
            ProtocolDrug(drug_id="prednisolone", drug_name="Prednisolone", dose=100, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[2, 3, 4, 5], frequency="Once daily", is_core_drug=False),
            ProtocolDrug(drug_id="ondansetron", drug_name="Ondansetron", dose=8, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1, 2, 3], frequency="Twice daily", is_core_drug=False),
        ],
        dose_modifications=[
            DoseModificationRule(rule_id="bili_30_50_dox", parameter="bilirubin", condition_type="range",
                threshold_low=30, threshold_high=50, affected_drugs=["doxorubicin", "vincristine"],
                modification_type="reduce", modification_percent=50, description="Bilirubin 30–50: reduce to 50%"),
            DoseModificationRule(rule_id="bili_gt85_dox", parameter="bilirubin", condition_type="greater_than",
                threshold_value=85, affected_drugs=["doxorubicin"], modification_type="omit",
                description="Bilirubin >85: omit doxorubicin"),
            DoseModificationRule(rule_id="bili_gt50_vcr", parameter="bilirubin", condition_type="greater_than",
                threshold_value=50, affected_drugs=["vincristine"], modification_type="omit",
                description="Bilirubin >50: omit vincristine"),
        ],
        monitoring=["FBC, U&E, LFTs before each cycle", "G-CSF required for 14-day schedule"],
        warnings=["G-CSF mandatory", "Vincristine 2mg cap — FATAL if exceeded"],
    ),

    # R-GDP (relapsed/refractory salvage)
    "rgdp": Protocol(
        id="rgdp",
        name="R-GDP",
        code="RGDP",
        full_name="Rituximab-Gemcitabine-Dexamethasone-Cisplatin",
        indication="Relapsed/refractory CD20+ diffuse large B-cell lymphoma — salvage prior to ASCT",
        cycle_length_days=21,
        total_cycles=2,
        version="1.0",
        treatment_intent="palliative",
        drugs=[
            ProtocolDrug(drug_id="rituximab", drug_name="Rituximab", dose=375, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[1], diluent="Sodium chloride 0.9%",
                diluent_volume_ml=500, administration_order=1),
            ProtocolDrug(drug_id="gemcitabine", drug_name="Gemcitabine", dose=1000, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[1, 8], duration_minutes=30,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=250, administration_order=2),
            ProtocolDrug(drug_id="cisplatin", drug_name="Cisplatin", dose=75, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[1], duration_minutes=60,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=1000, administration_order=3,
                special_instructions="Ensure pre- and post-hydration. Monitor urine output."),
            ProtocolDrug(drug_id="dexamethasone", drug_name="Dexamethasone", dose=40, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1, 2, 3, 4], frequency="Once daily", administration_order=4),
        ],
        pre_medications=[
            ProtocolDrug(drug_id="chlorphenamine", drug_name="Chlorphenamine", dose=10, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_BOLUS, days=[1], is_core_drug=False),
            ProtocolDrug(drug_id="paracetamol", drug_name="Paracetamol", dose=1000, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1], is_core_drug=False),
            ProtocolDrug(drug_id="ondansetron", drug_name="Ondansetron", dose=8, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_INFUSION, days=[1, 8], is_core_drug=False),
        ],
        take_home_medicines=[
            ProtocolDrug(drug_id="ondansetron", drug_name="Ondansetron", dose=8, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 6)), frequency="Twice daily", is_core_drug=False),
            ProtocolDrug(drug_id="metoclopramide", drug_name="Metoclopramide", dose=10, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 8)), frequency="Three times daily PRN",
                prn=True, is_core_drug=False),
        ],
        dose_modifications=[
            DoseModificationRule(rule_id="crcl_lt60_cis", parameter="creatinine_clearance",
                condition_type="less_than", threshold_value=60, affected_drugs=["cisplatin"],
                modification_type="omit", modification_percent=0,
                description="CrCl <60 ml/min: omit cisplatin — consider substituting carboplatin AUC5"),
            DoseModificationRule(rule_id="crcl_lt30_gem", parameter="creatinine_clearance",
                condition_type="less_than", threshold_value=30, affected_drugs=["gemcitabine"],
                modification_type="reduce", modification_percent=75,
                description="CrCl <30 ml/min: reduce gemcitabine to 75%"),
        ],
        monitoring=["FBC, U&E, LFTs before each cycle", "Urine output monitoring during cisplatin infusion",
                    "Magnesium, potassium post-cisplatin — replace as needed"],
        warnings=["Cisplatin contraindicated if CrCl <60 ml/min — use carboplatin-GDP instead",
                  "Aggressive IV hydration mandatory before/after cisplatin"],
    ),

    # DHAP (salvage lymphoma)
    "dhap": Protocol(
        id="dhap",
        name="DHAP",
        code="DHAP",
        full_name="Dexamethasone-Cytarabine-Cisplatin (high-dose cytarabine salvage)",
        indication="Relapsed/refractory aggressive lymphoma — salvage pre-ASCT",
        cycle_length_days=21,
        total_cycles=2,
        version="1.0",
        treatment_intent="palliative",
        drugs=[
            ProtocolDrug(drug_id="cisplatin", drug_name="Cisplatin", dose=100, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[1], duration_minutes=1440,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=1000, administration_order=1,
                special_instructions="Continuous 24-hour infusion. Aggressive hydration required."),
            ProtocolDrug(drug_id="cytarabine", drug_name="Cytarabine", dose=2000, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[2], duration_minutes=180,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=500, administration_order=2,
                frequency="Every 12 hours x2 doses",
                special_instructions="Use prophylactic steroid eye drops for 24h post-dose to prevent conjunctivitis."),
            ProtocolDrug(drug_id="dexamethasone", drug_name="Dexamethasone", dose=40, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_INFUSION, days=[1, 2, 3, 4], frequency="Once daily",
                administration_order=3),
        ],
        pre_medications=[
            ProtocolDrug(drug_id="ondansetron", drug_name="Ondansetron", dose=8, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_INFUSION, days=[1, 2], is_core_drug=False),
        ],
        take_home_medicines=[
            ProtocolDrug(drug_id="ondansetron", drug_name="Ondansetron", dose=8, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 6)), frequency="Twice daily", is_core_drug=False),
            ProtocolDrug(drug_id="cotrimoxazole", drug_name="Co-trimoxazole", dose=960, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1, 3, 5], frequency="Mon/Wed/Fri", is_core_drug=False,
                special_instructions="PCP prophylaxis — continue until immune recovery"),
        ],
        dose_modifications=[
            DoseModificationRule(rule_id="crcl_lt60_cis_dhap", parameter="creatinine_clearance",
                condition_type="less_than", threshold_value=60, affected_drugs=["cisplatin"],
                modification_type="omit", modification_percent=0,
                description="CrCl <60: omit cisplatin — consider oxaliplatin-based alternative"),
            DoseModificationRule(rule_id="age_cytarabine", parameter="bilirubin", condition_type="greater_than",
                threshold_value=30, affected_drugs=["cytarabine"], modification_type="reduce",
                modification_percent=50, description="Hepatic impairment: reduce cytarabine to 50%"),
        ],
        monitoring=["FBC, U&E, LFTs, Mg, K before each cycle", "Steroid eye drops days 2–5 (cytarabine conjunctivitis)",
                    "Neurotoxicity assessment before each cycle (HD-AraC)"],
        warnings=["High-dose cytarabine — steroid eye drops MANDATORY", "24h cisplatin infusion requires inpatient care",
                  "G-CSF support typically required from day 5"],
    ),

    # ICE (salvage ifosfamide-based)
    "ice": Protocol(
        id="ice",
        name="ICE",
        code="ICE",
        full_name="Ifosfamide-Carboplatin-Etoposide",
        indication="Relapsed/refractory aggressive lymphoma — salvage pre-ASCT",
        cycle_length_days=14,
        total_cycles=2,
        version="1.0",
        treatment_intent="palliative",
        drugs=[
            ProtocolDrug(drug_id="etoposide", drug_name="Etoposide", dose=100, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[1, 2, 3], duration_minutes=60,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=500, administration_order=1),
            ProtocolDrug(drug_id="carboplatin", drug_name="Carboplatin", dose=5, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[2], duration_minutes=60,
                diluent="Glucose 5%", diluent_volume_ml=500, administration_order=2,
                special_instructions="AUC5 (Calvert formula). Max dose 800mg."),
            ProtocolDrug(drug_id="ifosfamide", drug_name="Ifosfamide", dose=5000, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[2], duration_minutes=1440,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=3000, administration_order=3,
                special_instructions="Continuous 24h infusion. Requires mesna uroprotection."),
        ],
        pre_medications=[
            ProtocolDrug(drug_id="ondansetron", drug_name="Ondansetron", dose=8, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_INFUSION, days=[1, 2, 3], is_core_drug=False),
            ProtocolDrug(drug_id="mesna", drug_name="Mesna", dose=1000, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[2], duration_minutes=1440, is_core_drug=False,
                special_instructions="Concurrent with ifosfamide + 4h post. Uroprotection."),
        ],
        take_home_medicines=[
            ProtocolDrug(drug_id="cotrimoxazole", drug_name="Co-trimoxazole", dose=960, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1, 3, 5], frequency="Mon/Wed/Fri", is_core_drug=False,
                special_instructions="PCP prophylaxis"),
        ],
        dose_modifications=[
            DoseModificationRule(rule_id="crcl_lt50_ifos", parameter="creatinine_clearance",
                condition_type="less_than", threshold_value=50, affected_drugs=["ifosfamide"],
                modification_type="omit", modification_percent=0,
                description="CrCl <50: omit ifosfamide — nephrotoxicity risk"),
            DoseModificationRule(rule_id="crcl_carboplatin", parameter="creatinine_clearance",
                condition_type="less_than", threshold_value=30, affected_drugs=["carboplatin"],
                modification_type="reduce", modification_percent=75,
                description="CrCl <30: reduce carboplatin (recalculate AUC)"),
        ],
        monitoring=["Daily U&E during treatment (ifosfamide nephrotoxicity)", "Urine microscopy for haematuria",
                    "FBC before each cycle", "Neurological assessment (ifosfamide encephalopathy risk)"],
        warnings=["Mesna uroprotection MANDATORY with ifosfamide", "Ifosfamide encephalopathy — monitor for confusion",
                  "Inpatient admission required for ifosfamide 24h infusion"],
    ),

    # Pola-R-CHP (polatuzumab-based DLBCL)
    "polarchp": Protocol(
        id="polarchp",
        name="Pola-R-CHP",
        code="POLARCHP",
        full_name="Polatuzumab vedotin-Rituximab-Cyclophosphamide-Doxorubicin-Prednisolone",
        indication="Untreated CD20+ Diffuse Large B-Cell Lymphoma (IPI ≥2) — POLARIX regimen",
        cycle_length_days=21,
        total_cycles=6,
        version="1.0",
        treatment_intent="curative",
        drugs=[
            ProtocolDrug(drug_id="polatuzumab", drug_name="Polatuzumab vedotin", dose=1.8, dose_unit=DoseUnit.MG_KG,
                route=RouteOfAdministration.IV_INFUSION, days=[1], duration_minutes=90,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=100, administration_order=1,
                special_instructions="First infusion 90 min. Subsequent infusions 30 min if tolerated."),
            ProtocolDrug(drug_id="rituximab", drug_name="Rituximab", dose=375, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[1], diluent="Sodium chloride 0.9%",
                diluent_volume_ml=500, administration_order=2),
            ProtocolDrug(drug_id="cyclophosphamide", drug_name="Cyclophosphamide", dose=750, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[1], duration_minutes=60,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=500, administration_order=3),
            ProtocolDrug(drug_id="doxorubicin", drug_name="Doxorubicin", dose=50, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_BOLUS, days=[1], duration_minutes=10, administration_order=4),
        ],
        pre_medications=[
            ProtocolDrug(drug_id="chlorphenamine", drug_name="Chlorphenamine", dose=10, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_BOLUS, days=[1], is_core_drug=False),
            ProtocolDrug(drug_id="paracetamol", drug_name="Paracetamol", dose=1000, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1], is_core_drug=False),
            ProtocolDrug(drug_id="ondansetron", drug_name="Ondansetron", dose=8, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_INFUSION, days=[1], is_core_drug=False),
            ProtocolDrug(drug_id="prednisolone", drug_name="Prednisolone", dose=100, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1], is_core_drug=False),
        ],
        take_home_medicines=[
            ProtocolDrug(drug_id="prednisolone", drug_name="Prednisolone", dose=100, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[2, 3, 4, 5], frequency="Once daily", is_core_drug=False),
            ProtocolDrug(drug_id="ondansetron", drug_name="Ondansetron", dose=8, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1, 2, 3], frequency="Twice daily", is_core_drug=False),
            ProtocolDrug(drug_id="cotrimoxazole", drug_name="Co-trimoxazole", dose=960, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1, 3, 5], frequency="Mon/Wed/Fri", is_core_drug=False,
                special_instructions="PCP prophylaxis during polatuzumab therapy"),
        ],
        dose_modifications=[
            DoseModificationRule(rule_id="bili_30_50_dox", parameter="bilirubin", condition_type="range",
                threshold_low=30, threshold_high=85, affected_drugs=["doxorubicin"],
                modification_type="reduce", modification_percent=50, description="Bilirubin 30–85: reduce doxorubicin 50%"),
            DoseModificationRule(rule_id="bili_gt85_dox", parameter="bilirubin", condition_type="greater_than",
                threshold_value=85, affected_drugs=["doxorubicin"], modification_type="omit",
                description="Bilirubin >85: omit doxorubicin"),
        ],
        monitoring=["FBC, U&E, LFTs before each cycle", "Monitor for peripheral neuropathy (polatuzumab)",
                    "Baseline LVEF", "Hepatitis B screening before rituximab"],
        warnings=["Peripheral neuropathy — assess before each cycle; withhold if Grade ≥3",
                  "PCP prophylaxis MANDATORY during treatment"],
    ),

    # Brentuximab-AVD (Hodgkin lymphoma, advanced stage)
    "bravd": Protocol(
        id="bravd",
        name="BrAVD",
        code="BRAVD",
        full_name="Brentuximab vedotin-Doxorubicin-Vinblastine-Dacarbazine (ECHELON-1)",
        indication="Advanced classical Hodgkin Lymphoma (Stage III/IV) — frontline",
        cycle_length_days=14,
        total_cycles=6,
        version="1.0",
        treatment_intent="curative",
        drugs=[
            ProtocolDrug(drug_id="brentuximab", drug_name="Brentuximab vedotin", dose=1.2, dose_unit=DoseUnit.MG_KG,
                route=RouteOfAdministration.IV_INFUSION, days=[1], duration_minutes=30,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=150, administration_order=1,
                special_instructions="Max dose 120 mg. Do NOT substitute vincristine — different toxicity profile."),
            ProtocolDrug(drug_id="doxorubicin", drug_name="Doxorubicin", dose=25, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_BOLUS, days=[1], duration_minutes=10, administration_order=2),
            ProtocolDrug(drug_id="vinblastine", drug_name="Vinblastine", dose=6, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_BOLUS, days=[1], administration_order=3,
                special_instructions="Vesicant — ensure patent IV. Max single dose 10mg."),
            ProtocolDrug(drug_id="dacarbazine", drug_name="Dacarbazine", dose=375, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[1], duration_minutes=60,
                diluent="Glucose 5%", diluent_volume_ml=250, administration_order=4),
        ],
        pre_medications=[
            ProtocolDrug(drug_id="ondansetron", drug_name="Ondansetron", dose=8, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_INFUSION, days=[1], is_core_drug=False),
        ],
        take_home_medicines=[
            ProtocolDrug(drug_id="ondansetron", drug_name="Ondansetron", dose=8, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1, 2], frequency="Twice daily", is_core_drug=False),
            ProtocolDrug(drug_id="metoclopramide", drug_name="Metoclopramide", dose=10, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 5)), frequency="Three times daily PRN",
                prn=True, is_core_drug=False),
        ],
        dose_modifications=[
            DoseModificationRule(rule_id="neuropathy_bv", parameter="bilirubin", condition_type="greater_than",
                threshold_value=50, affected_drugs=["brentuximab"], modification_type="omit",
                description="Hepatic impairment (bili >50): omit brentuximab"),
            DoseModificationRule(rule_id="bili_dox_bravd", parameter="bilirubin", condition_type="greater_than",
                threshold_value=85, affected_drugs=["doxorubicin"], modification_type="omit",
                description="Bilirubin >85: omit doxorubicin"),
        ],
        monitoring=["FBC, U&E, LFTs before each cycle", "Peripheral neuropathy assessment each cycle",
                    "G-CSF primary prophylaxis mandatory", "Monitor for PML (brentuximab — JC virus)"],
        warnings=["G-CSF MANDATORY primary prophylaxis (14-day cycle)",
                  "Peripheral neuropathy — reduce/withhold brentuximab if Grade ≥2",
                  "Pulmonary toxicity (brentuximab) — monitor for new respiratory symptoms",
                  "Do NOT give with bleomycin — pulmonary toxicity risk"],
    ),

    # =========================================================
    # LEUKAEMIA PROTOCOLS
    # =========================================================

    # 7+3 induction (AML)
    "aml_7plus3": Protocol(
        id="aml_7plus3",
        name="7+3 AML Induction",
        code="AML-7+3",
        full_name="Cytarabine 7-day + Daunorubicin/Idarubicin 3-day (AML Induction)",
        indication="Acute Myeloid Leukaemia — induction chemotherapy (fit patients)",
        cycle_length_days=28,
        total_cycles=1,
        version="1.0",
        treatment_intent="curative",
        drugs=[
            ProtocolDrug(drug_id="cytarabine", drug_name="Cytarabine", dose=100, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=list(range(1, 8)), duration_minutes=1440,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=500, administration_order=1,
                frequency="Continuous 24-hour infusion", special_instructions="Days 1–7 continuous infusion"),
            ProtocolDrug(drug_id="idarubicin", drug_name="Idarubicin", dose=12, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[1, 2, 3], duration_minutes=30,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=100, administration_order=2,
                special_instructions="Vesicant — ensure patent central line. Daunorubicin 60 mg/m² can substitute."),
        ],
        pre_medications=[
            ProtocolDrug(drug_id="ondansetron", drug_name="Ondansetron", dose=8, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_INFUSION, days=list(range(1, 8)), is_core_drug=False),
            ProtocolDrug(drug_id="allopurinol", drug_name="Allopurinol", dose=300, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 8)), frequency="Once daily", is_core_drug=False,
                special_instructions="Tumour lysis prophylaxis — continue until blasts cleared"),
        ],
        take_home_medicines=[
            ProtocolDrug(drug_id="cotrimoxazole", drug_name="Co-trimoxazole", dose=960, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1, 3, 5], frequency="Mon/Wed/Fri", is_core_drug=False,
                special_instructions="PCP prophylaxis — start once ANC >0.5"),
            ProtocolDrug(drug_id="fluconazole", drug_name="Fluconazole", dose=200, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 29)), frequency="Once daily", is_core_drug=False,
                special_instructions="Antifungal prophylaxis during neutropenia"),
        ],
        dose_modifications=[
            DoseModificationRule(rule_id="bili_30_ida", parameter="bilirubin", condition_type="range",
                threshold_low=30, threshold_high=85, affected_drugs=["idarubicin"],
                modification_type="reduce", modification_percent=50,
                description="Bilirubin 30–85 µmol/L: reduce idarubicin to 50%"),
            DoseModificationRule(rule_id="bili_gt85_ida", parameter="bilirubin", condition_type="greater_than",
                threshold_value=85, affected_drugs=["idarubicin"], modification_type="omit",
                description="Bilirubin >85 µmol/L: omit idarubicin"),
            DoseModificationRule(rule_id="crcl_lt30_arac", parameter="creatinine_clearance",
                condition_type="less_than", threshold_value=30, affected_drugs=["cytarabine"],
                modification_type="reduce", modification_percent=50,
                description="CrCl <30: reduce cytarabine to 50% (renal accumulation risk)"),
        ],
        monitoring=["Daily FBC, U&E, LFTs during induction", "Bone marrow day 14–16 for response assessment",
                    "TLS monitoring — urate, potassium, phosphate, calcium daily x5",
                    "Baseline LVEF before anthracycline", "ECHO if cumulative anthracycline >300 mg/m²"],
        warnings=["Inpatient treatment required — prolonged myelosuppression expected",
                  "Tumour lysis syndrome prophylaxis MANDATORY (high disease burden)",
                  "Antifungal prophylaxis essential during neutropenia",
                  "Idarubicin anthracycline equivalent factor 5.0 — count towards cumulative limit"],
    ),

    # AML consolidation (HIDAC)
    "hidac": Protocol(
        id="hidac",
        name="HiDAC",
        code="HIDAC",
        full_name="High-Dose Cytarabine (AML Consolidation)",
        indication="Acute Myeloid Leukaemia — consolidation following induction (favourable/intermediate risk)",
        cycle_length_days=28,
        total_cycles=3,
        version="1.0",
        treatment_intent="curative",
        drugs=[
            ProtocolDrug(drug_id="cytarabine", drug_name="Cytarabine", dose=3000, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[1, 3, 5], duration_minutes=180,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=500, administration_order=1,
                frequency="Every 12 hours x2 doses per day",
                special_instructions="Steroid eye drops MANDATORY to prevent conjunctivitis. Neurological assessment before each dose."),
        ],
        pre_medications=[
            ProtocolDrug(drug_id="prednisolone_eyedrops", drug_name="Prednisolone 1% eye drops", dose=1,
                dose_unit=DoseUnit.DROP, route=RouteOfAdministration.TOPICAL,
                days=[1, 2, 3, 4, 5, 6], frequency="Every 6 hours", is_core_drug=False,
                special_instructions="Start with cytarabine, continue 24h after last dose"),
            ProtocolDrug(drug_id="ondansetron", drug_name="Ondansetron", dose=8, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_INFUSION, days=[1, 3, 5], is_core_drug=False),
        ],
        take_home_medicines=[
            ProtocolDrug(drug_id="cotrimoxazole", drug_name="Co-trimoxazole", dose=960, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1, 3, 5], frequency="Mon/Wed/Fri", is_core_drug=False,
                special_instructions="PCP prophylaxis"),
            ProtocolDrug(drug_id="fluconazole", drug_name="Fluconazole", dose=200, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 29)), frequency="Once daily", is_core_drug=False),
        ],
        dose_modifications=[
            DoseModificationRule(rule_id="age_hidac", parameter="creatinine_clearance", condition_type="less_than",
                threshold_value=50, affected_drugs=["cytarabine"], modification_type="reduce",
                modification_percent=50, description="CrCl <50 ml/min or age >60: reduce HiDAC to 1500 mg/m²"),
            DoseModificationRule(rule_id="neuro_hidac", parameter="creatinine_clearance", condition_type="less_than",
                threshold_value=30, affected_drugs=["cytarabine"], modification_type="omit",
                description="CrCl <30: omit HiDAC — severe neurotoxicity risk"),
        ],
        monitoring=["Neurological assessment before each dose (cerebellar toxicity)", "FBC, U&E, LFTs before each cycle",
                    "Ophthalmology review if visual symptoms develop"],
        warnings=["Steroid eye drops MANDATORY — cytarabine conjunctivitis", "Cerebellar toxicity risk at high doses — reduce if age >60 or CrCl <50",
                  "HOLD if cerebellar signs develop (nystagmus, ataxia, dysarthria)"],
    ),

    # Azacitidine (MDS/AML elderly)
    "azacitidine": Protocol(
        id="azacitidine",
        name="Azacitidine",
        code="AZACITIDINE",
        full_name="Azacitidine monotherapy (hypomethylating agent)",
        indication="Myelodysplastic Syndrome (IPSS Int-2/High); AML (>20% blasts) — unfit for intensive chemotherapy",
        cycle_length_days=28,
        total_cycles=6,
        version="1.0",
        treatment_intent="palliative",
        drugs=[
            ProtocolDrug(drug_id="azacitidine", drug_name="Azacitidine", dose=75, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.SC, days=[1, 2, 3, 4, 5, 6, 7], administration_order=1,
                special_instructions="Subcutaneous injection. Rotate sites. Warm to room temperature before injection. Alternative 5-2-2 schedule: days 1–5 then 8–9."),
        ],
        take_home_medicines=[
            ProtocolDrug(drug_id="allopurinol", drug_name="Allopurinol", dose=300, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 29)), frequency="Once daily", is_core_drug=False,
                special_instructions="Tumour lysis prophylaxis, especially first 2 cycles"),
        ],
        dose_modifications=[
            DoseModificationRule(rule_id="crcl_lt30_aza", parameter="creatinine_clearance", condition_type="less_than",
                threshold_value=30, affected_drugs=["azacitidine"], modification_type="reduce",
                modification_percent=50, description="CrCl <30 ml/min: reduce azacitidine to 50%"),
            DoseModificationRule(rule_id="bili_gt85_aza", parameter="bilirubin", condition_type="greater_than",
                threshold_value=85, affected_drugs=["azacitidine"], modification_type="reduce",
                modification_percent=50, description="Bilirubin >85 µmol/L: reduce azacitidine to 50%"),
            DoseModificationRule(rule_id="neut_lt1_aza", parameter="neutrophils", condition_type="less_than",
                threshold_value=1.0, affected_drugs=["azacitidine"], modification_type="delay",
                delay_days=7, description="Neutrophils <1.0: delay cycle by 1 week"),
            DoseModificationRule(rule_id="plt_lt50_aza", parameter="platelets", condition_type="less_than",
                threshold_value=50, affected_drugs=["azacitidine"], modification_type="delay",
                delay_days=7, description="Platelets <50: delay cycle by 1 week"),
        ],
        monitoring=["FBC before each cycle and during nadir (day 10–14)",
                    "U&E, LFTs, urate before cycles 1 and 2",
                    "Bone marrow reassessment after cycle 4–6 to assess response",
                    "Monitor for injection site reactions"],
        warnings=["Minimum 6 cycles required before assessing response",
                  "Myelosuppression expected — worse in cycles 1–2",
                  "Response rate 40–60% but may take 4–6 cycles to manifest"],
    ),

    # Azacitidine + Venetoclax (AML elderly)
    "aza_ven": Protocol(
        id="aza_ven",
        name="Azacitidine + Venetoclax",
        code="AZA-VEN",
        full_name="Azacitidine + Venetoclax (VIALE-A regimen)",
        indication="Newly diagnosed AML — unfit for intensive chemotherapy (elderly/comorbidities)",
        cycle_length_days=28,
        total_cycles=12,
        version="1.0",
        treatment_intent="palliative",
        drugs=[
            ProtocolDrug(drug_id="azacitidine", drug_name="Azacitidine", dose=75, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.SC, days=[1, 2, 3, 4, 5, 6, 7], administration_order=1,
                special_instructions="SC injection days 1–7. Alternative IV if injection site issues."),
            ProtocolDrug(drug_id="venetoclax", drug_name="Venetoclax", dose=400, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 29)), frequency="Once daily with food",
                administration_order=2, special_instructions=(
                    "RAMP-UP in cycle 1 ONLY: Day 1=100mg, Day 2=200mg, Day 3=400mg (maintenance). "
                    "Avoid grapefruit juice. Strong CYP3A4 inhibitors require dose reduction to 100mg. "
                    "Moderate CYP3A4 inhibitors reduce to 200mg."
                )),
        ],
        take_home_medicines=[
            ProtocolDrug(drug_id="allopurinol", drug_name="Allopurinol", dose=300, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 8)), frequency="Once daily", is_core_drug=False,
                special_instructions="Tumour lysis prophylaxis — MANDATORY first cycle"),
            ProtocolDrug(drug_id="cotrimoxazole", drug_name="Co-trimoxazole", dose=960, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1, 3, 5], frequency="Mon/Wed/Fri", is_core_drug=False,
                special_instructions="PCP prophylaxis"),
        ],
        dose_modifications=[
            DoseModificationRule(rule_id="cyp3a4_strong_ven", parameter="creatinine_clearance",
                condition_type="less_than", threshold_value=30, affected_drugs=["venetoclax"],
                modification_type="reduce", modification_percent=25,
                description="CrCl <30: reduce venetoclax to 100mg (25%). Monitor closely."),
            DoseModificationRule(rule_id="neut_lt0.5_ven", parameter="neutrophils", condition_type="less_than",
                threshold_value=0.5, affected_drugs=["venetoclax"], modification_type="delay",
                delay_days=7, description="ANC <0.5 after cycle 1: hold venetoclax until recovery"),
            DoseModificationRule(rule_id="crcl_lt30_aza2", parameter="creatinine_clearance",
                condition_type="less_than", threshold_value=30, affected_drugs=["azacitidine"],
                modification_type="reduce", modification_percent=50,
                description="CrCl <30: reduce azacitidine to 50%"),
        ],
        monitoring=["FBC twice weekly during cycles 1–3, then before each cycle",
                    "TLS monitoring — daily urate, K, Ca, PO4 for days 1–5 of cycle 1",
                    "U&E, LFTs before each cycle", "CYP3A4 drug interaction check EVERY cycle"],
        warnings=["TUMOUR LYSIS SYNDROME RISK — mandatory prophylaxis and monitoring in cycle 1",
                  "Venetoclax ramp-up in cycle 1 ONLY — do not restart ramp-up in subsequent cycles",
                  "Check ALL concurrent medications for CYP3A4 interactions every cycle",
                  "Strong CYP3A4 inhibitors (fluconazole, posaconazole) reduce venetoclax to 100mg",
                  "Avoid grapefruit, Seville oranges, starfruit"],
    ),

    # FLAG-Ida (AML salvage)
    "flagida": Protocol(
        id="flagida",
        name="FLAG-Ida",
        code="FLAG-IDA",
        full_name="Fludarabine-Cytarabine-G-CSF-Idarubicin (AML salvage/relapsed)",
        indication="Relapsed/refractory AML; high-risk MDS — salvage therapy",
        cycle_length_days=28,
        total_cycles=2,
        version="1.0",
        treatment_intent="curative",
        drugs=[
            ProtocolDrug(drug_id="fludarabine", drug_name="Fludarabine", dose=30, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[1, 2, 3, 4, 5], duration_minutes=30,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=100, administration_order=1,
                special_instructions="Give 4 hours before cytarabine for optimal synergy"),
            ProtocolDrug(drug_id="cytarabine", drug_name="Cytarabine", dose=2000, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[1, 2, 3, 4, 5], duration_minutes=240,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=500, administration_order=2,
                special_instructions="Start 4 hours after fludarabine each day"),
            ProtocolDrug(drug_id="idarubicin", drug_name="Idarubicin", dose=10, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[1, 2, 3], duration_minutes=30,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=100, administration_order=3),
            ProtocolDrug(drug_id="gcsf", drug_name="G-CSF (Filgrastim)", dose=300, dose_unit=DoseUnit.MCG,
                route=RouteOfAdministration.SC, days=list(range(0, 6)), frequency="Once daily",
                administration_order=0, special_instructions="Start day 0 (day before chemotherapy), continue until ANC >0.5"),
        ],
        pre_medications=[
            ProtocolDrug(drug_id="ondansetron", drug_name="Ondansetron", dose=8, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_INFUSION, days=list(range(1, 6)), is_core_drug=False),
            ProtocolDrug(drug_id="allopurinol", drug_name="Allopurinol", dose=300, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 8)), frequency="Once daily", is_core_drug=False),
        ],
        take_home_medicines=[
            ProtocolDrug(drug_id="cotrimoxazole", drug_name="Co-trimoxazole", dose=960, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1, 3, 5], frequency="Mon/Wed/Fri", is_core_drug=False),
            ProtocolDrug(drug_id="fluconazole", drug_name="Fluconazole", dose=200, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 29)), frequency="Once daily", is_core_drug=False),
            ProtocolDrug(drug_id="aciclovir", drug_name="Aciclovir", dose=400, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 29)), frequency="Twice daily", is_core_drug=False,
                special_instructions="Antiviral prophylaxis — fludarabine causes lifelong T-cell immunosuppression"),
        ],
        dose_modifications=[
            DoseModificationRule(rule_id="crcl_lt30_flu", parameter="creatinine_clearance", condition_type="less_than",
                threshold_value=30, affected_drugs=["fludarabine"], modification_type="omit",
                description="CrCl <30: omit fludarabine — severe renal impairment"),
            DoseModificationRule(rule_id="bili_ida_flag", parameter="bilirubin", condition_type="range",
                threshold_low=30, threshold_high=85, affected_drugs=["idarubicin"],
                modification_type="reduce", modification_percent=50, description="Bilirubin 30–85: reduce idarubicin 50%"),
            DoseModificationRule(rule_id="bili_gt85_ida_flag", parameter="bilirubin", condition_type="greater_than",
                threshold_value=85, affected_drugs=["idarubicin"], modification_type="omit",
                description="Bilirubin >85: omit idarubicin"),
        ],
        monitoring=["Daily FBC, U&E during treatment", "TLS monitoring days 1–5",
                    "Bone marrow assessment day 21–28",
                    "Neurological assessment (fludarabine neurotoxicity at high cumulative doses)"],
        warnings=["Fludarabine causes LIFELONG T-cell immunosuppression — irradiated blood products FOR LIFE",
                  "PCP, antifungal, antiviral prophylaxis ALL mandatory",
                  "G-CSF starts day BEFORE chemotherapy (day 0)",
                  "Prolonged aplasia expected — inpatient treatment required"],
    ),

    # CLL — FCR (fit CLL first-line)
    "fcr": Protocol(
        id="fcr",
        name="FCR",
        code="FCR",
        full_name="Fludarabine-Cyclophosphamide-Rituximab",
        indication="Fit Chronic Lymphocytic Leukaemia — first-line (IGHV mutated, young fit patients)",
        cycle_length_days=28,
        total_cycles=6,
        version="1.0",
        treatment_intent="curative",
        drugs=[
            ProtocolDrug(drug_id="rituximab", drug_name="Rituximab", dose=375, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[1], diluent="Sodium chloride 0.9%",
                diluent_volume_ml=500, administration_order=1,
                special_instructions="Cycle 1: 375 mg/m². Cycles 2–6: 500 mg/m². Slow initial infusion rate."),
            ProtocolDrug(drug_id="fludarabine", drug_name="Fludarabine", dose=25, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[1, 2, 3], duration_minutes=30,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=100, administration_order=2),
            ProtocolDrug(drug_id="cyclophosphamide", drug_name="Cyclophosphamide", dose=250, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[1, 2, 3], duration_minutes=30,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=250, administration_order=3),
        ],
        pre_medications=[
            ProtocolDrug(drug_id="chlorphenamine", drug_name="Chlorphenamine", dose=10, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_BOLUS, days=[1], is_core_drug=False),
            ProtocolDrug(drug_id="paracetamol", drug_name="Paracetamol", dose=1000, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1], is_core_drug=False),
            ProtocolDrug(drug_id="ondansetron", drug_name="Ondansetron", dose=8, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_INFUSION, days=[1, 2, 3], is_core_drug=False),
            ProtocolDrug(drug_id="allopurinol", drug_name="Allopurinol", dose=300, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 29)), frequency="Once daily", is_core_drug=False,
                special_instructions="TLS prophylaxis — especially first cycle if high disease burden"),
        ],
        take_home_medicines=[
            ProtocolDrug(drug_id="cotrimoxazole", drug_name="Co-trimoxazole", dose=960, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1, 3, 5], frequency="Mon/Wed/Fri", is_core_drug=False,
                special_instructions="PCP prophylaxis — continue 6 months post-treatment"),
            ProtocolDrug(drug_id="aciclovir", drug_name="Aciclovir", dose=400, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 29)), frequency="Twice daily", is_core_drug=False,
                special_instructions="Antiviral prophylaxis — fludarabine lifelong immunosuppression"),
            ProtocolDrug(drug_id="ondansetron", drug_name="Ondansetron", dose=8, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1, 2, 3], frequency="Twice daily", is_core_drug=False),
        ],
        dose_modifications=[
            DoseModificationRule(rule_id="crcl_lt60_flu_fcr", parameter="creatinine_clearance",
                condition_type="range", threshold_low=30, threshold_high=60, affected_drugs=["fludarabine"],
                modification_type="reduce", modification_percent=50, description="CrCl 30–60: reduce fludarabine to 50%"),
            DoseModificationRule(rule_id="crcl_lt30_flu_fcr", parameter="creatinine_clearance",
                condition_type="less_than", threshold_value=30, affected_drugs=["fludarabine"],
                modification_type="omit", description="CrCl <30: omit fludarabine — use chlorambucil-based regimen"),
            DoseModificationRule(rule_id="crcl_lt30_cyc_fcr", parameter="creatinine_clearance",
                condition_type="less_than", threshold_value=20, affected_drugs=["cyclophosphamide"],
                modification_type="reduce", modification_percent=75,
                description="CrCl <20: reduce cyclophosphamide to 75%"),
        ],
        monitoring=["FBC, U&E, LFTs before each cycle and at nadir (day 10–14)",
                    "Hepatitis B serology MANDATORY before rituximab",
                    "CMV monitoring in high-risk patients", "Autoimmune haemolytic anaemia surveillance"],
        warnings=["Fludarabine — LIFELONG irradiated blood products required",
                  "FCR NOT recommended if CrCl <30 or age >65 — consider BR or chlorambucil-obinutuzumab",
                  "High TLS risk — especially bulky disease or high WBC",
                  "Hepatitis B reactivation — screen and prophylax all patients before rituximab"],
    ),

    # CLL — Chlorambucil + Obinutuzumab (unfit CLL)
    "clb_obi": Protocol(
        id="clb_obi",
        name="Chlorambucil-Obinutuzumab",
        code="CLB-OBI",
        full_name="Chlorambucil-Obinutuzumab (CLL11 / GAIA regimen)",
        indication="Previously untreated CLL — unfit patients (CIRS >6 or CrCl <70 ml/min)",
        cycle_length_days=28,
        total_cycles=6,
        version="1.0",
        treatment_intent="palliative",
        drugs=[
            ProtocolDrug(drug_id="obinutuzumab", drug_name="Obinutuzumab", dose=1000, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_INFUSION, days=[1, 8, 15], administration_order=1,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=250,
                special_instructions=(
                    "Cycle 1 ONLY: Split cycle 1 dose — Day 1: 100mg, Day 2: 900mg, Day 8: 1000mg, Day 15: 1000mg. "
                    "Cycles 2–6: Day 1 only 1000mg. "
                    "First infusion rate 25mg/hr — escalate by 50mg/hr every 30min if tolerated. Max 400mg/hr."
                )),
            ProtocolDrug(drug_id="chlorambucil", drug_name="Chlorambucil", dose=0.5, dose_unit=DoseUnit.MG_KG,
                route=RouteOfAdministration.ORAL, days=[1, 15], frequency="Single dose on days 1 and 15",
                administration_order=2, special_instructions="Take on an empty stomach. Max single dose 50mg."),
        ],
        pre_medications=[
            ProtocolDrug(drug_id="chlorphenamine", drug_name="Chlorphenamine", dose=10, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_BOLUS, days=[1, 8, 15], is_core_drug=False),
            ProtocolDrug(drug_id="paracetamol", drug_name="Paracetamol", dose=1000, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1, 8, 15], is_core_drug=False),
            ProtocolDrug(drug_id="hydrocortisone", drug_name="Hydrocortisone", dose=100, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_BOLUS, days=[1, 8, 15], is_core_drug=False,
                special_instructions="Mandatory with obinutuzumab — high IRR risk on first infusion"),
            ProtocolDrug(drug_id="allopurinol", drug_name="Allopurinol", dose=300, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 29)), frequency="Once daily", is_core_drug=False,
                special_instructions="TLS prophylaxis — especially cycle 1"),
        ],
        take_home_medicines=[
            ProtocolDrug(drug_id="cotrimoxazole", drug_name="Co-trimoxazole", dose=960, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1, 3, 5], frequency="Mon/Wed/Fri", is_core_drug=False,
                special_instructions="PCP prophylaxis"),
            ProtocolDrug(drug_id="aciclovir", drug_name="Aciclovir", dose=400, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 29)), frequency="Twice daily", is_core_drug=False),
        ],
        dose_modifications=[
            DoseModificationRule(rule_id="crcl_lt30_clb", parameter="creatinine_clearance",
                condition_type="less_than", threshold_value=30, affected_drugs=["chlorambucil"],
                modification_type="reduce", modification_percent=50,
                description="CrCl <30: reduce chlorambucil to 50%"),
            DoseModificationRule(rule_id="neut_obi", parameter="neutrophils", condition_type="less_than",
                threshold_value=1.0, affected_drugs=["obinutuzumab", "chlorambucil"],
                modification_type="delay", delay_days=7,
                description="Neutrophils <1.0: delay until recovery ≥1.0"),
        ],
        monitoring=["FBC, U&E before each cycle and day 15 of cycle 1",
                    "TLS labs (urate, K, Ca, PO4) daily days 1–3 of cycle 1",
                    "Hepatitis B serology MANDATORY", "IgG levels — consider IVIG if recurrent infections"],
        warnings=["Obinutuzumab — HIGH infusion reaction risk, especially first dose",
                  "Split cycle 1 dosing schedule is MANDATORY (not standard 1000mg on day 1)",
                  "TLS risk in CLL — allopurinol mandatory, rasburicase if high burden",
                  "Hepatitis B reactivation screen before starting"],
    ),

    # ALL — UKALL (adult ALL induction, simplified)
    "all_induction": Protocol(
        id="all_induction",
        name="ALL Induction (UKALL14)",
        code="ALL-INDUCTION",
        full_name="Adult ALL Induction Phase 1 — Dexamethasone-Vincristine-Asparaginase-Daunorubicin",
        indication="Newly diagnosed Acute Lymphoblastic Leukaemia — induction phase",
        cycle_length_days=35,
        total_cycles=1,
        version="1.0",
        treatment_intent="curative",
        drugs=[
            ProtocolDrug(drug_id="dexamethasone", drug_name="Dexamethasone", dose=10, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.ORAL, days=list(range(1, 29)), frequency="Once daily",
                administration_order=1, special_instructions="Days 1–28 then taper over days 29–35"),
            ProtocolDrug(drug_id="vincristine", drug_name="Vincristine", dose=1.4, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_BOLUS, days=[1, 8, 15, 22], max_dose=2.0, max_dose_unit="mg",
                administration_order=2),
            ProtocolDrug(drug_id="daunorubicin", drug_name="Daunorubicin", dose=45, dose_unit=DoseUnit.MG_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[1, 8, 15, 22], duration_minutes=30,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=100, administration_order=3),
            ProtocolDrug(drug_id="peg_asparaginase", drug_name="PEG-Asparaginase", dose=1000, dose_unit=DoseUnit.UNITS_M2,
                route=RouteOfAdministration.IV_INFUSION, days=[4, 18], duration_minutes=120,
                diluent="Sodium chloride 0.9%", diluent_volume_ml=100, administration_order=4,
                special_instructions="Max 3750 units per dose. Monitor for pancreatitis, thrombosis, hypersensitivity."),
        ],
        pre_medications=[
            ProtocolDrug(drug_id="ondansetron", drug_name="Ondansetron", dose=8, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.IV_INFUSION, days=[1, 8, 15, 22], is_core_drug=False),
            ProtocolDrug(drug_id="allopurinol", drug_name="Allopurinol", dose=300, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 15)), frequency="Once daily", is_core_drug=False,
                special_instructions="TLS prophylaxis first 2 weeks"),
        ],
        take_home_medicines=[
            ProtocolDrug(drug_id="cotrimoxazole", drug_name="Co-trimoxazole", dose=960, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=[1, 3, 5], frequency="Mon/Wed/Fri", is_core_drug=False),
            ProtocolDrug(drug_id="fluconazole", drug_name="Fluconazole", dose=200, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 36)), frequency="Once daily", is_core_drug=False),
            ProtocolDrug(drug_id="aciclovir", drug_name="Aciclovir", dose=400, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 36)), frequency="Twice daily", is_core_drug=False),
        ],
        dose_modifications=[
            DoseModificationRule(rule_id="bili_dauno_all", parameter="bilirubin", condition_type="range",
                threshold_low=30, threshold_high=85, affected_drugs=["daunorubicin"],
                modification_type="reduce", modification_percent=50, description="Bilirubin 30–85: reduce daunorubicin 50%"),
            DoseModificationRule(rule_id="bili_gt85_dauno_all", parameter="bilirubin", condition_type="greater_than",
                threshold_value=85, affected_drugs=["daunorubicin"], modification_type="omit",
                description="Bilirubin >85: omit daunorubicin"),
            DoseModificationRule(rule_id="bili_vcr_all", parameter="bilirubin", condition_type="greater_than",
                threshold_value=50, affected_drugs=["vincristine"], modification_type="omit",
                description="Bilirubin >50: omit vincristine"),
        ],
        monitoring=["Daily FBC, U&E, LFTs, glucose during induction",
                    "Lipase/amylase if abdominal symptoms (PEG-asparaginase pancreatitis)",
                    "Fibrinogen, APTT, PT (asparaginase coagulopathy)",
                    "D-dimer — thrombosis risk with asparaginase",
                    "Bone marrow day 14 and day 29 for response assessment"],
        warnings=["PEG-Asparaginase pancreatitis risk — hold if lipase >3x ULN",
                  "Thrombosis risk — asparaginase reduces fibrinogen/antithrombin",
                  "Hyperglycaemia from dexamethasone — monitor glucose and treat",
                  "Daunorubicin cumulative limit applies — contributes to anthracycline total",
                  "Vincristine 2mg absolute cap — FATAL if exceeded"],
    ),

    # CML — Imatinib (TKI maintenance)
    "imatinib": Protocol(
        id="imatinib",
        name="Imatinib",
        code="IMATINIB",
        full_name="Imatinib mesylate (BCR-ABL1 TKI — Gleevec/Glivec)",
        indication="Chronic Myeloid Leukaemia (CML) — chronic phase; Philadelphia chromosome positive ALL",
        cycle_length_days=28,
        total_cycles=99,
        version="1.0",
        treatment_intent="palliative",
        drugs=[
            ProtocolDrug(drug_id="imatinib", drug_name="Imatinib", dose=400, dose_unit=DoseUnit.MG,
                route=RouteOfAdministration.ORAL, days=list(range(1, 29)), frequency="Once daily with food",
                administration_order=1, special_instructions=(
                    "CML chronic phase: 400mg once daily. "
                    "CML accelerated/blast phase: 600–800mg daily. "
                    "Take with large glass of water. Avoid grapefruit."
                )),
        ],
        dose_modifications=[
            DoseModificationRule(rule_id="crcl_lt30_ima", parameter="creatinine_clearance",
                condition_type="less_than", threshold_value=30, affected_drugs=["imatinib"],
                modification_type="reduce", modification_percent=50,
                description="CrCl <30: reduce imatinib to 200mg daily"),
            DoseModificationRule(rule_id="bili_gt85_ima", parameter="bilirubin", condition_type="greater_than",
                threshold_value=85, affected_drugs=["imatinib"], modification_type="reduce",
                modification_percent=50, description="Bilirubin >85: reduce imatinib to 200mg"),
            DoseModificationRule(rule_id="neut_lt1_ima", parameter="neutrophils", condition_type="less_than",
                threshold_value=1.0, affected_drugs=["imatinib"], modification_type="delay",
                delay_days=14, description="ANC <1.0: hold until ≥1.5, then restart 400mg"),
            DoseModificationRule(rule_id="plt_lt50_ima", parameter="platelets", condition_type="less_than",
                threshold_value=50, affected_drugs=["imatinib"], modification_type="delay",
                delay_days=14, description="Platelets <50: hold until ≥75, then restart"),
        ],
        monitoring=["FBC monthly for 3 months, then every 3 months",
                    "LFTs monthly for 3 months, then every 3 months",
                    "BCR-ABL1 PCR every 3 months — target MMR by 12 months",
                    "FISH/cytogenetics at 3 and 6 months then annually",
                    "Echocardiogram if cardiac risk factors"],
        warnings=["BCR-ABL1 PCR monitoring MANDATORY — track treatment response",
                  "Multiple CYP3A4 drug interactions — check every prescription change",
                  "Oedema common — especially periorbital and lower limb",
                  "Do NOT stop without haematologist approval even if PCR negative"],
    ),
}


def infer_required_patient_fields(protocol: Protocol) -> dict[str, str]:
    """
    Dynamically derive which PatientData fields are mandatory for a protocol
    based on the drugs it contains. Returns {field_name: reason}.
    """
    all_drug_names = " ".join(
        d.drug_name.lower()
        for d in (protocol.drugs + protocol.pre_medications + protocol.take_home_medicines)
    )
    fields: dict[str, str] = {}

    # Anti-CD20 (rituximab/obinutuzumab) → virology mandatory
    if any(x in all_drug_names for x in ["rituximab", "obinutuzumab"]):
        fields["hep_b_surface_antigen"] = "Rituximab/obinutuzumab can reactivate hepatitis B — HBsAg required"
        fields["hep_b_core_antibody"] = "HBcAb positive = prior HBV exposure; prophylactic antivirals needed with anti-CD20"
        fields["hep_c_antibody"] = "Anti-CD20 therapy — baseline HCV required"
        fields["hiv_status"] = "Anti-CD20 therapy — baseline HIV required"
        fields["ebv_status"] = "Rituximab — EBV reactivation risk in immunosuppressed"
        fields["histology"] = "CD20-positive lymphoma histology required for correct protocol selection"
        fields["disease_stage"] = "Stage affects total cycles and treatment intent"
        fields["ldh"] = "Lymphoma prognostic marker (IPI score)"
        fields["beta2_microglobulin"] = "Lymphoma prognostic marker"

    # Anthracyclines → cardiac workup
    if any(x in all_drug_names for x in ["doxorubicin", "daunorubicin", "epirubicin", "idarubicin"]):
        fields["lvef_percent"] = "Anthracycline — baseline LVEF/ECHO required before starting"
        fields["prior_anthracycline_dose_mg_m2"] = "Cumulative anthracycline dose tracking — lifetime limit 450 mg/m²"
        fields["prior_cardiac_history"] = "Cardiac history reduces anthracycline limit to 400 mg/m²"
        fields["prior_mediastinal_radiation"] = "Prior mediastinal RT reduces anthracycline limit to 350 mg/m²"

    # Bleomycin → pulmonary baseline
    if "bleomycin" in all_drug_names:
        fields["lung_function_fev1"] = "Bleomycin — baseline pulmonary function (FEV1) required; smokers at much higher risk"
        fields["smoker"] = "Smoking significantly increases bleomycin pulmonary toxicity risk"
        fields["prior_bleomycin_units"] = "Cumulative bleomycin dose tracking — lifetime limit 400,000 units"

    # Venetoclax → TLS risk markers
    if "venetoclax" in all_drug_names:
        fields["ldh"] = "Venetoclax — TLS risk stratification requires LDH"
        fields["urate"] = "Venetoclax — baseline urate for TLS monitoring"
        fields["calcium"] = "Venetoclax — TLS calcium monitoring"
        fields["beta2_microglobulin"] = "CLL/AML prognostic and TLS risk marker"

    # Rasburicase → G6PD (absolute contraindication — haemolytic anaemia)
    if "rasburicase" in all_drug_names:
        fields["g6pd_status"] = "CRITICAL: Rasburicase causes severe haemolytic anaemia in G6PD deficiency — must check before prescribing"

    # Bortezomib → VZV reactivation
    if "bortezomib" in all_drug_names:
        fields["vzv_status"] = "Bortezomib — VZV reactivation risk; aciclovir prophylaxis mandatory"

    # Fludarabine/bendamustine/cladribine → profound immunosuppression
    if any(x in all_drug_names for x in ["fludarabine", "bendamustine", "cladribine"]):
        fields["cmv_status"] = "Profoundly immunosuppressive agent — CMV reactivation risk"
        fields["vzv_status"] = "Immunosuppressive agent — VZV prophylaxis recommended"

    # AML/MDS drugs → cytogenetics/histology
    if any(x in all_drug_names for x in ["cytarabine", "azacitidine", "decitabine", "idarubicin", "daunorubicin"]):
        fields["ldh"] = fields.get("ldh", "AML/MDS — LDH is TLS and disease activity marker")
        fields["histology"] = fields.get("histology", "AML/MDS — cytogenetic/mutation profile affects treatment eligibility")
        fields["disease_stage"] = fields.get("disease_stage", "AML/MDS staging affects protocol selection")
        fields["urate"] = fields.get("urate", "AML/MDS — TLS risk; baseline urate required")

    # TKIs → mutation status required
    if any(x in all_drug_names for x in ["imatinib", "gilteritinib", "midostaurin"]):
        fields["histology"] = fields.get("histology", "TKI — mutation confirmation (BCR-ABL / FLT3) required before starting")

    # Cisplatin/carboplatin → renal function (mark explicitly)
    if any(x in all_drug_names for x in ["cisplatin", "carboplatin", "oxaliplatin"]):
        fields["creatinine_clearance"] = "Platinum compound — creatinine clearance is mandatory for dose calculation and safety"

    return fields


def get_all_protocols() -> dict[str, Protocol]:
    """Return all available protocols, augmenting each with inferred required_patient_fields."""
    result = {}
    for k, p in PROTOCOLS.items():
        if not p.required_patient_fields:
            inferred = infer_required_patient_fields(p)
            if inferred:
                result[k] = p.model_copy(update={"required_patient_fields": inferred})
                continue
        result[k] = p
    return result


def get_all_drugs() -> dict[str, Drug]:
    """Return all drug definitions"""
    return DRUGS

# ============= DYNAMIC LOADING =============
import json
import os
from pathlib import Path

def load_ingested_protocols():
    """Load protocols ingested from PDFs"""
    ingested_file = Path(__file__).parent / "ingested_protocols.json"
    if not ingested_file.exists():
        return

    try:
        with open(ingested_file, 'r') as f:
            data = json.load(f)
            
        for p_data in data:
            try:
                # Convert dictionary back to Protocol object
                # We need to handle nested objects (drugs, modifications etc)
                # For now, simplistic approach: assuming Gemini output matches Model structure
                # A robust implementation would use Pydantic parsing:
                p = Protocol.model_validate(p_data)
                
                # Check for ID conflict
                if p.id in PROTOCOLS:
                    print(f"Warning: Overwriting protocol {p.id} from ingested data")
                
                PROTOCOLS[p.id] = p
                print(f"Loaded ingested protocol: {p.name} ({p.code})")
                
            except Exception as e:
                print(f"Failed to load ingested protocol {p_data.get('protocol_code', 'unknown')}: {e}")
                
    except Exception as e:
        print(f"Error loading ingested protocols: {e}")

# Load them on startup
load_ingested_protocols()
