import React, { useRef } from 'react';

export function ProtocolDisplay({ protocol, onBack, onReset }) {
  const printRef = useRef();

  const handlePrint = () => {
    const printContent = printRef.current;
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>${protocol.protocol_code} - Cycle ${protocol.cycle_number}</title>
          <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
              font-family: Arial, sans-serif; 
              font-size: 11pt; 
              line-height: 1.4;
              padding: 20px;
              color: #333;
            }
            .print-header { 
              text-align: center; 
              border-bottom: 2px solid #000; 
              padding-bottom: 15px; 
              margin-bottom: 20px; 
            }
            .print-header h1 { font-size: 18pt; margin-bottom: 5px; }
            .print-header .subtitle { font-size: 14pt; color: #555; }
            .print-header .meta { font-size: 10pt; margin-top: 10px; }
            
            .section { margin-bottom: 20px; }
            .section h2 { 
              font-size: 12pt; 
              background: #f0f0f0; 
              padding: 8px 12px; 
              margin-bottom: 10px;
              border-left: 4px solid #333;
            }
            
            table { 
              width: 100%; 
              border-collapse: collapse; 
              margin-bottom: 15px;
              font-size: 10pt;
            }
            th, td { 
              border: 1px solid #ccc; 
              padding: 8px; 
              text-align: left; 
            }
            th { 
              background: #f5f5f5; 
              font-weight: bold;
            }
            
            .warning { 
              background: #fff3cd; 
              border: 1px solid #ffc107;
              padding: 8px 12px; 
              margin: 5px 0;
              font-size: 10pt;
            }
            .warning.critical { 
              background: #f8d7da; 
              border-color: #dc3545;
            }
            
            .modified { color: #dc3545; font-weight: bold; }
            .footer { 
              margin-top: 30px; 
              padding-top: 15px;
              border-top: 1px solid #ccc; 
              font-size: 9pt; 
              color: #666;
            }
            
            @media print {
              body { padding: 0; }
              .no-print { display: none; }
            }
          </style>
        </head>
        <body>
          ${printContent.innerHTML}
          <div class="footer">
            <p>Generated: ${new Date().toLocaleString()}</p>
            <p><strong>SOPHIA</strong> - System for Orchestrating Protocol-guided Healthcare Inference & Analysis</p>
            <p>Powered by <strong>Jivana AI</strong></p>
            <p><strong>This document is for clinical reference only. Always verify doses independently.</strong></p>
          </div>
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };

  const formatDose = (drug) => {
    let doseStr = `${drug.calculated_dose} ${drug.calculated_dose_unit}`;
    if (drug.banded_dose) {
      doseStr += ` (banded: ${drug.banded_dose} ${drug.calculated_dose_unit})`;
    }
    return doseStr;
  };

  const DrugTable = ({ drugs, title }) => {
    if (!drugs || drugs.length === 0) return null;

    return (
      <div className="section">
        <h2>{title}</h2>
        <table>
          <thead>
            <tr>
              <th style={{width: '20%'}}>Drug</th>
              <th style={{width: '15%'}}>Dose</th>
              <th style={{width: '12%'}}>Route</th>
              <th style={{width: '10%'}}>Days</th>
              <th style={{width: '43%'}}>Instructions</th>
            </tr>
          </thead>
          <tbody>
            {drugs.map((drug, i) => (
              <tr key={i} className={drug.dose_modified ? 'modified-row' : ''}>
                <td>
                  <strong>{drug.drug_name}</strong>
                  {drug.prn && <span className="prn-tag"> (PRN)</span>}
                </td>
                <td className={drug.dose_modified ? 'modified' : ''}>
                  {formatDose(drug)}
                  {drug.dose_modified && (
                    <div className="modification-note">
                      {drug.modification_reason}
                    </div>
                  )}
                </td>
                <td>{drug.route}</td>
                <td>{drug.days?.join(', ')}</td>
                <td>
                  {drug.duration_minutes && (
                    <div>Over {drug.duration_minutes} mins</div>
                  )}
                  {drug.diluent && (
                    <div>In {drug.diluent_volume_ml}ml {drug.diluent}</div>
                  )}
                  {drug.frequency && (
                    <div>{drug.frequency}</div>
                  )}
                  {drug.timing && (
                    <div>{drug.timing}</div>
                  )}
                  {drug.special_instructions && (
                    <div className="special">{drug.special_instructions}</div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="protocol-display">
      <div className="display-actions">
        <button className="btn-secondary" onClick={onBack}>
          ← Modify Selection
        </button>
        <button className="btn-primary" onClick={handlePrint}>
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M19 8H5c-1.66 0-3 1.34-3 3v6h4v4h12v-4h4v-6c0-1.66-1.34-3-3-3zm-3 11H8v-5h8v5zm3-7c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm-1-9H6v4h12V3z"/>
          </svg>
          Print Protocol
        </button>
        <button className="btn-success" onClick={onReset}>
          New Protocol
        </button>
      </div>

      {/* Printable Content */}
      <div ref={printRef} className="protocol-content">
        <div className="print-header">
          <h1>{protocol.protocol_code}</h1>
          <div className="subtitle">{protocol.protocol_name}</div>
          <div className="meta">
            <span>Cycle {protocol.cycle_number} of {protocol.total_cycles}</span>
            <span> | </span>
            <span>{protocol.cycle_length_days}-day cycle</span>
            <span> | </span>
            <span>BSA: {protocol.patient_bsa} m²</span>
            <span> | </span>
            <span>Weight: {protocol.patient_weight} kg</span>
          </div>
        </div>

        {/* Warnings */}
        {protocol.warnings && protocol.warnings.length > 0 && (
          <div className="section warnings-section">
            <h2>⚠️ Warnings & Alerts</h2>
            {protocol.warnings.map((warning, i) => (
              <div key={i} className={`warning ${warning.level}`}>
                <strong>{warning.level.toUpperCase()}:</strong> {warning.message}
              </div>
            ))}
          </div>
        )}

        {/* Dose Modifications Applied */}
        {protocol.dose_modifications_applied && protocol.dose_modifications_applied.length > 0 && (
          <div className="section modifications-section">
            <h2>📋 Dose Modifications Applied</h2>
            <ul>
              {protocol.dose_modifications_applied.map((mod, i) => (
                <li key={i}>{mod}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Pre-medications */}
        <DrugTable drugs={protocol.pre_medications} title="Pre-medications" />

        {/* Chemotherapy Drugs */}
        <DrugTable drugs={protocol.chemotherapy_drugs} title="Chemotherapy" />

        {/* Take-home Medicines */}
        <DrugTable drugs={protocol.take_home_medicines} title="Take-home Medications" />

        {/* Rescue Medications */}
        <DrugTable drugs={protocol.rescue_medications} title="Rescue Medications (PRN)" />

        {/* Monitoring Requirements */}
        {protocol.monitoring_requirements && protocol.monitoring_requirements.length > 0 && (
          <div className="section">
            <h2>Monitoring Requirements</h2>
            <ul className="monitoring-list">
              {protocol.monitoring_requirements.map((req, i) => (
                <li key={i}>{req}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Special Instructions */}
        {protocol.special_instructions && protocol.special_instructions.length > 0 && (
          <div className="section">
            <h2>Special Instructions</h2>
            <ul className="instructions-list">
              {protocol.special_instructions.map((inst, i) => (
                <li key={i}>{inst}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
