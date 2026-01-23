import React, { useState } from 'react';

export function ProtocolBrowser({ protocols, onSelect, selectedProtocol }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('all');

  const filteredProtocols = protocols.filter(p => {
    const matchesSearch = 
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.indication.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.drugs.some(d => d.toLowerCase().includes(searchTerm.toLowerCase()));
    
    return matchesSearch;
  });

  // Group protocols by indication type
  const groupedProtocols = {
    'Non-Hodgkin Lymphoma': filteredProtocols.filter(p => 
      p.indication.toLowerCase().includes('non-hodgkin') || 
      p.indication.toLowerCase().includes('nhl')
    ),
    'Hodgkin Lymphoma': filteredProtocols.filter(p => 
      p.indication.toLowerCase().includes('hodgkin') && 
      !p.indication.toLowerCase().includes('non-hodgkin')
    ),
    'Relapsed/Refractory': filteredProtocols.filter(p => 
      p.indication.toLowerCase().includes('relapsed') || 
      p.indication.toLowerCase().includes('refractory')
    ),
    'Other': filteredProtocols.filter(p => {
      const ind = p.indication.toLowerCase();
      return !ind.includes('hodgkin') && !ind.includes('relapsed') && !ind.includes('refractory');
    })
  };

  return (
    <div className="protocol-browser">
      <div className="browser-header">
        <h2>Select Treatment Protocol</h2>
        <p>Choose from {protocols.length} available protocols</p>
      </div>

      <div className="search-bar">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
          <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
        </svg>
        <input
          type="text"
          placeholder="Search protocols, drugs, or indications..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        {searchTerm && (
          <button className="clear-search" onClick={() => setSearchTerm('')}>
            ×
          </button>
        )}
      </div>

      <div className="protocol-list">
        {filteredProtocols.length === 0 ? (
          <div className="no-results">
            <p>No protocols found matching "{searchTerm}"</p>
          </div>
        ) : (
          filteredProtocols.map(protocol => (
            <div
              key={protocol.id}
              className={`protocol-card ${selectedProtocol?.id === protocol.id ? 'selected' : ''}`}
              onClick={() => onSelect(protocol)}
            >
              <div className="protocol-card-header">
                <span className="protocol-code">{protocol.code}</span>
                <span className="protocol-cycles">{protocol.total_cycles} cycles × {protocol.cycle_length_days} days</span>
              </div>
              
              <h3 className="protocol-name">{protocol.name}</h3>
              
              <p className="protocol-indication">{protocol.indication}</p>
              
              <div className="protocol-drugs">
                {protocol.drugs.map((drug, i) => (
                  <span key={i} className="drug-tag">{drug}</span>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
