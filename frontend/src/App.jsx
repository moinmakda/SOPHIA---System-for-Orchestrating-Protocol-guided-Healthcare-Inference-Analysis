import React, { useState, useEffect } from 'react';
import { ProtocolBrowser } from './components/ProtocolBrowser';
import { PatientForm } from './components/PatientForm';
import { DrugSelector } from './components/DrugSelector';
import { FlexibleProtocolBuilder } from './components/FlexibleProtocolBuilder';
import { ProtocolDisplay } from './components/ProtocolDisplay';
import { AdminPanel } from './components/AdminPanel';
import { api } from './utils/api';
import './App.css';

function App() {
  // State
  const [protocols, setProtocols] = useState([]);
  const [selectedProtocol, setSelectedProtocol] = useState(null);
  const [protocolDetails, setProtocolDetails] = useState(null);
  const [patientData, setPatientData] = useState({
    age_years: '',
    sex: '',
    weight_kg: '',
    height_cm: '',
    performance_status: '',
    neutrophils: '',
    platelets: '',
    hemoglobin: '',
    serum_creatinine: '',
    creatinine_clearance: '',
    bilirubin: '',
    ast: '',
    // Extended fields
    histology: '',
    disease_stage: '',
    ldh: '',
    urate: '',
    calcium: '',
    beta2_microglobulin: '',
    hep_b_surface_antigen: '',
    hep_b_core_antibody: '',
    hep_c_antibody: '',
    hiv_status: '',
    ebv_status: '',
    cmv_status: '',
    vzv_status: '',
    g6pd_status: '',
    lvef_percent: '',
    prior_anthracycline_dose_mg_m2: '',
    prior_bleomycin_units: '',
    prior_cardiac_history: false,
    prior_mediastinal_radiation: false,
    known_allergies: [],
  });
  const [cycleNumber, setCycleNumber] = useState(1);
  const [excludedDrugs, setExcludedDrugs] = useState([]);
  const [includePremeds, setIncludePremeds] = useState(true);
  const [includeTakeHome, setIncludeTakeHome] = useState(true);
  const [includeRescue, setIncludeRescue] = useState(true);
  const [generatedProtocol, setGeneratedProtocol] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [step, setStep] = useState(1); // 1: Select Protocol, 2: Patient Data, 3: Drug Selection, 4: Review
  const [useFlexibleBuilder, setUseFlexibleBuilder] = useState(false);
  const [customDrugSelection, setCustomDrugSelection] = useState(null);
  const [showAdmin, setShowAdmin] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(null);

  // Load protocols on mount and when search/category changes
  useEffect(() => {
    loadProtocols(searchTerm || null, selectedCategory);
  }, [searchTerm, selectedCategory]);

  // Load protocol details when selected
  useEffect(() => {
    if (selectedProtocol) {
      loadProtocolDetails(selectedProtocol.code);
    }
  }, [selectedProtocol]);

  const loadProtocols = async (search = null, category = null) => {
    try {
      const data = await api.getProtocols(search, category);
      setProtocols(data);
    } catch (err) {
      setError('Failed to load protocols');
    }
  };

  const loadProtocolDetails = async (code) => {
    try {
      const data = await api.getProtocol(code);
      setProtocolDetails(data);
      setExcludedDrugs([]);
      // Check if this protocol supports flexible combinations
      if (data.supports_flexible_combinations || data.combination_options) {
        setUseFlexibleBuilder(true);
      } else {
        setUseFlexibleBuilder(false);
      }
    } catch (err) {
      setError('Failed to load protocol details');
    }
  };

  const handleProtocolSelect = (protocol) => {
    setSelectedProtocol(protocol);
    setGeneratedProtocol(null);
    setStep(2);
  };

  const handlePatientDataChange = (field, value) => {
    setPatientData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleDrugToggle = (drugName) => {
    setExcludedDrugs(prev => {
      if (prev.includes(drugName)) {
        return prev.filter(d => d !== drugName);
      } else {
        return [...prev, drugName];
      }
    });
  };

  const handleFlexibleBuilderSave = (selectedDrugs) => {
    setCustomDrugSelection(selectedDrugs);
    console.log('Custom drug selection saved:', selectedDrugs);
  };

  const buildPatientPayload = () => {
    const p = {
      weight_kg: parseFloat(patientData.weight_kg),
      height_cm: parseFloat(patientData.height_cm),
      age_years: parseInt(patientData.age_years),
      performance_status: parseInt(patientData.performance_status),
      neutrophils: parseFloat(patientData.neutrophils),
      platelets: parseFloat(patientData.platelets),
      hemoglobin: parseFloat(patientData.hemoglobin),
      creatinine_clearance: parseFloat(patientData.creatinine_clearance),
      bilirubin: parseFloat(patientData.bilirubin),
      known_allergies: patientData.known_allergies || [],
      prior_cardiac_history: patientData.prior_cardiac_history || false,
      prior_mediastinal_radiation: patientData.prior_mediastinal_radiation || false,
    };
    // Optional numeric fields
    const numFields = [
      'ast', 'alt', 'ldh', 'urate', 'calcium', 'beta2_microglobulin',
      'lvef_percent', 'prior_anthracycline_dose_mg_m2', 'prior_bleomycin_units',
    ];
    numFields.forEach(f => {
      if (patientData[f] !== '' && patientData[f] != null) {
        p[f] = parseFloat(patientData[f]);
      }
    });
    // Optional string fields
    const strFields = [
      'histology', 'disease_stage',
      'hep_b_surface_antigen', 'hep_b_core_antibody', 'hep_c_antibody',
      'hiv_status', 'ebv_status', 'cmv_status', 'vzv_status', 'g6pd_status',
    ];
    strFields.forEach(f => {
      if (patientData[f]) p[f] = patientData[f];
    });
    return p;
  };

  const generateProtocol = async () => {
    setLoading(true);
    setError(null);

    try {
      const patient = buildPatientPayload();

      // Custom regimen path — user built drugs in FlexibleProtocolBuilder
      if (!selectedProtocol || useFlexibleBuilder) {
        if (!customDrugSelection || customDrugSelection.length === 0) {
          setError('Please add at least one drug to your custom regimen before generating.');
          setLoading(false);
          return;
        }

        const drugs = customDrugSelection.map(d => ({
          drug_name: d.drug_name,
          dose: parseFloat(d.dose) || 0,
          dose_unit: d.dose_unit || 'mg/m²',
          route: d.route || 'IV infusion',
          days: d.days || [1],
          duration_minutes: d.duration_minutes || null,
          diluent: d.diluent || null,
          diluent_volume_ml: d.diluent_volume_ml || null,
          frequency: d.frequency || null,
          special_instructions: d.special_instructions || null,
          max_dose: d.max_dose || null,
          prn: d.prn || false,
        }));

        const request = {
          patient,
          drugs,
          regimen_name: customDrugSelection.map(d => d.drug_name).join(' + '),
          cycle_number: cycleNumber,
          cycle_length_days: 28,
          total_cycles: 6,
        };

        const result = await api.generateCustomRegimen(request);
        setGeneratedProtocol(result);
        setStep(4);
        return;
      }

      // Standard protocol path
      const request = {
        protocol_code: selectedProtocol.code,
        patient,
        cycle_number: cycleNumber,
        excluded_drugs: excludedDrugs,
        include_premeds: includePremeds,
        include_antiemetics: true,
        include_take_home: includeTakeHome,
        include_rescue: includeRescue
      };

      const result = await api.generateProtocol(request);
      setGeneratedProtocol(result);
      setStep(4);
    } catch (err) {
      setError(err.message || 'Failed to generate protocol');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setSelectedProtocol(null);
    setProtocolDetails(null);
    setPatientData({
      age_years: '',
      sex: '',
      weight_kg: '',
      height_cm: '',
      performance_status: '',
      neutrophils: '',
      platelets: '',
      hemoglobin: '',
      serum_creatinine: '',
      creatinine_clearance: '',
      bilirubin: '',
      ast: '',
      histology: '',
      disease_stage: '',
      ldh: '',
      urate: '',
      calcium: '',
      beta2_microglobulin: '',
      hep_b_surface_antigen: '',
      hep_b_core_antibody: '',
      hep_c_antibody: '',
      hiv_status: '',
      ebv_status: '',
      cmv_status: '',
      vzv_status: '',
      g6pd_status: '',
      lvef_percent: '',
      prior_anthracycline_dose_mg_m2: '',
      prior_bleomycin_units: '',
      prior_cardiac_history: false,
      prior_mediastinal_radiation: false,
      known_allergies: [],
    });
    setCycleNumber(1);
    setExcludedDrugs([]);
    setGeneratedProtocol(null);
    setStep(1);
    setUseFlexibleBuilder(false);
    setCustomDrugSelection(null);
  };

  const canProceedFromPatient = () => {
    return (
      patientData.age_years &&
      patientData.sex &&
      patientData.weight_kg &&
      patientData.height_cm &&
      patientData.performance_status !== '' &&
      patientData.neutrophils &&
      patientData.platelets &&
      patientData.hemoglobin &&
      patientData.creatinine_clearance &&
      patientData.bilirubin
    );
  };

  return (
    <div className="app">
      <Header onReset={resetForm} onAdminOpen={() => setShowAdmin(true)} />
      
      <main className="main-content">
        {error && (
          <div className="error-banner">
            <span>{error}</span>
            <button onClick={() => setError(null)}>×</button>
          </div>
        )}

        {/* Progress Steps */}
        <div className="progress-steps">
          <div className={`step ${step >= 1 ? 'active' : ''} ${step > 1 ? 'completed' : ''}`}>
            <span className="step-number">1</span>
            <span className="step-label">Protocol</span>
          </div>
          <div className={`step ${step >= 2 ? 'active' : ''} ${step > 2 ? 'completed' : ''}`}>
            <span className="step-number">2</span>
            <span className="step-label">Patient</span>
          </div>
          <div className={`step ${step >= 3 ? 'active' : ''} ${step > 3 ? 'completed' : ''}`}>
            <span className="step-number">3</span>
            <span className="step-label">Drugs</span>
          </div>
          <div className={`step ${step >= 4 ? 'active' : ''}`}>
            <span className="step-number">4</span>
            <span className="step-label">Review</span>
          </div>
        </div>

        {/* Step 1: Protocol Selection */}
        {step === 1 && (
          <>
            <div className="protocol-selection-header">
              <h2>Choose Your Workflow</h2>
              <p>Select an existing protocol or build your own custom regimen</p>
            </div>

            <div className="workflow-options">
              <button
                className="workflow-card"
                onClick={() => {
                  setSelectedProtocol(null);
                  setUseFlexibleBuilder(true);
                  setStep(2);
                }}
              >
                <div className="workflow-icon">🔧</div>
                <h3>Build Custom Regimen</h3>
                <p>Start from scratch with flexible drug selection (Aza, Ven, combinations, etc.)</p>
                <span className="workflow-badge">New</span>
              </button>

              <button
                className="workflow-card"
                onClick={() => {
                  setUseFlexibleBuilder(false);
                }}
              >
                <div className="workflow-icon">📋</div>
                <h3>Use Standard Protocol</h3>
                <p>Select from pre-defined chemotherapy protocols</p>
              </button>
            </div>

            {!useFlexibleBuilder && (
              <ProtocolBrowser
                protocols={protocols}
                onSelect={handleProtocolSelect}
                selectedProtocol={selectedProtocol}
              />
            )}
          </>
        )}

        {/* Step 2: Patient Data */}
        {step === 2 && (
          <div className="step-content">
            {selectedProtocol ? (
              <div className="selected-protocol-banner">
                <h3>Selected: {selectedProtocol?.name}</h3>
                <p>{selectedProtocol?.indication}</p>
              </div>
            ) : (
              <div className="selected-protocol-banner custom-regimen">
                <h3>🔧 Custom Regimen Builder</h3>
                <p>Building from scratch - You'll select drugs in the next step</p>
              </div>
            )}
            
            <PatientForm
              patientData={patientData}
              onChange={handlePatientDataChange}
              cycleNumber={cycleNumber}
              onCycleChange={setCycleNumber}
              totalCycles={protocolDetails?.total_cycles || 6}
              requiredFields={protocolDetails?.required_patient_fields || {}}
            />
            
            <div className="step-actions">
              <button className="btn-secondary" onClick={() => setStep(1)}>
                ← Back
              </button>
              <button 
                className="btn-primary" 
                onClick={() => setStep(3)}
                disabled={!canProceedFromPatient()}
              >
                Next: Drug Selection →
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Drug Selection */}
        {step === 3 && (
          <div className="step-content">
            {/* Only show toggle if protocol is selected */}
            {protocolDetails && (
              <div className="mode-toggle-container">
                <label className="mode-toggle">
                  <input
                    type="checkbox"
                    checked={useFlexibleBuilder}
                    onChange={(e) => setUseFlexibleBuilder(e.target.checked)}
                  />
                  <span className="mode-toggle-slider"></span>
                  <span className="mode-toggle-label">
                    {useFlexibleBuilder ? '🔧 Flexible Drug Builder' : '📋 Simple Drug Selection'}
                  </span>
                </label>
              </div>
            )}

            {/* Custom regimen mode OR flexible builder mode */}
            {!selectedProtocol || useFlexibleBuilder ? (
              <FlexibleProtocolBuilder
                protocol={protocolDetails}
                onSave={handleFlexibleBuilderSave}
                patientBSA={patientData.height_cm && patientData.weight_kg
                  ? Math.sqrt((parseFloat(patientData.height_cm) * parseFloat(patientData.weight_kg)) / 3600)
                  : null}
              />
            ) : (
              <DrugSelector
                protocol={protocolDetails}
                excludedDrugs={excludedDrugs}
                onDrugToggle={handleDrugToggle}
                includePremeds={includePremeds}
                onPremedsChange={setIncludePremeds}
                includeTakeHome={includeTakeHome}
                onTakeHomeChange={setIncludeTakeHome}
                includeRescue={includeRescue}
                onRescueChange={setIncludeRescue}
              />
            )}
            
            {(!selectedProtocol || useFlexibleBuilder) && customDrugSelection && customDrugSelection.length > 0 && (
              <div className="custom-regimen-summary" style={{
                background: '#e8f5e9', border: '1px solid #4caf50', padding: '10px 15px',
                borderRadius: '4px', margin: '10px 0', fontSize: '14px'
              }}>
                <strong>Regimen ready:</strong> {customDrugSelection.map(d => d.drug_name).join(' + ')}
                <span style={{ marginLeft: 8, color: '#666' }}>({customDrugSelection.length} drug{customDrugSelection.length > 1 ? 's' : ''})</span>
              </div>
            )}
            {(!selectedProtocol || useFlexibleBuilder) && (!customDrugSelection || customDrugSelection.length === 0) && (
              <div style={{
                background: '#fff3cd', border: '1px solid #ffc107', padding: '10px 15px',
                borderRadius: '4px', margin: '10px 0', fontSize: '14px'
              }}>
                Add at least one drug to your regimen above before generating.
              </div>
            )}
            <div className="step-actions">
              <button className="btn-secondary" onClick={() => setStep(2)}>
                ← Back
              </button>
              <button
                className="btn-primary"
                onClick={generateProtocol}
                disabled={loading || ((!selectedProtocol || useFlexibleBuilder) && (!customDrugSelection || customDrugSelection.length === 0))}
              >
                {loading ? 'Generating...' : 'Generate Protocol →'}
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Review Generated Protocol */}
        {step === 4 && generatedProtocol && (
          <div className="step-content">
            <ProtocolDisplay 
              protocol={generatedProtocol}
              onBack={() => setStep(3)}
              onReset={resetForm}
            />
          </div>
        )}
      </main>

      {showAdmin && (
        <AdminPanel
          onClose={() => setShowAdmin(false)}
          onProtocolIngested={() => loadProtocols(searchTerm || null, selectedCategory)}
        />
      )}
    </div>
  );
}

export default App;
