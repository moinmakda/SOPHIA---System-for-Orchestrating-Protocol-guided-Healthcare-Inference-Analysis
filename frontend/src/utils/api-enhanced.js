/**
 * Enhanced API client for Chemotherapy Protocol Engine
 * Includes admin and Gemini integration endpoints
 */

const API_BASE = import.meta.env.VITE_API_URL || '';

class ApiClient {
  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    
    const config = {
      ...options,
    };

    // Only set Content-Type for non-FormData requests
    if (!(options.body instanceof FormData)) {
      config.headers = {
        'Content-Type': 'application/json',
        ...options.headers,
      };
    }

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error ${response.status}`);
      }
      
      return response.json();
    } catch (error) {
      if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
        throw new Error('Unable to connect to server. Please check if the API is running.');
      }
      throw error;
    }
  }

  // ============= PROTOCOL ENDPOINTS =============
  
  async getProtocols(search = null, category = null) {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (category) params.append('category', category);
    const queryString = params.toString();
    return this.request(`/api/v1/protocols${queryString ? '?' + queryString : ''}`);
  }

  async getProtocol(code) {
    return this.request(`/api/v1/protocols/${code}`);
  }

  async getProtocolDrugs(code) {
    return this.request(`/api/v1/protocol/${code}/drugs`);
  }

  async generateProtocol(request) {
    return this.request('/api/v1/protocol/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // ============= DRUG ENDPOINTS =============
  
  async getDrugs(category = null) {
    const params = category ? `?category=${encodeURIComponent(category)}` : '';
    return this.request(`/api/v1/drugs${params}`);
  }

  async getDrug(id) {
    return this.request(`/api/v1/drugs/${id}`);
  }

  // ============= CALCULATION ENDPOINTS =============
  
  async calculateBSA(heightCm, weightKg, method = 'mosteller') {
    return this.request(
      `/api/v1/calculate/bsa?height_cm=${heightCm}&weight_kg=${weightKg}&method=${method}`,
      { method: 'POST' }
    );
  }

  async calculateCrCl(creatinine, age, weightKg, female = false) {
    return this.request(
      `/api/v1/calculate/crcl?creatinine=${creatinine}&age=${age}&weight_kg=${weightKg}&female=${female}`,
      { method: 'POST' }
    );
  }

  // ============= ADMIN ENDPOINTS =============
  
  async getSystemStats() {
    return this.request('/api/v1/admin/stats');
  }

  async getCategories() {
    return this.request('/api/v1/admin/categories');
  }

  async uploadProtocol(file, diseaseCategory = 'lymphoma', forceReparse = false) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('disease_category', diseaseCategory);
    formData.append('force_reparse', forceReparse.toString());

    return this.request('/api/v1/admin/upload', {
      method: 'POST',
      body: formData,
    });
  }

  async ingestDirectory(directoryPath, diseaseCategory = 'lymphoma') {
    const params = new URLSearchParams({
      directory_path: directoryPath,
      disease_category: diseaseCategory
    });
    return this.request(`/api/v1/admin/ingest-directory?${params}`, {
      method: 'POST'
    });
  }

  async deleteProtocol(protocolId) {
    return this.request(`/api/v1/admin/protocol/${protocolId}`, {
      method: 'DELETE'
    });
  }

  async clearCache() {
    return this.request('/api/v1/admin/clear-cache', {
      method: 'POST'
    });
  }

  // ============= HEALTH CHECK =============
  
  async healthCheck() {
    return this.request('/api/v1/health');
  }
}

export const api = new ApiClient();

// Export for debugging
if (typeof window !== 'undefined') {
  window.chemoApi = api;
}
