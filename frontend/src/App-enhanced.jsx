import React, { useState, useEffect } from 'react';
import { ProtocolBrowser } from './components/ProtocolBrowser';
import { PatientForm } from './components/PatientForm';
import { DrugSelector } from './components/DrugSelector';
import { ProtocolDisplay } from './components/ProtocolDisplay';
import { Header } from './components/Header';
import { AdminPanel } from './components/AdminPanel';
import { api } from './utils/api';
import './App.css';

function App() {
  // State
  const [protocols, setProtocols] = useState([]);
  const [selectedProtocol, setSelectedProtocol] = useState(null);
  const [protocolDetails, setProtocolDetails] = useState(null);
  const [patientData, setPatientData] = useState({
    weight_kg: '',
    height_cm: '',
    neutrophils: '',
    platelets: '',
    bilirubin: '',
    creatinine_clearance: '',
    ast: '',
    alt: '',
    hemoglobin: ''
  });
  const [cycleNumber, setCycleNumber] = useState(1);
  const [excludedDrugs, setExcludedDrugs] = useState([]);
  const [includePremeds, setIncludePremeds] = useState(true);
  const [includeTakeHome, setIncludeTakeHome] = useState(true);
  const [includeRescue, setIncludeRescue] = useState(true);
  const [generatedProtocol, setGeneratedProtocol] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [step, setStep] = useState(1);
  const [showAdmin, setShowAdmin] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState(null);

  // Load protocols on mount
  useEffect(() => {
    loadProtocols();
  }, []);

  // Reload protocols when search/category changes
  useEffect(() => {
    loadProtocols(searchTerm, selectedCategory);
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
      setError('Failed to load protocols: ' + err.message);
    }
  };

  const loadProtocolDetails = async (code) => {
    try {
      const data = await api.getProtocol(code);
      setProtocolDetails(data);
      setExcludedDrugs([]);
    } catch (err) {
      setError('Failed to load protocol details: ' + err.message);
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

  const generateProtocol = async () => {
    setLoading(true);
    setError(null);

    try {
      const patient = {
        weight_kg: parseFloat(patientData.weight_kg),
        height_cm: parseFloat(patientData.height_cm)
      };

      // Add optional lab values
      if (patientData.neutrophils) patient.neutrophils = parseFloat(patientData.neutrophils);
      if (patientData.platelets) patient.platelets = parseFloat(patientData.platelets);
      if (patientData.bilirubin) patient.bilirubin = parseFloat(patientData.bilirubin);
      if (patientData.creatinine_clearance) patient.creatinine_clearance = parseFloat(patientData.creatinine_clearance);
      if (patientData.ast) patient.ast = parseFloat(patientData.ast);
      if (patientData.alt) patient.alt = parseFloat(patientData.alt);
      if (patientData.hemoglobin) patient.hemoglobin = parseFloat(patientData.hemoglobin);

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
      weight_kg: '',
      height_cm: '',
      neutrophils: '',
      platelets: '',
      bilirubin: '',
      creatinine_clearance: '',
      ast: '',
      alt: '',
      hemoglobin: ''
    });
    setCycleNumber(1);
    setExcludedDrugs([]);
    setGeneratedProtocol(null);
    setStep(1);
  };

  const canProceedFromPatient = () => {
    return patientData.weight_kg && patientData.height_cm;
  };

  const handleProtocolIngested = () => {
    // Reload protocols when a new one is ingested
    loadProtocols();
  };

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="logo" onClick={resetForm}>
            <img 
              src="/src/assets/logo.png" 
              alt="SOPHIA Logo" 
              style={{ width: '64px', height: '64px', objectFit: 'contain', marginRight: '12px' }}
            />
            <div className="logo-text">
              <h1>SOPHIA</h1>
              <span className="subtitle">System for Orchestrating Protocol-guided Healthcare Inference & Analysis</span>
            </div>
          </div>
          
          <nav className="header-nav">
            <img 
              src="/src/assets/JIVANA_WHITE.png" 
              alt="Jivana AI" 
              style={{ height: '48px', marginRight: '24px', objectFit: 'contain' }}
            />
            <button className="nav-btn" onClick={resetForm}>
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z"/>
              </svg>
              New Protocol
            </button>
            <button className="nav-btn admin-btn" onClick={() => setShowAdmin(true)}>
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
              </svg>
              Admin
            </button>
          </nav>
        </div>
      </header>
      
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
          <ProtocolBrowser
            protocols={protocols}
            onSelect={handleProtocolSelect}
            selectedProtocol={selectedProtocol}
          />
        )}

        {/* Step 2: Patient Data */}
        {step === 2 && (
          <div className="step-content">
            <div className="selected-protocol-banner">
              <h3>Selected: {selectedProtocol?.name}</h3>
              <p>{selectedProtocol?.indication}</p>
            </div>
            
            <PatientForm
              patientData={patientData}
              onChange={handlePatientDataChange}
              cycleNumber={cycleNumber}
              onCycleChange={setCycleNumber}
              totalCycles={protocolDetails?.total_cycles || 6}
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
        {step === 3 && protocolDetails && (
          <div className="step-content">
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
            
            <div className="step-actions">
              <button className="btn-secondary" onClick={() => setStep(2)}>
                ← Back
              </button>
              <button 
                className="btn-primary" 
                onClick={generateProtocol}
                disabled={loading}
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

      {/* Admin Panel Modal */}
      {showAdmin && (
        <AdminPanel 
          onClose={() => setShowAdmin(false)}
          onProtocolIngested={handleProtocolIngested}
        />
      )}
    </div>
  );
}

export default App;
