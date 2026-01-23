import React from 'react';

export function DrugSelector({
  protocol,
  excludedDrugs,
  onDrugToggle,
  includePremeds,
  onPremedsChange,
  includeTakeHome,
  onTakeHomeChange,
  includeRescue,
  onRescueChange
}) {
  const coreDrugs = protocol.drugs || [];
  const preMedications = protocol.pre_medications || [];
  const takeHomeMeds = protocol.take_home_medicines || [];
  const rescueMeds = protocol.rescue_medications || [];

  const isDrugExcluded = (drugName) => excludedDrugs.includes(drugName);

  const DrugItem = ({ drug, isCore = false }) => {
    const excluded = isDrugExcluded(drug.drug_name);
    
    return (
      <div 
        className={`drug-item ${excluded ? 'excluded' : ''} ${isCore ? 'core' : ''}`}
        onClick={() => onDrugToggle(drug.drug_name)}
      >
        <div className="drug-checkbox">
          {!excluded ? (
            <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-9 14l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
              <path d="M19 5v14H5V5h14m0-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z"/>
            </svg>
          )}
        </div>
        
        <div className="drug-info">
          <div className="drug-header">
            <span className="drug-name">{drug.drug_name}</span>
            {isCore && <span className="core-badge">Core</span>}
            {drug.prn && <span className="prn-badge">PRN</span>}
          </div>
          
          <div className="drug-details">
            <span className="drug-dose">
              {drug.dose} {drug.dose_unit}
            </span>
            <span className="drug-route">{drug.route}</span>
            <span className="drug-days">
              Day{drug.days?.length > 1 ? 's' : ''} {drug.days?.join(', ')}
            </span>
          </div>
          
          {drug.special_instructions && (
            <div className="drug-instructions">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
              </svg>
              {drug.special_instructions}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="drug-selector">
      <div className="selector-header">
        <h2>Drug Selection</h2>
        <p>Click on drugs to include/exclude them from the protocol</p>
      </div>

      {/* Core Chemotherapy Drugs */}
      <div className="drug-section">
        <div className="section-header">
          <h3>
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M12 2l-5.5 9h11z M12 22l-5.5-9h11z"/>
            </svg>
            Core Chemotherapy Drugs
          </h3>
          <span className="drug-count">
            {coreDrugs.filter(d => !isDrugExcluded(d.drug_name)).length} / {coreDrugs.length} selected
          </span>
        </div>
        
        <div className="drug-list">
          {coreDrugs.map((drug, i) => (
            <DrugItem key={i} drug={drug} isCore={true} />
          ))}
        </div>
      </div>

      {/* Pre-medications */}
      {preMedications.length > 0 && (
        <div className="drug-section">
          <div className="section-header">
            <h3>
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
              </svg>
              Pre-medications
            </h3>
            <label className="toggle-all">
              <input
                type="checkbox"
                checked={includePremeds}
                onChange={(e) => onPremedsChange(e.target.checked)}
              />
              <span>Include all</span>
            </label>
          </div>
          
          {includePremeds && (
            <div className="drug-list">
              {preMedications.map((drug, i) => (
                <DrugItem key={i} drug={drug} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Take-home Medications */}
      {takeHomeMeds.length > 0 && (
        <div className="drug-section">
          <div className="section-header">
            <h3>
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
              </svg>
              Take-home Medications
            </h3>
            <label className="toggle-all">
              <input
                type="checkbox"
                checked={includeTakeHome}
                onChange={(e) => onTakeHomeChange(e.target.checked)}
              />
              <span>Include all</span>
            </label>
          </div>
          
          {includeTakeHome && (
            <div className="drug-list">
              {takeHomeMeds.map((drug, i) => (
                <DrugItem key={i} drug={drug} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Rescue Medications */}
      {rescueMeds.length > 0 && (
        <div className="drug-section">
          <div className="section-header">
            <h3>
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
              Rescue Medications (PRN)
            </h3>
            <label className="toggle-all">
              <input
                type="checkbox"
                checked={includeRescue}
                onChange={(e) => onRescueChange(e.target.checked)}
              />
              <span>Include all</span>
            </label>
          </div>
          
          {includeRescue && (
            <div className="drug-list">
              {rescueMeds.map((drug, i) => (
                <DrugItem key={i} drug={drug} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Summary */}
      <div className="selection-summary">
        <h4>Selection Summary</h4>
        <div className="summary-stats">
          <div className="stat">
            <span className="stat-value">
              {coreDrugs.filter(d => !isDrugExcluded(d.drug_name)).length}
            </span>
            <span className="stat-label">Core drugs</span>
          </div>
          {includePremeds && (
            <div className="stat">
              <span className="stat-value">
                {preMedications.filter(d => !isDrugExcluded(d.drug_name)).length}
              </span>
              <span className="stat-label">Pre-meds</span>
            </div>
          )}
          {includeTakeHome && (
            <div className="stat">
              <span className="stat-value">
                {takeHomeMeds.filter(d => !isDrugExcluded(d.drug_name)).length}
              </span>
              <span className="stat-label">Take-home</span>
            </div>
          )}
        </div>
        
        {excludedDrugs.length > 0 && (
          <div className="excluded-list">
            <span className="excluded-label">Excluded:</span>
            {excludedDrugs.map((drug, i) => (
              <span key={i} className="excluded-drug">{drug}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
