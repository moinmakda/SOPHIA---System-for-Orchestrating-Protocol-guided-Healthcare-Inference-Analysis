import React, { useState } from 'react';

// Protocols that have been fully validated and are live
const LIVE_PROTOCOLS = new Set(['LYMPHOMA-RCHOP21', 'HAEM-BLINA-34DAY']);

export function ProtocolBrowser({ protocols, onSelect, selectedProtocol }) {
  const [searchTerm, setSearchTerm] = useState('');

  const liveProtocols = protocols.filter(p => LIVE_PROTOCOLS.has(p.code));
  const totalProtocols = protocols.length;
  const underDevelopmentCount = totalProtocols - liveProtocols.length;

  const filteredLive = liveProtocols.filter(p =>
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.indication.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.drugs.some(d => d.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="protocol-browser">
      <div className="browser-header">
        <h2>Select Treatment Protocol</h2>
        <p>Choose a protocol to generate a dosing plan</p>
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
          <button className="clear-search" onClick={() => setSearchTerm('')}>×</button>
        )}
      </div>

      <div className="protocol-list">
        {filteredLive.length === 0 ? (
          <div className="no-results">
            <p>No live protocols match "{searchTerm}"</p>
          </div>
        ) : (
          filteredLive.map(protocol => (
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

      {/* Under development notice */}
      <div style={{
        marginTop: 24,
        padding: '14px 18px',
        background: '#f5f5f5',
        border: '1px solid #e0e0e0',
        borderRadius: 6,
        color: '#757575',
        fontSize: 13,
        lineHeight: 1.5
      }}>
        <strong style={{ color: '#424242' }}>~{underDevelopmentCount} further protocols under development</strong>
        <br />
        Full haematology and oncology library is being validated against NHS PDFs before release.
        Contact the SOPHIA team to request prioritisation of a specific protocol.
      </div>
    </div>
  );
}
