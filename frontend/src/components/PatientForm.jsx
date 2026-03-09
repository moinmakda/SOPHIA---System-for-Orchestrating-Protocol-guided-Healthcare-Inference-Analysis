import React, { useMemo, useState } from 'react';

const BSA_CAP = 2.0;

const VALID_START_DAYS = new Set([1, 2, 5]); // Mon=1, Tue=2, Fri=5 (getDay: Sun=0)
const VALID_START_NAMES = 'Monday, Tuesday or Friday';

export function PatientForm({ patientData, onChange, cycleNumber, onCycleChange, totalCycles, protocolCode = '' }) {

  const isBlina = protocolCode.includes('BLINA');
  // Protocols that include bleomycin (e.g. ABVD, BEACOPP) — hide field for RCHOP21 and blinatumomab
  const hasBleomycin = !isBlina && !protocolCode.includes('RCHOP');

  const [showAllergyInput, setShowAllergyInput] = useState(false);
  const [newAllergy, setNewAllergy] = useState('');
  const [useManualCrCl, setUseManualCrCl] = useState(false);

  // Validate blinatumomab start date is Mon/Tue/Fri
  const startDateError = useMemo(() => {
    if (!isBlina || !patientData.treatment_start_date) return null;
    const d = new Date(patientData.treatment_start_date + 'T00:00:00');
    const day = d.getDay(); // 0=Sun,1=Mon,...,6=Sat
    if (!VALID_START_DAYS.has(day)) {
      const names = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
      return `${names[day]} is not a valid start day. Blinatumomab must start on ${VALID_START_NAMES}.`;
    }
    return null;
  }, [isBlina, patientData.treatment_start_date]);

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

      {/* Treatment Start Date — used for continuous infusion bag schedules */}
      <div className="form-section" style={{ marginBottom: 8 }}>
        <div className="form-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
          <div className="form-group">
            <label htmlFor="treatment_start_date">
              Treatment Start Date
              {isBlina && (
                <span style={{ fontWeight: 600, fontSize: 12, color: '#c62828', marginLeft: 6 }}>
                  * Must be Mon, Tue or Fri
                </span>
              )}
            </label>
            <input
              id="treatment_start_date"
              type="date"
              value={patientData.treatment_start_date || ''}
              onChange={(e) => onChange('treatment_start_date', e.target.value)}
              className={startDateError ? 'danger-input' : ''}
            />
            {startDateError && (
              <span className="field-critical">{startDateError}</span>
            )}
          </div>
        </div>
      </div>

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

          {!isBlina && (
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
          )}

          {!isBlina && (
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
          )}
          
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
          
          {!isBlina && <div className="form-group calculated-bsa">
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
          </div>}
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
          Lab Values
        </h3>
        <p className="section-hint critical-hint">⚠️ All applicable lab values required — "No labs, no chemo"</p>

        {isBlina && (
          <div style={{ background: '#fff8e1', border: '1px solid #f9a825', borderRadius: 4, padding: '8px 12px', marginBottom: 12, fontSize: 12 }}>
            Blinatumomab is a fixed flat dose — haematological values (Neutrophils, Platelets, Hb) are for baseline monitoring only, not dose modification.
          </div>
        )}

        <div className="form-grid">
          {!isBlina && <div className="form-group">
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
          </div>}

          {!isBlina && <div className="form-group">
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
          </div>}

          {!isBlina && <div className="form-group">
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
          </div>}
          
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
                placeholder={calculatedCrCl ? `Auto: ${calculatedCrCl}` : "Enter measured CrCl"}
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
              <span className="field-info">Auto-calculated (Cockcroft-Gault) — or enter measured value manually</span>
            )}
            {patientData.creatinine_clearance && patientData.creatinine_clearance < 10 && (
              <span className="field-critical">TREATMENT CONTRAINDICATED: Severe renal failure</span>
            )}
            {patientData.creatinine_clearance && patientData.creatinine_clearance >= 10 && patientData.creatinine_clearance < 30 && (
              <span className="field-warning">Severe renal impairment - review nephrotoxic drugs</span>
            )}
            {/* Optional CrCl auto-calculator inputs */}
            {useManualCrCl || !calculatedCrCl ? (
              <details style={{ marginTop: 8 }}>
                <summary style={{ fontSize: 12, color: '#1976d2', cursor: 'pointer' }}>
                  Calculate using Cockcroft-Gault
                </summary>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 8 }}>
                  <div>
                    <label style={{ fontSize: 12 }}>Sex</label>
                    <select
                      value={patientData.sex || ''}
                      onChange={(e) => onChange('sex', e.target.value)}
                      style={{ fontSize: 12 }}
                    >
                      <option value="">Select...</option>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: 12 }}>Serum Creatinine (mg/dL)</label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={patientData.serum_creatinine || ''}
                      onChange={(e) => onChange('serum_creatinine', e.target.value)}
                      placeholder="e.g., 1.0"
                      style={{ fontSize: 12 }}
                    />
                  </div>
                </div>
                {calculatedCrCl && (
                  <div style={{ marginTop: 6, fontSize: 12, color: '#2e7d32' }}>
                    Calculated CrCl: <strong>{calculatedCrCl} ml/min</strong>
                    <button
                      type="button"
                      style={{ marginLeft: 8, fontSize: 11, padding: '1px 6px' }}
                      onClick={() => {
                        setUseManualCrCl(false);
                        onChange('creatinine_clearance', calculatedCrCl.toString());
                      }}
                    >
                      Use this value
                    </button>
                  </div>
                )}
              </details>
            ) : null}
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
      
      {/* Treatment Safety Checklist */}
      <div className="form-section">
        <h3>
          <svg viewBox="0 0 24 24" width="20" height="20" fill="#e74c3c">
            <path d="M12 2L1 21h22L12 2zm0 3.99L19.53 19H4.47L12 5.99zM11 10v4h2v-4h-2zm0 6v2h2v-2h-2z"/>
          </svg>
          Treatment Safety Checklist
        </h3>
        <p className="section-hint critical-hint">⚠️ Required before every cycle — these drive critical safety warnings</p>
        <div className="form-grid">

          <div className="form-group">
            <label htmlFor="active_infection">Active Infection / Fever?</label>
            <select
              id="active_infection"
              value={patientData.active_infection === true ? 'yes' : patientData.active_infection === false ? 'no' : ''}
              onChange={(e) => onChange('active_infection', e.target.value === 'yes' ? true : e.target.value === 'no' ? false : null)}
            >
              <option value="">Unknown / not assessed</option>
              <option value="no">No — afebrile, no active infection</option>
              <option value="yes">Yes — active infection or fever present</option>
            </select>
            {patientData.active_infection === true && (
              <span className="field-critical">TREATMENT DELAY: Treat infection first</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="pregnancy_status">Pregnancy Status</label>
            <select
              id="pregnancy_status"
              value={patientData.pregnancy_status || ''}
              onChange={(e) => onChange('pregnancy_status', e.target.value || null)}
            >
              <option value="">Not recorded</option>
              <option value="not_applicable">Not applicable</option>
              <option value="not_pregnant">Not pregnant</option>
              <option value="pregnant">Pregnant</option>
              <option value="unknown">Unknown</option>
            </select>
            {patientData.pregnancy_status === 'pregnant' && (
              <span className="field-critical">Cytotoxic chemotherapy — specialist review required</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="hbsag">HBsAg</label>
            <select
              id="hbsag"
              value={patientData.hep_b_surface_antigen || ''}
              onChange={(e) => onChange('hep_b_surface_antigen', e.target.value || null)}
            >
              <option value="">Not tested</option>
              <option value="negative">Negative</option>
              <option value="positive">Positive</option>
            </select>
            {patientData.hep_b_surface_antigen === 'positive' && (
              <span className="field-critical">HBsAg+ — antiviral prophylaxis mandatory with rituximab</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="hbcab">Anti-HBc</label>
            <select
              id="hbcab"
              value={patientData.hep_b_core_antibody || ''}
              onChange={(e) => onChange('hep_b_core_antibody', e.target.value || null)}
            >
              <option value="">Not tested</option>
              <option value="negative">Negative</option>
              <option value="positive">Positive</option>
            </select>
            {patientData.hep_b_core_antibody === 'positive' && (
              <span className="field-warning">Anti-HBc+ — reactivation risk with rituximab; prophylaxis or monitoring required</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="hbv_prophylaxis">HBV Prophylaxis Started?</label>
            <select
              id="hbv_prophylaxis"
              value={patientData.hbv_prophylaxis_started === true ? 'yes' : patientData.hbv_prophylaxis_started === false ? 'no' : ''}
              onChange={(e) => onChange('hbv_prophylaxis_started', e.target.value === 'yes' ? true : e.target.value === 'no' ? false : null)}
            >
              <option value="">N/A</option>
              <option value="yes">Yes — entecavir/tenofovir prescribed</option>
              <option value="no">No</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="peripheral_neuropathy_grade">
              Peripheral Neuropathy Grade
              <span className="normal-range">CTCAE 0–4</span>
            </label>
            <select
              id="peripheral_neuropathy_grade"
              value={patientData.peripheral_neuropathy_grade ?? ''}
              onChange={(e) => onChange('peripheral_neuropathy_grade', e.target.value !== '' ? parseInt(e.target.value) : null)}
            >
              <option value="">Not assessed</option>
              <option value="0">Grade 0 — none</option>
              <option value="1">Grade 1 — asymptomatic</option>
              <option value="2">Grade 2 — limiting instrumental ADL</option>
              <option value="3">Grade 3 — limiting self-care ADL</option>
              <option value="4">Grade 4 — life threatening</option>
            </select>
            {patientData.peripheral_neuropathy_grade >= 3 && (
              <span className="field-critical">Grade ≥3 — vincristine must be omitted</span>
            )}
            {patientData.peripheral_neuropathy_grade === 2 && (
              <span className="field-warning">Grade 2 — vincristine dose reduction required</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="lvef">
              Baseline LVEF (%)
              <span className="normal-range">Required if age ≥70 or cardiac history</span>
            </label>
            <input
              id="lvef"
              type="number"
              step="1"
              min="0"
              max="100"
              value={patientData.lvef_percent || ''}
              onChange={(e) => onChange('lvef_percent', e.target.value || null)}
              placeholder="e.g., 60"
              className={
                patientData.lvef_percent > 0 && patientData.lvef_percent < 50 ? 'danger-input' :
                patientData.lvef_percent > 0 && patientData.lvef_percent < 55 ? 'warning-input' : ''
              }
            />
            {patientData.lvef_percent > 0 && patientData.lvef_percent < 50 && (
              <span className="field-critical">LVEF &lt;50% — cardiology review before doxorubicin</span>
            )}
            {patientData.lvef_percent >= 50 && patientData.lvef_percent < 55 && (
              <span className="field-warning">Borderline LVEF — monitor closely</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="tls_risk">Tumour Lysis Risk</label>
            <select
              id="tls_risk"
              value={patientData.tls_risk || ''}
              onChange={(e) => onChange('tls_risk', e.target.value || null)}
            >
              <option value="">Not assessed</option>
              <option value="low">Low</option>
              <option value="intermediate">Intermediate</option>
              <option value="high">High</option>
            </select>
            {patientData.tls_risk === 'high' && (
              <span className="field-critical">High TLS risk — rasburicase + hydration required</span>
            )}
            {patientData.tls_risk === 'intermediate' && (
              <span className="field-warning">Intermediate TLS risk — allopurinol + hydration</span>
            )}
          </div>

        </div>
      </div>

      {/* Prior Treatment History — hidden for blinatumomab */}
      {!isBlina && <div className="form-section">
        <h3>
          <svg viewBox="0 0 24 24" width="20" height="20" fill="#f39c12">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
          </svg>
          Prior Treatment History
        </h3>
        <p className="section-hint">Cumulative lifetime doses — relevant for anthracycline (doxorubicin) and bleomycin protocols</p>

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

          {hasBleomycin && <div className="form-group">
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
          </div>}

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
      </div>}

      {/* Blinatumomab-specific: Blast Count Assessment */}
      {isBlina && (
        <div className="form-section">
          <h3>
            <svg viewBox="0 0 24 24" width="20" height="20" fill="#c62828">
              <path d="M12 2L1 21h22L12 2zm0 3.99L19.53 19H4.47L12 5.99zM11 10v4h2v-4h-2zm0 6v2h2v-2h-2z"/>
            </svg>
            Blast Count Assessment (Cycle 1)
          </h3>
          <p className="section-hint critical-hint">
            ⚠️ Pre-phase dexamethasone required if peripheral blasts &gt;15% or bone marrow blasts &gt;50%
          </p>
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="peripheral_blast">
                Peripheral Blast Count (%)
                <span className="normal-range">Pre-phase threshold: &gt;15%</span>
              </label>
              <input
                id="peripheral_blast"
                type="number"
                step="1"
                min="0"
                max="100"
                value={patientData.peripheral_blast_percent ?? ''}
                onChange={(e) => onChange('peripheral_blast_percent', e.target.value !== '' ? parseFloat(e.target.value) : null)}
                placeholder="e.g., 10"
                className={patientData.peripheral_blast_percent > 15 ? 'danger-input' : ''}
              />
              {patientData.peripheral_blast_percent > 15 && (
                <span className="field-critical">PRE-PHASE REQUIRED: &gt;15% peripheral blasts</span>
              )}
            </div>
            <div className="form-group">
              <label htmlFor="bm_blast">
                Bone Marrow Blasts (%)
                <span className="normal-range">Pre-phase threshold: &gt;50%</span>
              </label>
              <input
                id="bm_blast"
                type="number"
                step="1"
                min="0"
                max="100"
                value={patientData.bone_marrow_blast_percent ?? ''}
                onChange={(e) => onChange('bone_marrow_blast_percent', e.target.value !== '' ? parseFloat(e.target.value) : null)}
                placeholder="e.g., 30"
                className={patientData.bone_marrow_blast_percent > 50 ? 'danger-input' : ''}
              />
              {patientData.bone_marrow_blast_percent > 50 && (
                <span className="field-critical">PRE-PHASE REQUIRED: &gt;50% bone marrow blasts</span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
