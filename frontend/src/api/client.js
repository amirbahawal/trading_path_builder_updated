// src/api/client.js
// PRODUCTION MODE - REAL API ONLY (NO MOCK MODE)

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

// Storage key for auth token
const TOKEN_STORAGE_KEY = "trading_path_token";

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
    localStorage.removeItem("trading_path_user_id");
    localStorage.removeItem("trading_path_email");
    localStorage.removeItem("trading_path_expires_at");
    console.log("Auth data cleared");
  } catch (error) {
    console.error("Error clearing auth data:", error);
  }
}

/**
 * PRODUCTION API REQUEST - Real Backend Only
 * No mock mode fallback - errors are thrown and must be handled by caller
 */
export async function apiRequest(endpoint, method = "GET", body = null) {
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

  try {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, options);

    // Handle 401 Unauthorized - clear auth and notify user
    if (res.status === 401) {
      console.error("401 Unauthorized - clearing auth data");
      clearAuthData();
      
      // Dispatch custom event for auth context to pick up
      window.dispatchEvent(new CustomEvent("auth:unauthorized"));
      
      throw new Error("Unauthorized - please log in again. Please refresh and try again.");
    }

    // Handle other HTTP errors
    if (!res.ok) {
      let errorMessage = "An error occurred";
      try {
        const errorData = await res.json();
        errorMessage = errorData.detail || errorData.message || `HTTP ${res.status}`;
      } catch {
        errorMessage = `HTTP ${res.status}: ${res.statusText}`;
      }
      
      const error = new Error(errorMessage);
      error.status = res.status;
      throw error;
    }

    return await res.json();
  } catch (error) {
    // Log error for debugging
    console.error(`API Error [${method} ${endpoint}]:`, error.message);
    
    // Re-throw error - let caller handle it
    throw error;
  }
}

/**
 * Production-ready error handler
 * All components must handle their own errors
 */
export function handleApiError(error) {
  if (!error) return "An unknown error occurred";
  
  if (error.message.includes("fetch")) {
    return "Connection failed. Is the server running? Backend must be running on http://127.0.0.1:8000";
  }
  
  if (error.message.includes("Unauthorized")) {
    return "Session expired. Please log in again.";
  }
  
  if (error.status === 400) {
    return "Invalid request. Please check your input.";
  }
  
  if (error.status === 403) {
    return "Access denied. You don't have permission to access this.";
  }
  
  if (error.status === 404) {
    return "Resource not found.";
  }
  
  if (error.status === 429) {
    return "Too many requests. Please wait a moment and try again.";
  }
  
  if (error.status === 500) {
    return "Server error. The backend is having issues. Please try again later.";
  }
  
  return error.message || "An unexpected error occurred";
}