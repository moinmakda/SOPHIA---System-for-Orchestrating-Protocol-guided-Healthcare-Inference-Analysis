import React, { useState, useRef, useEffect } from 'react';
import { api } from '../utils/api';

export function AdminPanel({ onClose, onProtocolIngested }) {
  const [activeTab, setActiveTab] = useState('upload');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [stats, setStats] = useState(null);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('lymphoma');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadStats();
    loadCategories();
  }, []);

  const loadStats = async () => {
    try {
      const data = await api.getSystemStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await api.getCategories();
      setCategories(data.categories || []);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadResult({
        success: false,
        message: 'Only PDF files are supported'
      });
      return;
    }

    setUploading(true);
    setUploadResult(null);

    try {
      const result = await api.uploadProtocol(file, selectedCategory);
      setUploadResult(result);
      
      if (result.success) {
        loadStats();
        onProtocolIngested?.();
      }
    } catch (err) {
      setUploadResult({
        success: false,
        message: err.message || 'Upload failed'
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="admin-panel-overlay">
      <div className="admin-panel">
        <div className="admin-header">
          <h2>
            <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
              <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
            </svg>
            Admin Panel
          </h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="admin-tabs">
          <button 
            className={`tab ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
              <path d="M9 16h6v-6h4l-7-7-7 7h4zm-4 2h14v2H5z"/>
            </svg>
            Upload Protocol
          </button>
          <button 
            className={`tab ${activeTab === 'stats' ? 'active' : ''}`}
            onClick={() => setActiveTab('stats')}
          >
            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
            </svg>
            Statistics
          </button>
        </div>

        <div className="admin-content">
          {activeTab === 'upload' && (
            <div className="upload-section">
              <div className="upload-info">
                <h3>🤖 AI-Powered Protocol Ingestion</h3>
                <p>
                  Upload NHS chemotherapy protocol PDFs and SOPHIA's Gemini AI will automatically extract:
                </p>
                <ul>
                  <li>Protocol name, code, and indication</li>
                  <li>All drugs with doses, routes, and schedules</li>
                  <li>Pre-medications and supportive care</li>
                  <li>Dose modification rules</li>
                  <li>Monitoring requirements</li>
                </ul>
              </div>

              <div className="category-selector">
                <label>Disease Category:</label>
                <select 
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                >
                  {categories.map(cat => (
                    <option key={cat} value={cat}>
                      {cat.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </option>
                  ))}
                  <option value="breast_cancer">Breast Cancer</option>
                  <option value="lung_cancer">Lung Cancer</option>
                  <option value="colorectal">Colorectal Cancer</option>
                  <option value="leukemia">Leukemia</option>
                  <option value="myeloma">Multiple Myeloma</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div 
                className={`upload-zone ${dragActive ? 'drag-active' : ''} ${uploading ? 'uploading' : ''}`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                />
                
                {uploading ? (
                  <div className="upload-progress">
                    <div className="spinner"></div>
                    <p>Processing with Gemini AI...</p>
                    <span>This may take 30-60 seconds</span>
                  </div>
                ) : (
                  <>
                    <svg viewBox="0 0 24 24" width="48" height="48" fill="currentColor">
                      <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h7v5h5v11zM8 15.01l1.41 1.41L11 14.84V19h2v-4.16l1.59 1.59L16 15.01 12.01 11z"/>
                    </svg>
                    <p>Drag & drop protocol PDF here</p>
                    <span>or click to browse</span>
                  </>
                )}
              </div>

              {uploadResult && (
                <div className={`upload-result ${uploadResult.success ? 'success' : 'error'}`}>
                  {uploadResult.success ? (
                    <>
                      <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                      </svg>
                      <div>
                        <strong>Protocol Ingested Successfully!</strong>
                        <p>
                          <span className="code">{uploadResult.protocol_code}</span> - {uploadResult.protocol_name}
                        </p>
                        <p>{uploadResult.drugs_count} drugs extracted</p>
                      </div>
                    </>
                  ) : (
                    <>
                      <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                      </svg>
                      <div>
                        <strong>Ingestion Failed</strong>
                        <p>{uploadResult.message}</p>
                      </div>
                    </>
                  )}
                </div>
              )}

              {!stats?.gemini_configured && (
                <div className="warning-box">
                  <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                    <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
                  </svg>
                  <div>
                    <strong>Gemini API Not Configured</strong>
                    <p>Set the GEMINI_API_KEY environment variable to enable AI-powered PDF parsing.</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'stats' && stats && (
            <div className="stats-section">
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-value">{stats.total_protocols}</div>
                  <div className="stat-label">Total Protocols</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{stats.total_drugs}</div>
                  <div className="stat-label">Unique Drugs</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{stats.hardcoded_protocols}</div>
                  <div className="stat-label">Built-in Protocols</div>
                </div>
                <div className="stat-card">
                  <div className="stat-value">{stats.ingested_protocols}</div>
                  <div className="stat-label">Ingested Protocols</div>
                </div>
              </div>

              <div className="categories-section">
                <h3>Disease Categories</h3>
                {stats.categories && stats.categories.length > 0 ? (
                  <div className="category-list">
                    {stats.categories.map(cat => (
                      <div key={cat.category} className="category-item">
                        <span className="category-name">
                          {cat.category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                        <span className="category-count">{cat.protocol_count} protocols</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="no-data">No ingested protocols yet. Upload some PDFs to get started!</p>
                )}
              </div>

              <div className="system-info">
                <h3>System Information</h3>
                <div className="info-row">
                  <span>Gemini AI:</span>
                  <span className={stats.gemini_configured ? 'status-ok' : 'status-warn'}>
                    {stats.gemini_configured ? '✓ Configured' : '✗ Not Configured'}
                  </span>
                </div>
                {stats.last_updated && (
                  <div className="info-row">
                    <span>Last Updated:</span>
                    <span>{new Date(stats.last_updated).toLocaleString()}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
