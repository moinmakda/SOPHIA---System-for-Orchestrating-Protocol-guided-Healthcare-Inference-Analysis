import React, { useMemo, useState } from 'react';

const BSA_CAP = 2.0;

export function PatientForm({ patientData, onChange, cycleNumber, onCycleChange, totalCycles, requiredFields = {} }) {

  const [showAllergyInput, setShowAllergyInput] = useState(false);
  const [newAllergy, setNewAllergy] = useState('');
  const [useManualCrCl, setUseManualCrCl] = useState(false);

  // Calculate BSA when height and weight are available
  const calculatedBSA = useMemo(() => {
    if (patientData.weight_kg && patientData.height_cm) {
      const w = parseFloat(patientData.weight_kg);
      const h = parseFloat(patientData.height_cm);
      if (w > 0 && h > 0) {
        return Math.sqrt((h * w) / 3600).toFixed(2);
      }
    }
    return null;
  }, [patientData.weight_kg, patientData.height_cm]);

  // Calculate Creatinine Clearance using Cockcroft-Gault equation
  const calculatedCrCl = useMemo(() => {
    if (patientData.weight_kg && patientData.age_years && patientData.serum_creatinine) {
      const weight = parseFloat(patientData.weight_kg);
      const age = parseFloat(patientData.age_years);
      const screat = parseFloat(patientData.serum_creatinine);
      const isFemale = patientData.sex === 'female';

      if (weight > 0 && age > 0 && screat > 0) {
        // Cockcroft-Gault: CrCl = ((140 - age) × weight) / (72 × SCr) [× 0.85 if female]
        let crcl = ((140 - age) * weight) / (72 * screat);
        if (isFemale) {
          crcl = crcl * 0.85;
        }
        return Math.round(crcl);
      }
    }
    return null;
  }, [patientData.weight_kg, patientData.age_years, patientData.serum_creatinine, patientData.sex]);

  // Auto-update creatinine clearance when calculated
  React.useEffect(() => {
    if (calculatedCrCl !== null && !useManualCrCl) {
      onChange('creatinine_clearance', calculatedCrCl.toString());
    }
  }, [calculatedCrCl, useManualCrCl, onChange]);
  
  // Check if BSA would be capped
  const bsaWouldBeCapped = calculatedBSA && parseFloat(calculatedBSA) > BSA_CAP;
  const cappedBSA = bsaWouldBeCapped ? BSA_CAP.toFixed(2) : calculatedBSA;

  const cycleOptions = Array.from({ length: totalCycles }, (_, i) => i + 1);

  // Helper: is this field required by the current protocol?
  const isRequired = (fieldName) => fieldName in requiredFields;
  const requiredReason = (fieldName) => requiredFields[fieldName] || '';

  const requiredFieldKeys = Object.keys(requiredFields);
  
  const addAllergy = () => {
    if (newAllergy.trim()) {
      const current = patientData.known_allergies || [];
      onChange('known_allergies', [...current, newAllergy.trim()]);
      setNewAllergy('');
      setShowAllergyInput(false);
    }
  };
  
  const removeAllergy = (index) => {
    const current = patientData.known_allergies || [];
    onChange('known_allergies', current.filter((_, i) => i !== index));
  };

  return (
    <div className="patient-form">
      <h2>Patient Information</h2>
      
      {/* Safety Notice */}
      <div className="safety-notice">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="#e74c3c">
          <path d="M12 2L1 21h22L12 2zm0 3.99L19.53 19H4.47L12 5.99zM11 10v4h2v-4h-2zm0 6v2h2v-2h-2z"/>
        </svg>
        <div>
          <strong>Clinical Decision Support Only</strong>
          <p>All lab values are <strong>mandatory</strong>. SOPHIA will validate values against safety thresholds.
          Independent prescriber and pharmacist verification is required.</p>
        </div>
      </div>

      {/* Protocol-specific required workup */}
      {requiredFieldKeys.length > 0 && (
        <div style={{
          background: '#e3f2fd', border: '1px solid #1976d2', borderRadius: 4,
          padding: '12px 16px', marginBottom: 16
        }}>
          <strong style={{ color: '#1565c0' }}>Required workup for this protocol:</strong>
          <ul style={{ margin: '8px 0 0 0', paddingLeft: 18, fontSize: 13 }}>
            {requiredFieldKeys.map(field => (
              <li key={field} style={{ marginBottom: 4 }}>
                <code style={{ background: '#bbdefb', padding: '1px 4px', borderRadius: 2 }}>{field}</code>
                {' — '}{requiredFields[field]}
              </li>
            ))}
          </ul>
        </div>
      )}
      
      <div className="form-section">
        <h3>
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
          Required Information
        </h3>
        
        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="age">Age (years) *</label>
            <input
              id="age"
              type="number"
              step="1"
              min="0"
              max="120"
              value={patientData.age_years || ''}
              onChange={(e) => onChange('age_years', e.target.value)}
              placeholder="e.g., 55"
              required
              className={patientData.age_years > 70 ? 'warning-input' : ''}
            />
            {patientData.age_years > 70 && (
              <span className="field-warning">Consider dose reduction for elderly patients</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="sex">Sex *</label>
            <select
              id="sex"
              value={patientData.sex || ''}
              onChange={(e) => onChange('sex', e.target.value)}
              required
            >
              <option value="">Select...</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="weight">Weight (kg) *</label>
            <input
              id="weight"
              type="number"
              step="0.1"
              min="0"
              value={patientData.weight_kg}
              onChange={(e) => onChange('weight_kg', e.target.value)}
              placeholder="e.g., 70"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="height">Height (cm) *</label>
            <input
              id="height"
              type="number"
              step="0.1"
              min="0"
              value={patientData.height_cm}
              onChange={(e) => onChange('height_cm', e.target.value)}
              placeholder="e.g., 175"
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="performance_status">ECOG Performance Status *</label>
            <select
              id="performance_status"
              value={patientData.performance_status ?? ''}
              onChange={(e) => onChange('performance_status', parseInt(e.target.value))}
              required
              className={patientData.performance_status >= 3 ? 'critical-input' : ''}
            >
              <option value="">Select status...</option>
              <option value="0">0 - Fully active</option>
              <option value="1">1 - Restricted strenuous activity</option>
              <option value="2">2 - Ambulatory, capable of self-care</option>
              <option value="3">3 - Limited self-care, bed/chair &gt;50%</option>
              <option value="4">4 - Completely disabled</option>
            </select>
            {patientData.performance_status >= 3 && (
              <span className="field-critical">Full-dose chemotherapy may not be appropriate</span>
            )}
          </div>
          
          <div className="form-group">
            <label htmlFor="cycle">Cycle Number</label>
            <select
              id="cycle"
              value={cycleNumber}
              onChange={(e) => onCycleChange(parseInt(e.target.value))}
            >
              {cycleOptions.map(n => (
                <option key={n} value={n}>Cycle {n} of {totalCycles}</option>
              ))}
            </select>
          </div>
          
          <div className="form-group calculated-bsa">
            <label>BSA (for dosing)</label>
            <div className={`bsa-display ${bsaWouldBeCapped ? 'bsa-capped' : ''}`}>
              {calculatedBSA ? (
                <>
                  <span className="bsa-value">{cappedBSA}</span>
                  <span className="bsa-unit">m²</span>
                  {bsaWouldBeCapped && (
                    <span className="bsa-cap-notice" title="Per ASCO guidelines for obese patients">
                      (capped from {calculatedBSA})
                    </span>
                  )}
                </>
              ) : (
                <span className="bsa-placeholder">Enter height & weight</span>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Allergies Section */}
      <div className="form-section allergy-section">
        <h3>
          <svg viewBox="0 0 24 24" width="20" height="20" fill="#e74c3c">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
          </svg>
          Known Drug Allergies
        </h3>
        
        <div className="allergy-list">
          {(patientData.known_allergies || []).map((allergy, index) => (
            <span key={index} className="allergy-tag">
              {allergy}
              <button onClick={() => removeAllergy(index)} title="Remove">×</button>
            </span>
          ))}
          
          {showAllergyInput ? (
            <div className="allergy-input-group">
              <input
                type="text"
                value={newAllergy}
                onChange={(e) => setNewAllergy(e.target.value)}
                placeholder="e.g., platinum, rituximab"
                onKeyDown={(e) => e.key === 'Enter' && addAllergy()}
              />
              <button onClick={addAllergy} className="btn-small">Add</button>
              <button onClick={() => setShowAllergyInput(false)} className="btn-small btn-cancel">Cancel</button>
            </div>
          ) : (
            <button onClick={() => setShowAllergyInput(true)} className="btn-add-allergy">
              + Add Allergy
            </button>
          )}
        </div>
      </div>

      <div className="form-section">
        <h3>
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/>
          </svg>
          Lab Values (MANDATORY for dose modifications)
        </h3>
        <p className="section-hint critical-hint">⚠️ All lab values are required per "No labs, no chemo" principle</p>
        
        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="neutrophils">
              Neutrophils (×10⁹/L) *
              <span className="normal-range">Normal: 2.0-7.5</span>
            </label>
            <input
              id="neutrophils"
              type="number"
              step="0.1"
              min="0"
              value={patientData.neutrophils}
              onChange={(e) => onChange('neutrophils', e.target.value)}
              placeholder="e.g., 2.5"
              required
              className={patientData.neutrophils && patientData.neutrophils < 1 ? 'critical-input' : 
                         patientData.neutrophils && patientData.neutrophils < 0.5 ? 'danger-input' : ''}
            />
            {patientData.neutrophils && patientData.neutrophils < 0.5 && (
              <span className="field-critical">TREATMENT CONTRAINDICATED: Severe neutropenia</span>
            )}
            {patientData.neutrophils && patientData.neutrophils >= 0.5 && patientData.neutrophils < 1 && (
              <span className="field-warning">Consider treatment delay</span>
            )}
          </div>
          
          <div className="form-group">
            <label htmlFor="platelets">
              Platelets (×10⁹/L) *
              <span className="normal-range">Normal: 150-400</span>
            </label>
            <input
              id="platelets"
              type="number"
              step="1"
              min="0"
              value={patientData.platelets}
              onChange={(e) => onChange('platelets', e.target.value)}
              placeholder="e.g., 200"
              required
              className={patientData.platelets && patientData.platelets < 50 ? 'danger-input' : 
                         patientData.platelets && patientData.platelets < 100 ? 'critical-input' : ''}
            />
            {patientData.platelets && patientData.platelets < 50 && (
              <span className="field-critical">TREATMENT CONTRAINDICATED: Severe thrombocytopenia</span>
            )}
            {patientData.platelets && patientData.platelets >= 50 && patientData.platelets < 100 && (
              <span className="field-warning">Consider treatment delay</span>
            )}
          </div>
          
          <div className="form-group">
            <label htmlFor="hemoglobin">
              Hemoglobin (g/dL) *
              <span className="normal-range">Normal: 12-17</span>
            </label>
            <input
              id="hemoglobin"
              type="number"
              step="0.1"
              min="0"
              value={patientData.hemoglobin}
              onChange={(e) => onChange('hemoglobin', e.target.value)}
              placeholder="e.g., 14"
              required
              className={patientData.hemoglobin && patientData.hemoglobin < 8 ? 'warning-input' : ''}
            />
            {patientData.hemoglobin && patientData.hemoglobin < 8 && (
              <span className="field-warning">Consider blood transfusion</span>
            )}
          </div>
          
          <div className="form-group">
            <label htmlFor="serum_creatinine">
              Serum Creatinine (mg/dL) *
              <span className="normal-range">Normal: 0.6-1.2</span>
            </label>
            <input
              id="serum_creatinine"
              type="number"
              step="0.01"
              min="0"
              value={patientData.serum_creatinine || ''}
              onChange={(e) => onChange('serum_creatinine', e.target.value)}
              placeholder="e.g., 1.0"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="crcl">
              Creatinine Clearance (ml/min) *
              <span className="normal-range">Normal: &gt;90</span>
            </label>
            <div className="input-with-toggle">
              <input
                id="crcl"
                type="number"
                step="1"
                min="0"
                value={patientData.creatinine_clearance || ''}
                onChange={(e) => {
                  setUseManualCrCl(true);
                  onChange('creatinine_clearance', e.target.value);
                }}
                placeholder={calculatedCrCl ? `Auto: ${calculatedCrCl}` : "Enter value or auto-calc"}
                required
                className={patientData.creatinine_clearance && patientData.creatinine_clearance < 10 ? 'danger-input' :
                           patientData.creatinine_clearance && patientData.creatinine_clearance < 30 ? 'critical-input' : ''}
                disabled={!useManualCrCl && calculatedCrCl}
              />
              {calculatedCrCl && (
                <button
                  type="button"
                  className="btn-toggle-auto"
                  onClick={() => setUseManualCrCl(!useManualCrCl)}
                  title={useManualCrCl ? "Use auto-calculated value" : "Enter manually"}
                >
                  {useManualCrCl ? "🔄 Auto" : "✏️ Manual"}
                </button>
              )}
            </div>
            {calculatedCrCl && !useManualCrCl && (
              <span className="field-info">Auto-calculated using Cockcroft-Gault equation</span>
            )}
            {patientData.creatinine_clearance && patientData.creatinine_clearance < 10 && (
              <span className="field-critical">TREATMENT CONTRAINDICATED: Severe renal failure</span>
            )}
            {patientData.creatinine_clearance && patientData.creatinine_clearance >= 10 && patientData.creatinine_clearance < 30 && (
              <span className="field-warning">Severe renal impairment - review nephrotoxic drugs</span>
            )}
          </div>
          
          <div className="form-group">
            <label htmlFor="bilirubin">
              Bilirubin (µmol/L) *
              <span className="normal-range">Normal: &lt;21</span>
            </label>
            <input
              id="bilirubin"
              type="number"
              step="1"
              min="0"
              value={patientData.bilirubin}
              onChange={(e) => onChange('bilirubin', e.target.value)}
              placeholder="e.g., 15"
              required
              className={patientData.bilirubin && patientData.bilirubin > 85 ? 'danger-input' : 
                         patientData.bilirubin && patientData.bilirubin > 30 ? 'warning-input' : ''}
            />
            {patientData.bilirubin && patientData.bilirubin > 85 && (
              <span className="field-critical">Doxorubicin will be omitted</span>
            )}
            {patientData.bilirubin && patientData.bilirubin > 30 && patientData.bilirubin <= 85 && (
              <span className="field-warning">Hepatic dose modifications will apply</span>
            )}
          </div>
          
          <div className="form-group">
            <label htmlFor="ast">
              AST (U/L)
              <span className="normal-range">Normal: 10-40</span>
            </label>
            <input
              id="ast"
              type="number"
              step="1"
              min="0"
              value={patientData.ast}
              onChange={(e) => onChange('ast', e.target.value)}
              placeholder="e.g., 25"
            />
          </div>
        </div>
      </div>
      
      {/* Disease Characterisation */}
      <div className="form-section">
        <h3>Disease Characterisation</h3>
        <p className="section-hint">Clinical context — used for dose modification decisions and warnings</p>
        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="histology">Histology / Diagnosis</label>
            <input
              id="histology"
              type="text"
              value={patientData.histology || ''}
              onChange={(e) => onChange('histology', e.target.value)}
              placeholder="e.g., DLBCL, AML M4, CLL"
            />
          </div>
          <div className="form-group">
            <label htmlFor="disease_stage">Disease Stage</label>
            <input
              id="disease_stage"
              type="text"
              value={patientData.disease_stage || ''}
              onChange={(e) => onChange('disease_stage', e.target.value)}
              placeholder="e.g., Ann Arbor IV, Binet B"
            />
          </div>
          <div className="form-group">
            <label htmlFor="ldh">
              LDH (U/L)
              <span className="normal-range">Normal: &lt;250</span>
            </label>
            <input
              id="ldh"
              type="number"
              step="1"
              min="0"
              value={patientData.ldh || ''}
              onChange={(e) => onChange('ldh', e.target.value)}
              placeholder="e.g., 350"
              className={patientData.ldh > 500 ? 'warning-input' : ''}
            />
            {patientData.ldh > 500 && <span className="field-warning">Elevated — TLS risk assessment required</span>}
          </div>
          <div className="form-group">
            <label htmlFor="beta2_microglobulin">
              β2-Microglobulin (mg/L)
              <span className="normal-range">Normal: &lt;2.4</span>
            </label>
            <input
              id="beta2_microglobulin"
              type="number"
              step="0.1"
              min="0"
              value={patientData.beta2_microglobulin || ''}
              onChange={(e) => onChange('beta2_microglobulin', e.target.value)}
              placeholder="e.g., 3.5"
            />
          </div>
          <div className="form-group">
            <label htmlFor="urate">
              Serum Urate (µmol/L)
              <span className="normal-range">Normal: 200–420</span>
            </label>
            <input
              id="urate"
              type="number"
              step="1"
              min="0"
              value={patientData.urate || ''}
              onChange={(e) => onChange('urate', e.target.value)}
              placeholder="e.g., 350"
              className={patientData.urate > 480 ? 'warning-input' : ''}
            />
            {patientData.urate > 480 && <span className="field-warning">Elevated — TLS / gout risk</span>}
          </div>
          <div className="form-group">
            <label htmlFor="calcium">
              Corrected Calcium (mmol/L)
              <span className="normal-range">Normal: 2.2–2.6</span>
            </label>
            <input
              id="calcium"
              type="number"
              step="0.01"
              min="0"
              value={patientData.calcium || ''}
              onChange={(e) => onChange('calcium', e.target.value)}
              placeholder="e.g., 2.4"
              className={patientData.calcium > 2.8 ? 'warning-input' : patientData.calcium > 0 && patientData.calcium < 2.1 ? 'warning-input' : ''}
            />
            {patientData.calcium > 2.8 && <span className="field-warning">Hypercalcaemia</span>}
            {patientData.calcium > 0 && patientData.calcium < 2.1 && <span className="field-warning">Hypocalcaemia</span>}
          </div>
          <div className="form-group">
            <label htmlFor="lvef">
              LVEF (%)
              <span className="normal-range">Normal: &gt;55%</span>
            </label>
            <input
              id="lvef"
              type="number"
              step="1"
              min="0"
              max="100"
              value={patientData.lvef_percent || ''}
              onChange={(e) => onChange('lvef_percent', e.target.value)}
              placeholder="e.g., 60"
              className={patientData.lvef_percent > 0 && patientData.lvef_percent < 50 ? 'critical-input' : patientData.lvef_percent > 0 && patientData.lvef_percent < 55 ? 'warning-input' : ''}
            />
            {patientData.lvef_percent > 0 && patientData.lvef_percent < 50 && (
              <span className="field-critical">Reduced LVEF — anthracycline use requires cardiology review</span>
            )}
            {patientData.lvef_percent >= 50 && patientData.lvef_percent < 55 && (
              <span className="field-warning">Low-normal LVEF — monitor closely on anthracyclines</span>
            )}
          </div>
        </div>
      </div>

      {/* Virology Panel */}
      <div className="form-section">
        <h3>Virology Panel</h3>
        <p className="section-hint">Affects prophylaxis decisions and immunosuppression risks</p>
        <div className="form-grid">
          {[
            { field: 'hep_b_surface_antigen', label: 'HBsAg', hint: 'Positive → antiviral prophylaxis mandatory with rituximab' },
            { field: 'hep_b_core_antibody', label: 'HBcAb', hint: 'Positive → reactivation risk with rituximab — monitor HBV DNA' },
            { field: 'hep_c_antibody', label: 'HCV Antibody', hint: '' },
            { field: 'hiv_status', label: 'HIV', hint: 'Positive → specialist review before immunosuppressive chemo' },
            { field: 'ebv_status', label: 'EBV', hint: '' },
            { field: 'cmv_status', label: 'CMV', hint: 'Positive → increased reactivation risk post-transplant' },
            { field: 'vzv_status', label: 'VZV', hint: 'Negative → consider vaccination before treatment' },
          ].map(({ field, label, hint }) => (
            <div className="form-group" key={field}>
              <label htmlFor={field}>{label}</label>
              <select
                id={field}
                value={patientData[field] || ''}
                onChange={(e) => onChange(field, e.target.value)}
              >
                <option value="">Unknown</option>
                <option value="negative">Negative</option>
                <option value="positive">Positive</option>
              </select>
              {hint && patientData[field] === 'positive' && (
                <span className="field-warning">{hint}</span>
              )}
            </div>
          ))}
          <div className="form-group">
            <label htmlFor="g6pd_status">G6PD Status</label>
            <select
              id="g6pd_status"
              value={patientData.g6pd_status || ''}
              onChange={(e) => onChange('g6pd_status', e.target.value)}
            >
              <option value="">Unknown</option>
              <option value="normal">Normal</option>
              <option value="deficient">Deficient</option>
            </select>
            {patientData.g6pd_status === 'deficient' && (
              <span className="field-critical">G6PD deficiency — rasburicase CONTRAINDICATED (haemolytic anaemia risk)</span>
            )}
          </div>
        </div>
      </div>

      {/* Cumulative Toxicity Section */}
      <div className="form-section">
        <h3>
          <svg viewBox="0 0 24 24" width="20" height="20" fill="#f39c12">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
          </svg>
          Prior Treatment History
        </h3>
        <p className="section-hint">Enter if patient has received prior anthracyclines or bleomycin</p>

        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="prior_anthracycline">
              Prior Anthracycline Dose (mg/m²)
              <span className="normal-range">Lifetime max: 450 mg/m²</span>
            </label>
            <input
              id="prior_anthracycline"
              type="number"
              step="1"
              min="0"
              value={patientData.prior_anthracycline_dose_mg_m2 || ''}
              onChange={(e) => onChange('prior_anthracycline_dose_mg_m2', e.target.value)}
              placeholder="e.g., 200"
              className={patientData.prior_anthracycline_dose_mg_m2 > 350 ? 'warning-input' : ''}
            />
            {patientData.prior_anthracycline_dose_mg_m2 > 450 && (
              <span className="field-critical">LIFETIME LIMIT EXCEEDED - Cardiac toxicity risk</span>
            )}
            {patientData.prior_anthracycline_dose_mg_m2 > 350 && patientData.prior_anthracycline_dose_mg_m2 <= 450 && (
              <span className="field-warning">Approaching lifetime limit - Monitor cardiac function</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="prior_bleomycin">
              Prior Bleomycin Dose (units)
              <span className="normal-range">Lifetime max: 400,000 units</span>
            </label>
            <input
              id="prior_bleomycin"
              type="number"
              step="1000"
              min="0"
              value={patientData.prior_bleomycin_units || ''}
              onChange={(e) => onChange('prior_bleomycin_units', e.target.value)}
              placeholder="e.g., 30000"
            />
            {patientData.prior_bleomycin_units > 400000 && (
              <span className="field-critical">LIFETIME LIMIT EXCEEDED - Pulmonary fibrosis risk</span>
            )}
          </div>

          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={patientData.prior_cardiac_history || false}
                onChange={(e) => onChange('prior_cardiac_history', e.target.checked)}
                style={{ marginRight: 8 }}
              />
              Prior cardiac history
            </label>
            {patientData.prior_cardiac_history && (
              <span className="field-warning">Anthracycline limit reduced to 400 mg/m²</span>
            )}
          </div>

          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={patientData.prior_mediastinal_radiation || false}
                onChange={(e) => onChange('prior_mediastinal_radiation', e.target.checked)}
                style={{ marginRight: 8 }}
              />
              Prior mediastinal radiation
            </label>
            {patientData.prior_mediastinal_radiation && (
              <span className="field-warning">Anthracycline limit reduced to 350 mg/m²</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
