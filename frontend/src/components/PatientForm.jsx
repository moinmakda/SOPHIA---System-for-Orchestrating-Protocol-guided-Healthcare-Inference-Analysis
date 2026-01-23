import React, { useMemo } from 'react';

export function PatientForm({ patientData, onChange, cycleNumber, onCycleChange, totalCycles }) {
  
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

  const cycleOptions = Array.from({ length: totalCycles }, (_, i) => i + 1);

  return (
    <div className="patient-form">
      <h2>Patient Information</h2>
      
      <div className="form-section">
        <h3>
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
          Required Information
        </h3>
        
        <div className="form-grid">
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
            <label>Calculated BSA</label>
            <div className="bsa-display">
              {calculatedBSA ? (
                <>
                  <span className="bsa-value">{calculatedBSA}</span>
                  <span className="bsa-unit">m²</span>
                </>
              ) : (
                <span className="bsa-placeholder">Enter height & weight</span>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="form-section">
        <h3>
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/>
          </svg>
          Lab Values (for dose modifications)
        </h3>
        <p className="section-hint">Leave blank if not applicable or normal values</p>
        
        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="neutrophils">
              Neutrophils (×10⁹/L)
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
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="platelets">
              Platelets (×10⁹/L)
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
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="bilirubin">
              Bilirubin (µmol/L)
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
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="crcl">
              Creatinine Clearance (ml/min)
              <span className="normal-range">Normal: &gt;90</span>
            </label>
            <input
              id="crcl"
              type="number"
              step="1"
              min="0"
              value={patientData.creatinine_clearance}
              onChange={(e) => onChange('creatinine_clearance', e.target.value)}
              placeholder="e.g., 90"
            />
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
          
          <div className="form-group">
            <label htmlFor="hemoglobin">
              Hemoglobin (g/dL)
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
            />
          </div>
        </div>
      </div>
    </div>
  );
}
