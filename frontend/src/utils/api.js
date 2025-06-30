import { API_BASE_URL } from '../config';

/**
 * Make an authenticated API request
 * @param {string} endpoint - API endpoint (without base URL)
 * @param {Object} options - Fetch options
 * @param {string} token - Authentication token
 * @returns {Promise} - Fetch response
 */
export const authenticatedFetch = async (endpoint, options = {}, token = null) => {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers = {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true',
    ...options.headers
  };

  // Add authorization header if token is provided
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config = {
    ...options,
    headers
  };

  try {
    const response = await fetch(url, config);
    
    // Handle 401 Unauthorized - token might be expired
    if (response.status === 401) {
      // Clear token from localStorage
      localStorage.removeItem('authToken');
      // Redirect to login or trigger logout
      window.location.reload();
      throw new Error('Authentication failed');
    }
    
    return response;
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
};

/**
 * Make a GET request
 * @param {string} endpoint - API endpoint
 * @param {string} token - Authentication token
 * @returns {Promise} - JSON response
 */
export const apiGet = async (endpoint, token = null) => {
  const response = await authenticatedFetch(endpoint, { method: 'GET' }, token);
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return response.json();
};

/**
 * Make a POST request
 * @param {string} endpoint - API endpoint
 * @param {Object} data - Request body
 * @param {string} token - Authentication token
 * @returns {Promise} - JSON response
 */
export const apiPost = async (endpoint, data, token = null) => {
  const response = await authenticatedFetch(endpoint, {
    method: 'POST',
    body: JSON.stringify(data)
  }, token);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
  
  return response.json();
};

/**
 * Make a PUT request
 * @param {string} endpoint - API endpoint
 * @param {Object} data - Request body
 * @param {string} token - Authentication token
 * @returns {Promise} - JSON response
 */
export const apiPut = async (endpoint, data, token = null) => {
  const response = await authenticatedFetch(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data)
  }, token);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
  
  return response.json();
};

/**
 * Make a DELETE request
 * @param {string} endpoint - API endpoint
 * @param {string} token - Authentication token
 * @returns {Promise} - Response
 */
export const apiDelete = async (endpoint, token = null) => {
  const response = await authenticatedFetch(endpoint, { method: 'DELETE' }, token);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
  
  return response;
}; 