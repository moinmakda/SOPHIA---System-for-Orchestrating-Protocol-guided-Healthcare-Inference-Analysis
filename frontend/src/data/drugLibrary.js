/**
 * Comprehensive Drug Library for SOPHIA
 * Contains common chemotherapy agents, targeted therapies, and supportive care drugs
 */

export const DRUG_LIBRARY = {
  // TARGETED THERAPIES
  azacitidine: {
    drug_id: 'azacitidine',
    drug_name: 'Azacitidine',
    dose: 75,
    dose_unit: 'mg/m²',
    route: 'Subcutaneous',
    days: [1, 2, 3, 4, 5, 6, 7],
    duration_minutes: null,
    diluent: null,
    diluent_volume_ml: null,
    max_dose: null,
    special_instructions: 'Rotate injection sites. Give at room temperature.',
    category: 'main',
    drug_class: 'Hypomethylating agent',
  },

  venetoclax: {
    drug_id: 'venetoclax',
    drug_name: 'Venetoclax',
    dose: 400,
    dose_unit: 'mg',
    route: 'Oral',
    days: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28],
    frequency: 'Once daily',
    duration_minutes: null,
    diluent: null,
    diluent_volume_ml: null,
    max_dose: 400,
    special_instructions: 'Take with food and water. Requires dose ramp-up on first cycle. Monitor for tumor lysis syndrome.',
    category: 'main',
    drug_class: 'BCL-2 inhibitor',
  },

  gilteritinib: {
    drug_id: 'gilteritinib',
    drug_name: 'Gilteritinib',
    dose: 120,
    dose_unit: 'mg',
    route: 'Oral',
    days: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28],
    frequency: 'Once daily',
    duration_minutes: null,
    diluent: null,
    diluent_volume_ml: null,
    max_dose: 120,
    special_instructions: 'FLT3 mutation required. Monitor QTc interval.',
    category: 'main',
    drug_class: 'FLT3 inhibitor',
  },

  // CHEMOTHERAPY AGENTS
  rituximab: {
    drug_id: 'rituximab',
    drug_name: 'Rituximab',
    dose: 375,
    dose_unit: 'mg/m²',
    route: 'IV infusion',
    days: [1],
    duration_minutes: 120,
    diluent: 'Sodium chloride 0.9%',
    diluent_volume_ml: 250,
    max_dose: null,
    special_instructions: 'First infusion may take longer. Premedicate with acetaminophen and antihistamine.',
    category: 'main',
    drug_class: 'Monoclonal antibody',
  },

  cyclophosphamide: {
    drug_id: 'cyclophosphamide',
    drug_name: 'Cyclophosphamide',
    dose: 750,
    dose_unit: 'mg/m²',
    route: 'IV infusion',
    days: [1],
    duration_minutes: 60,
    diluent: 'Sodium chloride 0.9%',
    diluent_volume_ml: 250,
    max_dose: null,
    special_instructions: 'Ensure adequate hydration. Give mesna for bladder protection if dose >1g/m².',
    category: 'main',
    drug_class: 'Alkylating agent',
  },

  doxorubicin: {
    drug_id: 'doxorubicin',
    drug_name: 'Doxorubicin',
    dose: 50,
    dose_unit: 'mg/m²',
    route: 'IV infusion',
    days: [1],
    duration_minutes: 15,
    diluent: 'Sodium chloride 0.9%',
    diluent_volume_ml: 100,
    max_dose: null,
    special_instructions: 'Vesicant - ensure patent IV. Monitor cumulative dose (max 450 mg/m²). Causes red urine.',
    category: 'main',
    drug_class: 'Anthracycline',
  },

  vincristine: {
    drug_id: 'vincristine',
    drug_name: 'Vincristine',
    dose: 1.4,
    dose_unit: 'mg/m²',
    route: 'IV bolus',
    days: [1],
    duration_minutes: 5,
    diluent: null,
    diluent_volume_ml: null,
    max_dose: 2,
    special_instructions: 'FATAL IF GIVEN INTRATHECALLY. Cap at 2mg total dose. Monitor for neuropathy.',
    category: 'main',
    drug_class: 'Vinca alkaloid',
  },

  cytarabine: {
    drug_id: 'cytarabine',
    drug_name: 'Cytarabine',
    dose: 100,
    dose_unit: 'mg/m²',
    route: 'IV infusion',
    days: [1, 2, 3, 4, 5, 6, 7],
    frequency: 'Twice daily',
    duration_minutes: 30,
    diluent: 'Sodium chloride 0.9%',
    diluent_volume_ml: 100,
    max_dose: null,
    special_instructions: 'Can cause flu-like symptoms. Use steroid eye drops for high doses.',
    category: 'main',
    drug_class: 'Antimetabolite',
  },

  // PREMEDICATIONS & SUPPORTIVE CARE
  dexamethasone: {
    drug_id: 'dexamethasone',
    drug_name: 'Dexamethasone',
    dose: 12,
    dose_unit: 'mg',
    route: 'IV infusion',
    days: [1],
    duration_minutes: 15,
    diluent: 'Sodium chloride 0.9%',
    diluent_volume_ml: 50,
    max_dose: null,
    special_instructions: 'Give as antiemetic and premedication.',
    category: 'premedication',
    drug_class: 'Corticosteroid',
  },

  ondansetron: {
    drug_id: 'ondansetron',
    drug_name: 'Ondansetron',
    dose: 8,
    dose_unit: 'mg',
    route: 'IV infusion',
    days: [1],
    duration_minutes: 15,
    diluent: 'Sodium chloride 0.9%',
    diluent_volume_ml: 50,
    max_dose: 16,
    special_instructions: 'Give 30 minutes before chemotherapy.',
    category: 'premedication',
    drug_class: '5-HT3 antagonist',
  },

  diphenhydramine: {
    drug_id: 'diphenhydramine',
    drug_name: 'Diphenhydramine',
    dose: 25,
    dose_unit: 'mg',
    route: 'IV infusion',
    days: [1],
    duration_minutes: 15,
    diluent: 'Sodium chloride 0.9%',
    diluent_volume_ml: 50,
    max_dose: 50,
    special_instructions: 'Give as premedication for hypersensitivity prevention.',
    category: 'premedication',
    drug_class: 'Antihistamine',
  },

  acetaminophen: {
    drug_id: 'acetaminophen',
    drug_name: 'Acetaminophen',
    dose: 650,
    dose_unit: 'mg',
    route: 'Oral',
    days: [1],
    frequency: 'Once',
    duration_minutes: null,
    diluent: null,
    diluent_volume_ml: null,
    max_dose: 1000,
    special_instructions: 'Give 30-60 minutes before rituximab.',
    category: 'premedication',
    drug_class: 'Analgesic/antipyretic',
  },

  // TAKE-HOME MEDICATIONS
  allopurinol: {
    drug_id: 'allopurinol',
    drug_name: 'Allopurinol',
    dose: 300,
    dose_unit: 'mg',
    route: 'Oral',
    days: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21],
    frequency: 'Once daily',
    duration_minutes: null,
    diluent: null,
    diluent_volume_ml: null,
    max_dose: 600,
    special_instructions: 'For tumor lysis syndrome prevention. Take with food and plenty of water.',
    category: 'take_home',
    drug_class: 'Xanthine oxidase inhibitor',
  },

  prednisone: {
    drug_id: 'prednisone',
    drug_name: 'Prednisone',
    dose: 100,
    dose_unit: 'mg',
    route: 'Oral',
    days: [1, 2, 3, 4, 5],
    frequency: 'Once daily',
    duration_minutes: null,
    diluent: null,
    diluent_volume_ml: null,
    max_dose: null,
    special_instructions: 'Take with food in the morning.',
    category: 'take_home',
    drug_class: 'Corticosteroid',
  },

  metoclopramide: {
    drug_id: 'metoclopramide',
    drug_name: 'Metoclopramide',
    dose: 10,
    dose_unit: 'mg',
    route: 'Oral',
    days: [1, 2, 3],
    frequency: 'Three times daily',
    duration_minutes: null,
    diluent: null,
    diluent_volume_ml: null,
    max_dose: 10,
    special_instructions: 'Take 30 minutes before meals for nausea.',
    category: 'take_home',
    drug_class: 'Antiemetic',
  },
};

// Quick combination templates
export const COMBINATION_TEMPLATES = {
  'aza_only': {
    name: 'Azacitidine Monotherapy',
    description: 'Single agent for AML/MDS',
    drugs: ['azacitidine'],
  },
  'ven_only': {
    name: 'Venetoclax Monotherapy',
    description: 'Single agent for CLL',
    drugs: ['venetoclax'],
  },
  'aza_ven': {
    name: 'Azacitidine + Venetoclax',
    description: 'Standard for elderly AML',
    drugs: ['azacitidine', 'venetoclax'],
  },
  'aza_ven_gilt': {
    name: 'Aza + Ven + Gilteritinib',
    description: 'FLT3+ AML triplet therapy',
    drugs: ['azacitidine', 'venetoclax', 'gilteritinib'],
  },
  'rchop': {
    name: 'R-CHOP',
    description: 'Standard for lymphoma',
    drugs: ['rituximab', 'cyclophosphamide', 'doxorubicin', 'vincristine', 'prednisone'],
  },
  'cytarabine_7_3': {
    name: '7+3 Induction',
    description: 'Intensive AML induction',
    drugs: ['cytarabine', 'doxorubicin'],
  },
};

// Get all drugs as array
export const getAllDrugs = () => Object.values(DRUG_LIBRARY);

// Get drugs by category
export const getDrugsByCategory = (category) => {
  return Object.values(DRUG_LIBRARY).filter(drug => drug.category === category);
};

// Get drug by ID
export const getDrugById = (drugId) => {
  return DRUG_LIBRARY[drugId];
};

// Get combination template
export const getCombinationTemplate = (templateId) => {
  return COMBINATION_TEMPLATES[templateId];
};

// Get all combination templates
export const getAllCombinations = () => Object.entries(COMBINATION_TEMPLATES).map(([id, combo]) => ({
  id,
  ...combo,
}));
