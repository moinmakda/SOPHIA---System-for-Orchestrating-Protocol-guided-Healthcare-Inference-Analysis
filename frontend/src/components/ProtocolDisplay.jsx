import React, { useRef, useState, useEffect } from 'react';

// Map Unicode superscript digits to their ASCII equivalents for reliable rendering
const SUPERSCRIPT_MAP = {
  '⁰':'0','¹':'1','²':'2','³':'3','⁴':'4',
  '⁵':'5','⁶':'6','⁷':'7','⁸':'8','⁹':'9',
};

/**
 * Replace Unicode superscript digits (e.g. ⁹ in 10⁹/L) with <sup> HTML elements
 * so they render correctly regardless of font support.
 * Returns an array of React nodes (safe — no dangerouslySetInnerHTML).
 */
function renderWithSuperscripts(text) {
  if (!text) return text;
  // Split on runs of superscript digits
  const parts = text.split(/([\u2070-\u2079\u00B2\u00B3\u00B9]+)/);
  if (parts.length === 1) return text;
  return parts.map((part, i) => {
    const isSuper = /^[\u2070-\u2079\u00B2\u00B3\u00B9]+$/.test(part);
    if (isSuper) {
      const digits = part.split('').map(c => SUPERSCRIPT_MAP[c] || c).join('');
      return <sup key={i}>{digits}</sup>;
    }
    return part;
  });
}

export function ProtocolDisplay({ protocol, onBack, onReset }) {
  const printRef = useRef();
  const [hasAcknowledged, setHasAcknowledged] = useState(false);
  const [canPrint, setCanPrint] = useState(false);

  // Check for critical warnings
  const hasCriticalWarnings = protocol.warnings?.some(w => w.level === 'critical') || false;
  const isAiGenerated = protocol.is_ai_generated || (protocol.warnings && protocol.warnings.some(w => w.message && w.message.includes("AI-EXTRACTED")));

  useEffect(() => {
    // Enable print only if acknowledged or (no critical warnings AND not AI generated)
    // Actually, AI generated ALWAYS requires verification per our plan.
    if (hasCriticalWarnings || isAiGenerated) {
      setCanPrint(hasAcknowledged);
    } else {
      setCanPrint(true);
    }
  }, [hasAcknowledged, hasCriticalWarnings, isAiGenerated]);

  const handlePrint = () => {
    if (!canPrint) return;
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
              font-weight: bold;
            }
            
            .modified { color: #dc3545; font-weight: bold; }
            .footer { 
              margin-top: 30px; 
              padding-top: 15px;
              border-top: 1px solid #ccc; 
              font-size: 9pt; 
              color: #666;
            }
            
            .verification-box {
                border: 2px solid #000;
                padding: 10px;
                margin-bottom: 20px;
                font-weight: bold;
                text-align: center;
            }

            @media print {
              body { padding: 0; }
              .no-print { display: none; }
            }
          </style>
        </head>
        <body>
          ${hasAcknowledged ? '<div class="verification-box">✓ VERIFIED BY PHARMACIST/PRESCRIBER</div>' : ''}
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

  const formatDuration = (minutes) => {
    if (!minutes) return null;
    if (minutes < 60) return `${minutes} mins`;
    const hours = minutes / 60;
    // Show as hours if < 48h or not a round number of days
    const days = hours / 24;
    const isRoundDays = Math.abs(days - Math.round(days)) < 0.05;
    if (hours < 48 || !isRoundDays) {
      const h = Math.floor(hours);
      const m = Math.round((hours - h) * 60);
      return m > 0 ? `${h} hr ${m} mins` : `${h} hr`;
    }
    return `${Math.round(days)} days`;
  };

  const roundDose = (v) => {
    if (v == null) return v;
    const n = parseFloat(v);
    if (isNaN(n)) return v;
    // Round to at most 2 decimal places, strip trailing zeros
    return parseFloat(n.toFixed(2));
  };

  const formatDose = (drug) => {
    if (drug.calculated_dose_unit === 'per label') {
      return 'Per prescriber / product label';
    }
    if (drug.banded_dose) {
      const calculatedDisplay = roundDose(drug.uncapped_calculated_dose ?? drug.calculated_dose);
      return `${drug.banded_dose} ${drug.calculated_dose_unit} (banded; calculated: ${calculatedDisplay} ${drug.calculated_dose_unit})`;
    }
    if (drug.uncapped_calculated_dose) {
      return `${roundDose(drug.calculated_dose)} ${drug.calculated_dose_unit} (capped; calculated: ${roundDose(drug.uncapped_calculated_dose)} ${drug.calculated_dose_unit})`;
    }
    return `${roundDose(drug.calculated_dose)} ${drug.calculated_dose_unit}`;
  };

  const DrugTable = ({ drugs, title }) => {
    if (!drugs || drugs.length === 0) return null;

    return (
      <div className="section">
        <h2>{title}</h2>
        <table>
          <thead>
            <tr>
              <th style={{ width: '20%' }}>Drug</th>
              <th style={{ width: '15%' }}>Dose</th>
              <th style={{ width: '12%' }}>Route</th>
              <th style={{ width: '10%' }}>Days</th>
              <th style={{ width: '43%' }}>Instructions</th>
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
                  {drug.dose_modified && drug.modification_percent > 0 && drug.modification_percent < 100 && !drug.uncapped_calculated_dose && (
                    <div className="modification-note">
                      ↓{drug.modification_percent}% dose reduction applied
                    </div>
                  )}
                  {drug.uncapped_calculated_dose && (
                    <div className="modification-note">
                      capped at {roundDose(drug.calculated_dose)} {drug.calculated_dose_unit}
                    </div>
                  )}
                </td>
                <td>{drug.route}</td>
                <td>{drug.days?.join(', ')}</td>
                <td>
                  {drug.duration_minutes && (
                    <div>Over {formatDuration(drug.duration_minutes)}</div>
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
                    <div className="special">{renderWithSuperscripts(drug.special_instructions)}</div>
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
      {(hasCriticalWarnings || isAiGenerated) && (
        <div className="verification-required-box" style={{
          background: '#fff3cd',
          border: '2px solid #ffc107',
          padding: '15px',
          margin: '20px 0',
          borderRadius: '4px'
        }}>
          <h3 style={{ margin: '0 0 10px 0' }}>⚠️ Pharmacist/Prescriber Verification Required</h3>
          <p style={{ marginBottom: '10px' }}>
            {isAiGenerated ?
              "This protocol was extracted by AI. " :
              "Critical safety warnings are present. "
            }
            You must verify all doses against the original protocol source before printing.
          </p>
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', fontWeight: 'bold' }}>
            <input
              type="checkbox"
              checked={hasAcknowledged}
              onChange={e => setHasAcknowledged(e.target.checked)}
              style={{ width: '20px', height: '20px', marginRight: '10px' }}
            />
            I certify that I have independently verified this protocol and it is safe for administration.
          </label>
        </div>
      )}

      <div className="display-actions">
        <button className="btn-secondary" onClick={onBack}>
          ← Modify Selection
        </button>
        <button
          className="btn-primary"
          onClick={handlePrint}
          disabled={!canPrint}
          style={{ opacity: canPrint ? 1 : 0.5, cursor: canPrint ? 'pointer' : 'not-allowed' }}
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M19 8H5c-1.66 0-3 1.34-3 3v6h4v4h12v-4h4v-6c0-1.66-1.34-3-3-3zm-3 11H8v-5h8v5zm3-7c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1zm-1-9H6v4h12V3z" />
          </svg>
          {canPrint ? "Print Protocol" : "Verify to Print"}
        </button>
        <button className="btn-success" onClick={onReset}>
          New Protocol
        </button>
      </div>

      {/* Printable Content */}
      <div ref={printRef} className="protocol-content">
        {/* Disclaimer Banner */}
        <div className="disclaimer-box">
          <h4>
            <svg viewBox="0 0 24 24" width="20" height="20" fill="#b45309">
              <path d="M12 2L1 21h22L12 2zm0 3.99L19.53 19H4.47L12 5.99zM11 10v4h2v-4h-2zm0 6v2h2v-2h-2z" />
            </svg>
            Clinical Decision Support Only
          </h4>
          <p>{protocol.disclaimer || "This protocol is for decision support only. Independent verification by prescriber and pharmacist is REQUIRED before administration."}</p>
        </div>

        {/* Treatment Delay Warning */}
        {protocol.treatment_delay_recommended && (
          <div className="delay-banner">
            <svg viewBox="0 0 24 24" width="24" height="24" fill="#c53030">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
            </svg>
            <div>
              <strong>⚠️ TREATMENT DELAY RECOMMENDED</strong>
              <ul>
                {(protocol.delay_reasons || []).map((reason, i) => (
                  <li key={i}>{reason}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        <div className="print-header">
          <h1>{protocol.protocol_code}</h1>
          <div className="subtitle">{protocol.protocol_name}</div>
          <div className="meta">
            <span>Cycle {protocol.cycle_number} of {protocol.total_cycles}</span>
            <span> | </span>
            <span>{protocol.cycle_length_days}-day cycle</span>
            <span> | </span>
            <span>BSA: {protocol.patient_bsa} m²{protocol.patient_bsa_capped && ` (capped from ${protocol.patient_bsa_actual} m²)`}</span>
            <span> | </span>
            <span>Weight: {protocol.patient_weight} kg</span>
            {protocol.patient_age && (
              <>
                <span> | </span>
                <span>Age: {protocol.patient_age} years</span>
              </>
            )}
            {protocol.patient_performance_status !== undefined && protocol.patient_performance_status !== null && (
              <>
                <span> | </span>
                <span>ECOG: {protocol.patient_performance_status}</span>
              </>
            )}
          </div>
        </div>

        {/* Warnings */}
        {protocol.warnings && protocol.warnings.length > 0 && (
          <div className="section warnings-section">
            <h2>⚠️ Warnings & Alerts</h2>
            {protocol.warnings.map((warning, i) => (
              <div key={i} className={`warning ${warning.level}`}>
                <strong>{warning.level.toUpperCase()}:</strong> {renderWithSuperscripts(warning.message)}
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

        {/* Chemotherapy Drugs — hidden for blinatumomab (bag schedule shown instead) */}
        {!(protocol.blinatumomab_bag_schedule && protocol.blinatumomab_bag_schedule.length > 0) && (
          <DrugTable drugs={protocol.chemotherapy_drugs} title="Chemotherapy" />
        )}

        {/* Blinatumomab Bag-Change Schedule */}
        {protocol.blinatumomab_bag_schedule && protocol.blinatumomab_bag_schedule.length > 0 && (
          <div className="section">
            <h2>Blinatumomab — Alternating 72/96-Hour Bag Schedule</h2>

            {/* Critical safety box */}
            <div style={{ background: '#f8d7da', border: '2px solid #dc3545', borderRadius: 4, padding: '10px 14px', marginBottom: 8 }}>
              <strong style={{ color: '#721c24', fontSize: 13 }}>⛔ CRITICAL — DO NOT FLUSH LINE WHEN CHANGING BAGS</strong>
              <div style={{ color: '#721c24', fontSize: 12, marginTop: 4 }}>
                Flushing causes an inadvertent blinatumomab bolus — potentially fatal. Replace the entire IV line with every pump change. CADD pump only. Central venous access via a <strong>dedicated lumen</strong>.
              </div>
            </div>

            {/* Alternating schedule explanation */}
            <div style={{ background: '#fff8e1', border: '1px solid #f0ad4e', borderRadius: 4, padding: '8px 14px', marginBottom: 8, fontSize: 12 }}>
              <strong>Alternating bag schedule (per NHS protocol):</strong><br />
              ODD bags (1st, 3rd, 5th, 7th): pump programmed to <strong>stop after 72 hours</strong> — bag must then be <strong>DISCARDED</strong> (drug remains in bag).<br />
              EVEN bags (2nd, 4th, 6th, 8th): run for the full <strong>96 hours</strong>.<br />
              All bags prepared for 96h but only odd bags stop early. Ensure pump is set to correct stop time.
            </div>

            {/* Hospitalisation + line requirements */}
            <div style={{ background: '#d1ecf1', border: '1px solid #17a2b8', borderRadius: 4, padding: '8px 14px', marginBottom: 8, fontSize: 12 }}>
              <strong>Hospitalisation:</strong> Cycle 1 days 1–9 in-patient. Cycle 2 days 1–2 minimum in-patient. &nbsp;|&nbsp;
              <strong>Start day:</strong> Monday, Tuesday or Friday only. &nbsp;|&nbsp;
              <strong>Line:</strong> Polyolefin / PVC non-DEHP / EVA + 0.2 µm in-line filter.
            </div>

            <table>
              <thead>
                <tr>
                  <th style={{ width: '7%' }}>Bag</th>
                  <th style={{ width: '20%' }}>Date (Start → End)</th>
                  <th style={{ width: '13%' }}>Dose</th>
                  <th style={{ width: '14%' }}>Content</th>
                  <th style={{ width: '13%' }}>Volume / Rate</th>
                  <th style={{ width: '33%' }}>Run time</th>
                </tr>
              </thead>
              <tbody>
                {protocol.blinatumomab_bag_schedule.map((bag, i) => {
                  const isOdd = bag.bag_number % 2 === 1;
                  const rowBg = bag.dose_mcg_per_day === 9 ? '#fff8e1' : (isOdd ? '#fafafa' : 'white');
                  return (
                    <tr key={i} style={{ background: rowBg }}>
                      <td><strong>Bag {bag.bag_number}</strong><br /><span style={{ fontSize: 10, color: isOdd ? '#c0392b' : '#27ae60' }}>{isOdd ? '72h — DISCARD' : '96h — full run'}</span></td>
                      <td><strong>{bag.date_start}</strong> → <strong>{bag.date_end}</strong></td>
                      <td><strong>{bag.dose_mcg_per_day} mcg/day</strong></td>
                      <td style={{ fontSize: 11 }}>{bag.total_dose_mcg} mcg in {bag.total_volume_ml} ml NS 0.9%</td>
                      <td style={{ fontSize: 11 }}>{bag.total_volume_ml} ml @ <strong>{bag.rate_ml_per_hr} ml/hr</strong></td>
                      <td style={{ fontSize: 11, fontWeight: isOdd ? 'bold' : 'normal', color: isOdd ? '#c0392b' : 'inherit' }}>
                        {isOdd
                          ? `Set pump to STOP at 72 hours. Discard remaining volume. Replace IV line.`
                          : `Run full 96 hours. Replace IV line at change.`}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {/* Monitoring reminder */}
            <div style={{ background: '#e8f4fd', border: '1px solid #3498db', borderRadius: 4, padding: '8px 14px', marginTop: 8, fontSize: 12 }}>
              <strong>Before each cycle:</strong> FBC, U&amp;Es, LFTs on day 1 of each cycle. Hepatitis B, C and HIV serology prior to cycle 1.
              Neurological examination before starting therapy. Weekly writing test for neurotoxicity monitoring throughout.
            </div>
          </div>
        )}

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
                <li key={i}>{renderWithSuperscripts(req)}</li>
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
                <li key={i}>{renderWithSuperscripts(inst)}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Audit Trail */}
        <div className="audit-info">
          <span><strong>Generated:</strong> {protocol.generated_at ? new Date(protocol.generated_at).toLocaleString() : new Date().toLocaleString()}</span>
          <span><strong>Protocol Version:</strong> {protocol.protocol_version || 'N/A'}</span>
          <span><strong>System:</strong> SOPHIA by Jivana AI</span>
        </div>
      </div>
    </div>
  );
}
