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
            # Hepatic - Doxorubicin
            DoseModificationRule(
                parameter="bilirubin",
                condition="30-50",
                affected_drugs=["doxorubicin"],
                modification="reduce_50",
                modification_percent=50,
                description="Bilirubin 30-50 µmol/L: reduce doxorubicin to 50%"
            ),
            DoseModificationRule(
                parameter="bilirubin",
                condition="> 85",
                affected_drugs=["doxorubicin"],
                modification="omit",
                description="Bilirubin > 85 µmol/L: omit doxorubicin"
            ),
            # Hepatic - Vincristine
            DoseModificationRule(
                parameter="bilirubin",
                condition="30-51",
                affected_drugs=["vincristine"],
                modification="reduce_50",
                modification_percent=50,
                description="Bilirubin 30-51 µmol/L: reduce vincristine to 50%"
            ),
            DoseModificationRule(
                parameter="bilirubin",
                condition="> 51",
                affected_drugs=["vincristine"],
                modification="omit",
                description="Bilirubin > 51 µmol/L: omit vincristine"
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
}


def get_all_protocols() -> dict[str, Protocol]:
    """Return all available protocols"""
    return PROTOCOLS


def get_all_drugs() -> dict[str, Drug]:
    """Return all drug definitions"""
    return DRUGS
