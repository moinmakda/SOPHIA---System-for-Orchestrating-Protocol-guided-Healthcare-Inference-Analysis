import React from 'react';

export function Header({ onReset, onAdminOpen }) {
  return (
    <header className="header">
      <div className="header-content">
        <div className="logo" onClick={onReset}>
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
          <button className="nav-btn" onClick={onReset}>
            <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
              <path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z"/>
            </svg>
            New Protocol
          </button>
          {onAdminOpen && (
            <button className="nav-btn admin-btn" onClick={onAdminOpen}>
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
              </svg>
              Admin
            </button>
          )}
        </nav>
      </div>
    </header>
  );
}
