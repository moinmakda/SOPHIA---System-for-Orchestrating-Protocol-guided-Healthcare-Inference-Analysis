import React, { useState, useCallback, useEffect } from 'react';
import './FlexibleProtocolBuilder.css';
import { getAllDrugs, getCombinationTemplate, getAllCombinations, DRUG_LIBRARY } from '../data/drugLibrary';

/**
 * FlexibleProtocolBuilder - Allows doctors to:
 * 1. Drag-drop drugs to build custom combinations (e.g., Aza alone, Ven alone, Aza+Ven)
 * 2. Edit doses, days, frequencies on the fly
 * 3. Add drugs from a pool or remove them
 * 4. Save custom protocol templates
 * 5. Build protocols from scratch using the drug library
 */
export function FlexibleProtocolBuilder({
  protocol,             // Optional: Protocol object containing drugs (if null, uses drug library)
  onSave,               // Callback when drugs are saved
  patientBSA,           // For dose calculations
}) {
  // Extract available drugs from protocol
  const extractDrugsFromProtocol = (proto) => {
    if (!proto) return [];
    
    const allDrugs = [];
    
    // Extract from main drugs
    if (proto.drugs && Array.isArray(proto.drugs)) {
      proto.drugs.forEach((drug, index) => {
        allDrugs.push({
          ...drug,
          drug_id: drug.drug_name?.toLowerCase().replace(/\s+/g, '_') || `drug_${index}`,
          category: 'main',
        });
      });
    }
    
    // Extract from premedications
    if (proto.premedications && Array.isArray(proto.premedications)) {
      proto.premedications.forEach((drug, index) => {
        allDrugs.push({
          ...drug,
          drug_id: drug.drug_name?.toLowerCase().replace(/\s+/g, '_') || `premed_${index}`,
          category: 'premedication',
        });
      });
    }
    
    // Extract from take_home_medications
    if (proto.take_home_medications && Array.isArray(proto.take_home_medications)) {
      proto.take_home_medications.forEach((drug, index) => {
        allDrugs.push({
          ...drug,
          drug_id: drug.drug_name?.toLowerCase().replace(/\s+/g, '_') || `takehome_${index}`,
          category: 'take_home',
        });
      });
    }
    
    return allDrugs;
  };

  const [availableDrugs, setAvailableDrugs] = useState([]);
  const [selectedDrugs, setSelectedDrugs] = useState([]);
  const [draggedDrug, setDraggedDrug] = useState(null);
  const [editingDrug, setEditingDrug] = useState(null);
  const [showAddDrugModal, setShowAddDrugModal] = useState(false);

  // Initialize drugs from protocol OR drug library
  useEffect(() => {
    if (protocol) {
      // Use drugs from provided protocol
      const drugs = extractDrugsFromProtocol(protocol);
      setAvailableDrugs(drugs);

      // Pre-select main drugs
      const mainDrugs = drugs
        .filter(d => d.category === 'main')
        .map((d, i) => ({
          ...d,
          id: `${d.drug_id}_${Date.now()}_${i}`,
          isEdited: false,
        }));
      setSelectedDrugs(mainDrugs);
    } else {
      // Use standalone drug library - build from scratch
      const libraryDrugs = getAllDrugs();
      setAvailableDrugs(libraryDrugs);
      // Start with empty regimen - user builds from scratch
      setSelectedDrugs([]);
    }
  }, [protocol]);

  // Notify parent of changes
  const handleDrugsChange = (newDrugs) => {
    setSelectedDrugs(newDrugs);
    if (onSave) {
      onSave(newDrugs);
    }
  };

  // Handle drag start
  const handleDragStart = (e, drug, fromPool = true) => {
    setDraggedDrug({ ...drug, fromPool });
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', drug.drug_id);
  };

  // Handle drag over
  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  // Handle drop on regimen area
  const handleDropOnRegimen = (e) => {
    e.preventDefault();
    if (draggedDrug && draggedDrug.fromPool) {
      // Add drug from pool to regimen
      const newDrug = {
        ...draggedDrug,
        id: `${draggedDrug.drug_id}_${Date.now()}`, // Unique instance ID
        isEdited: false,
      };
      handleDrugsChange([...selectedDrugs, newDrug]);
    }
    setDraggedDrug(null);
  };

  // Handle drop back to pool (remove from regimen)
  const handleDropOnPool = (e) => {
    e.preventDefault();
    if (draggedDrug && !draggedDrug.fromPool) {
      // Remove drug from regimen
      handleDrugsChange(selectedDrugs.filter(d => d.id !== draggedDrug.id));
    }
    setDraggedDrug(null);
  };

  // Handle reordering within regimen
  const handleDropOnDrug = (e, targetDrug) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!draggedDrug || draggedDrug.fromPool) return;
    
    const dragIndex = selectedDrugs.findIndex(d => d.id === draggedDrug.id);
    const dropIndex = selectedDrugs.findIndex(d => d.id === targetDrug.id);
    
    if (dragIndex === dropIndex) return;
    
    const newDrugs = [...selectedDrugs];
    newDrugs.splice(dragIndex, 1);
    newDrugs.splice(dropIndex, 0, draggedDrug);
    
    handleDrugsChange(newDrugs);
    setDraggedDrug(null);
  };

  // Remove drug from regimen
  const removeDrug = (drugId) => {
    handleDrugsChange(selectedDrugs.filter(d => d.id !== drugId));
  };

  // Start editing a drug
  const startEditing = (drug) => {
    setEditingDrug({ ...drug });
  };

  // Save drug edits
  const saveEdits = () => {
    if (!editingDrug) return;
    
    const updatedDrugs = selectedDrugs.map(d => 
      d.id === editingDrug.id 
        ? { ...editingDrug, isEdited: true } 
        : d
    );
    handleDrugsChange(updatedDrugs);
    setEditingDrug(null);
  };

  // Cancel editing
  const cancelEdits = () => {
    setEditingDrug(null);
  };

  // Update editing drug field
  const updateEditingField = (field, value) => {
    setEditingDrug(prev => ({ ...prev, [field]: value }));
  };

  // Calculate dose based on BSA
  const calculateDose = (drug) => {
    if (!patientBSA) return drug.dose;
    
    if (drug.dose_unit === 'mg/m²' || drug.dose_unit === 'mg/m2') {
      return Math.round(drug.dose * patientBSA * 100) / 100;
    }
    if (drug.dose_unit === 'mg/kg' && drug.weight_kg) {
      return Math.round(drug.dose * drug.weight_kg * 100) / 100;
    }
    return drug.dose;
  };

  // Drug pool item (available drugs to drag)
  const DrugPoolItem = ({ drug }) => {
    const isInRegimen = selectedDrugs.some(d => d.drug_id === drug.drug_id);
    
    return (
      <div
        className={`drug-pool-item ${isInRegimen ? 'in-regimen' : ''}`}
        draggable={!isInRegimen}
        onDragStart={(e) => handleDragStart(e, drug, true)}
      >
        <div className="drug-pool-icon">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M19 3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-2 10h-4v4h-2v-4H7v-2h4V7h2v4h4v2z"/>
          </svg>
        </div>
        <div className="drug-pool-info">
          <span className="drug-pool-name">{drug.drug_name}</span>
          <span className="drug-pool-dose">{drug.dose} {drug.dose_unit}</span>
        </div>
        {isInRegimen && (
          <span className="in-regimen-badge">Added</span>
        )}
      </div>
    );
  };

  // Drug item in the regimen (editable)
  const RegimenDrugItem = ({ drug, index }) => {
    const calculatedDose = calculateDose(drug);
    
    return (
      <div
        className={`regimen-drug-item ${drug.isEdited ? 'edited' : ''}`}
        draggable
        onDragStart={(e) => handleDragStart(e, drug, false)}
        onDragOver={handleDragOver}
        onDrop={(e) => handleDropOnDrug(e, drug)}
      >
        <div className="drug-order">
          <span className="order-number">{index + 1}</span>
          <div className="drag-handle">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
              <path d="M11 18c0 1.1-.9 2-2 2s-2-.9-2-2 .9-2 2-2 2 .9 2 2zm-2-8c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0-6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm6 4c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z"/>
            </svg>
          </div>
        </div>
        
        <div className="drug-main-info">
          <div className="drug-name-row">
            <span className="drug-name">{drug.drug_name}</span>
            {drug.isEdited && <span className="edited-badge">Modified</span>}
          </div>
          
          <div className="drug-details-row">
            <span className="detail-item">
              <strong>Dose:</strong> {drug.dose} {drug.dose_unit}
              {patientBSA && drug.dose_unit?.includes('m²') && (
                <span className="calculated"> = {calculatedDose} mg</span>
              )}
            </span>
            <span className="detail-item">
              <strong>Route:</strong> {drug.route}
            </span>
            <span className="detail-item">
              <strong>Days:</strong> {drug.days?.join(', ') || '1'}
            </span>
            {drug.frequency && (
              <span className="detail-item">
                <strong>Frequency:</strong> {drug.frequency}
              </span>
            )}
          </div>
          
          {drug.special_instructions && (
            <div className="drug-instructions">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="#666">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
              </svg>
              {drug.special_instructions}
            </div>
          )}
        </div>
        
        <div className="drug-actions">
          <button 
            className="btn-edit" 
            onClick={() => startEditing(drug)}
            title="Edit drug details"
          >
            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
              <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
            </svg>
          </button>
          <button 
            className="btn-remove" 
            onClick={() => removeDrug(drug.id)}
            title="Remove from regimen"
          >
            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
      </div>
    );
  };

  // Edit drug modal
  const EditDrugModal = () => {
    if (!editingDrug) return null;

    return (
      <div className="modal-overlay" onClick={cancelEdits}>
        <div className="edit-drug-modal" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h3>Edit {editingDrug.drug_name}</h3>
            <button className="btn-close" onClick={cancelEdits}>×</button>
          </div>
          
          <div className="modal-body">
            <div className="form-row">
              <div className="form-group">
                <label>Dose</label>
                <input
                  type="number"
                  step="0.1"
                  value={editingDrug.dose}
                  onChange={(e) => updateEditingField('dose', parseFloat(e.target.value) || 0)}
                />
              </div>
              <div className="form-group">
                <label>Dose Unit</label>
                <select
                  value={editingDrug.dose_unit}
                  onChange={(e) => updateEditingField('dose_unit', e.target.value)}
                >
                  <option value="mg">mg</option>
                  <option value="mg/m²">mg/m²</option>
                  <option value="mg/kg">mg/kg</option>
                  <option value="g">g</option>
                  <option value="g/m²">g/m²</option>
                  <option value="mcg">mcg</option>
                  <option value="units">units</option>
                  <option value="AUC">AUC</option>
                </select>
              </div>
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label>Route</label>
                <select
                  value={editingDrug.route}
                  onChange={(e) => updateEditingField('route', e.target.value)}
                >
                  <option value="IV infusion">IV infusion</option>
                  <option value="IV bolus">IV bolus</option>
                  <option value="Oral">Oral</option>
                  <option value="Subcutaneous">Subcutaneous</option>
                  <option value="IM">IM</option>
                </select>
              </div>
              <div className="form-group">
                <label>Duration (minutes)</label>
                <input
                  type="number"
                  value={editingDrug.duration_minutes || ''}
                  onChange={(e) => updateEditingField('duration_minutes', parseInt(e.target.value) || null)}
                  placeholder="e.g., 60"
                />
              </div>
            </div>
            
            <div className="form-row">
              <div className="form-group full-width">
                <label>Days (comma-separated)</label>
                <input
                  type="text"
                  value={editingDrug.days?.join(', ') || '1'}
                  onChange={(e) => {
                    const days = e.target.value
                      .split(',')
                      .map(d => parseInt(d.trim()))
                      .filter(d => !isNaN(d));
                    updateEditingField('days', days.length > 0 ? days : [1]);
                  }}
                  placeholder="e.g., 1, 2, 3"
                />
              </div>
            </div>
            
            <div className="form-row">
              <div className="form-group full-width">
                <label>Frequency</label>
                <select
                  value={editingDrug.frequency || ''}
                  onChange={(e) => updateEditingField('frequency', e.target.value)}
                >
                  <option value="">Once per day listed</option>
                  <option value="Once daily">Once daily</option>
                  <option value="Twice daily">Twice daily</option>
                  <option value="Three times daily">Three times daily</option>
                  <option value="Four times daily">Four times daily</option>
                  <option value="Every 6 hours">Every 6 hours</option>
                  <option value="Every 8 hours">Every 8 hours</option>
                  <option value="Every 12 hours">Every 12 hours</option>
                  <option value="Weekly">Weekly</option>
                </select>
              </div>
            </div>
            
            <div className="form-row">
              <div className="form-group full-width">
                <label>Diluent</label>
                <input
                  type="text"
                  value={editingDrug.diluent || ''}
                  onChange={(e) => updateEditingField('diluent', e.target.value)}
                  placeholder="e.g., Sodium chloride 0.9%"
                />
              </div>
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label>Diluent Volume (ml)</label>
                <input
                  type="number"
                  value={editingDrug.diluent_volume_ml || ''}
                  onChange={(e) => updateEditingField('diluent_volume_ml', parseInt(e.target.value) || null)}
                  placeholder="e.g., 250"
                />
              </div>
              <div className="form-group">
                <label>Max Dose</label>
                <input
                  type="number"
                  step="0.1"
                  value={editingDrug.max_dose || ''}
                  onChange={(e) => updateEditingField('max_dose', parseFloat(e.target.value) || null)}
                  placeholder="e.g., 2"
                />
              </div>
            </div>
            
            <div className="form-row">
              <div className="form-group full-width">
                <label>Special Instructions</label>
                <textarea
                  value={editingDrug.special_instructions || ''}
                  onChange={(e) => updateEditingField('special_instructions', e.target.value)}
                  rows={3}
                  placeholder="Enter any special instructions..."
                />
              </div>
            </div>
          </div>
          
          <div className="modal-footer">
            <button className="btn-secondary" onClick={cancelEdits}>Cancel</button>
            <button className="btn-primary" onClick={saveEdits}>Save Changes</button>
          </div>
        </div>
      </div>
    );
  };

  // Quick add drug templates - use combination library
  const commonCombinations = protocol
    ? [
        { name: 'Aza Only', drugs: ['azacitidine'] },
        { name: 'Ven Only', drugs: ['venetoclax'] },
        { name: 'Aza + Ven', drugs: ['azacitidine', 'venetoclax'] },
        { name: 'Aza + Ven + Gilteritinib', drugs: ['azacitidine', 'venetoclax', 'gilteritinib'] },
      ]
    : getAllCombinations();

  const applyQuickCombination = (combo) => {
    const drugIds = protocol ? combo.drugs : combo.drugs;

    const newDrugs = drugIds
      .map(drugId => {
        // First try to find in available drugs
        let drug = availableDrugs.find(d =>
          d.drug_id?.toLowerCase() === drugId.toLowerCase() ||
          d.drug_name?.toLowerCase() === drugId.toLowerCase()
        );

        // If not found and we're using drug library, try to get from DRUG_LIBRARY
        if (!drug && !protocol) {
          drug = DRUG_LIBRARY[drugId];
        }

        if (drug) {
          return {
            ...drug,
            id: `${drug.drug_id}_${Date.now()}_${Math.random()}`,
            isEdited: false,
          };
        }
        return null;
      })
      .filter(Boolean);

    handleDrugsChange(newDrugs);
  };

  return (
    <div className="flexible-protocol-builder">
      <div className="builder-header">
        <h2>
          <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
            <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
          </svg>
          Flexible Protocol Builder
        </h2>
        <p>Drag drugs to build your regimen, or use quick combinations</p>
      </div>

      {/* Quick Combinations */}
      <div className="quick-combinations">
        <span className="quick-label">Quick Add:</span>
        {commonCombinations.map((combo, i) => (
          <button
            key={i}
            className="quick-combo-btn"
            onClick={() => applyQuickCombination(combo)}
            title={combo.description || ''}
          >
            {combo.name}
          </button>
        ))}
        {!protocol && (
          <span className="quick-hint">⭐ Building from scratch - No protocol selected</span>
        )}
      </div>

      <div className="builder-container">
        {/* Drug Pool (Available Drugs) */}
        <div 
          className="drug-pool"
          onDragOver={handleDragOver}
          onDrop={handleDropOnPool}
        >
          <div className="pool-header">
            <h3>Available Drugs</h3>
            <span className="pool-hint">Drag to add →</span>
          </div>
          <div className="pool-list">
            {availableDrugs.map((drug, i) => (
              <DrugPoolItem key={i} drug={drug} />
            ))}
          </div>
        </div>

        {/* Current Regimen */}
        <div 
          className={`current-regimen ${draggedDrug?.fromPool ? 'drop-target' : ''}`}
          onDragOver={handleDragOver}
          onDrop={handleDropOnRegimen}
        >
          <div className="regimen-header">
            <h3>Current Regimen</h3>
            <span className="drug-count">{selectedDrugs.length} drug(s)</span>
          </div>
          
          {selectedDrugs.length === 0 ? (
            <div className="empty-regimen">
              <svg viewBox="0 0 24 24" width="48" height="48" fill="#ccc">
                <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
              </svg>
              <p>Drag drugs here to build your regimen</p>
              <p className="hint">Or use the quick combinations above</p>
            </div>
          ) : (
            <div className="regimen-list">
              {selectedDrugs.map((drug, index) => (
                <RegimenDrugItem key={drug.id} drug={drug} index={index} />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Save Template Option */}
      {onSave && selectedDrugs.length > 0 && (
        <div className="save-template-section">
          <button 
            className="btn-save-template"
            onClick={() => onSave(selectedDrugs)}
          >
            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
              <path d="M17 3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V7l-4-4zm-5 16c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3zm3-10H5V5h10v4z"/>
            </svg>
            Save as Custom Template
          </button>
        </div>
      )}

      <EditDrugModal />
    </div>
  );
}

export default FlexibleProtocolBuilder;
