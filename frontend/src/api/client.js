// src/api/client.js
// PRODUCTION MODE - REAL API ONLY (NO MOCK MODE)

import { API_CONFIG, STORAGE_KEYS, ERROR_MESSAGES } from "../constants";

const API_BASE_URL = API_CONFIG.BASE_URL;
const TOKEN_STORAGE_KEY = STORAGE_KEYS.AUTH_TOKEN;

/**
 * Get auth token from localStorage
 */
function getAuthToken() {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch (error) {
    console.error("Error getting auth token:", error);
    return null;
  }
}

/**
 * Clear auth data on logout or 401 error
 */
function clearAuthData() {
  try {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(STORAGE_KEYS.USER_ID);
    localStorage.removeItem(STORAGE_KEYS.EMAIL);
    localStorage.removeItem(STORAGE_KEYS.EXPIRES_AT);
  } catch (error) {
    console.error("Error clearing auth data:", error);
  }
}

/**
 * PRODUCTION API REQUEST - Real Backend Only
 * No mock mode fallback - errors are thrown and must be handled by caller
 * 
 * @param {string} endpoint - API endpoint path
 * @param {string} method - HTTP method (GET, POST, etc.)
 * @param {object} body - Request body (optional)
 * @param {number} timeoutMs - Request timeout in milliseconds (default: 30s, plan generation: 120s)
 */
export async function apiRequest(endpoint, method = "GET", body = null, timeoutMs = null) {
  const options = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  
  // Add Authorization header if token exists
  const token = getAuthToken();
  if (token) {
    options.headers["Authorization"] = `Bearer ${token}`;
  }
  
  if (body) options.body = JSON.stringify(body);

  // Determine timeout based on endpoint
  // Plan generation endpoints need longer timeout (120 seconds)
  let timeout = timeoutMs;
  if (!timeout) {
    if (endpoint.includes('/plan/summary') || endpoint === '/plan' || endpoint.startsWith('/plan/')) {
      timeout = 120000; // 120 seconds for plan generation
    } else {
      timeout = 30000; // 30 seconds for other requests
    }
  }

  try {
    // Add timeout for long-running requests
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);

    // Handle network errors (CORS, connection refused, etc.)
    if (!res.ok) {
      // Handle 401 Unauthorized - clear auth and notify user
      if (res.status === 401) {
        clearAuthData();
        window.dispatchEvent(new CustomEvent("auth:unauthorized"));
        throw new Error("Session expired. Please log in again.");
      }

      // Handle other HTTP errors
      let errorMessage = "An error occurred";
      try {
        const errorData = await res.json();
        // Handle both FastAPI error formats: {detail: "..."} and {detail: {...}}
        if (errorData.detail) {
          if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else if (errorData.detail.message) {
            errorMessage = errorData.detail.message;
          } else if (errorData.detail.error) {
            errorMessage = errorData.detail.error;
          }
        } else if (errorData.message) {
          errorMessage = errorData.message;
        } else {
          errorMessage = `HTTP ${res.status}: ${res.statusText}`;
        }
      } catch {
        errorMessage = `HTTP ${res.status}: ${res.statusText}`;
      }
      
      const error = new Error(errorMessage);
      error.status = res.status;
      throw error;
    }

    return await res.json();
  } catch (error) {
    // Handle timeout errors
    if (error.name === 'AbortError') {
      const timeoutSeconds = Math.round(timeout / 1000);
      const timeoutError = new Error(`Request timed out after ${timeoutSeconds} seconds. AI generation can take time. Please check if the backend server is running and try again.`);
      timeoutError.status = 0;
      timeoutError.isNetworkError = true;
      timeoutError.isTimeout = true;
      throw timeoutError;
    }
    
    // Handle network errors (CORS, fetch failures, etc.)
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      const networkError = new Error("Cannot connect to server. Please check if the backend is running.");
      networkError.status = 0;
      networkError.isNetworkError = true;
      throw networkError;
    }
    
    // Re-throw other errors - let caller handle it
    throw error;
  }
}

/**
 * Production-ready error handler
 * All components must handle their own errors
 */
export function handleApiError(error) {
  if (!error) return ERROR_MESSAGES.UNKNOWN_ERROR;
  
  if (error.message.includes("fetch")) {
    return ERROR_MESSAGES.CONNECTION_FAILED;
  }
  
  if (error.message.includes("Unauthorized")) {
    return ERROR_MESSAGES.UNAUTHORIZED;
  }
  
  if (error.status === 400) {
    return ERROR_MESSAGES.INVALID_REQUEST;
  }
  
  if (error.status === 403) {
    return ERROR_MESSAGES.ACCESS_DENIED;
  }
  
  if (error.status === 404) {
    return ERROR_MESSAGES.NOT_FOUND;
  }
  
  if (error.status === 429) {
    return ERROR_MESSAGES.TOO_MANY_REQUESTS;
  }
  
  if (error.status === 500) {
    return ERROR_MESSAGES.SERVER_ERROR;
  }
  
  return error.message || ERROR_MESSAGES.UNKNOWN_ERROR;
}