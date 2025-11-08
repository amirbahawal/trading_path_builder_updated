/**
 * Application-wide constants and configuration
 * Centralizes all magic numbers, strings, and configuration values
 */

/**
 * API Configuration
 */
export const API_CONFIG = {
  // Base URL for API requests
  // Priority: REACT_APP_API_URL > VITE_BACKEND_URL > default
  BASE_URL:
    process.env.REACT_APP_API_URL ||
    process.env.VITE_BACKEND_URL ||
    "http://127.0.0.1:8000",
};

/**
 * Storage Keys
 * Keys used for localStorage
 */
export const STORAGE_KEYS = {
  AUTH_TOKEN: "trading_path_token",
  USER_ID: "trading_path_user_id",
  EMAIL: "trading_path_email",
  EXPIRES_AT: "trading_path_expires_at",
  PLAN_ID: "planId",
};

/**
 * Authentication Configuration
 */
export const AUTH_CONFIG = {
  // Token expiration time (24 hours in milliseconds)
  TOKEN_EXPIRATION_MS: 24 * 60 * 60 * 1000,
};

/**
 * UI Configuration
 */
export const UI_CONFIG = {
  // Toast notification duration (milliseconds)
  TOAST_DURATION: 3000,
  
  // OTP expiration time (10 minutes in seconds)
  OTP_EXPIRATION_SECONDS: 600,
  
  // Resend OTP cooldown (60 seconds)
  OTP_RESEND_COOLDOWN: 60,
};

/**
 * API Endpoints
 * Centralized endpoint paths
 */
export const API_ENDPOINTS = {
  // Plan endpoints
  PLAN: "/plan",
  PLAN_BY_ID: (id) => `/plan/${id}`,
  
  // Auth endpoints
  AUTH_MAGIC_LINK: "/auth/magic-link",
  AUTH_VERIFY: "/auth/verify",
  AUTH_SEND_LOGIN_CODE: "/auth/send-login-code",
  AUTH_VERIFY_LOGIN_CODE: "/auth/verify-login-code",
  AUTH_UNLOCK_PLAN: "/auth/unlock-plan",
  AUTH_COMPLETE_UNLOCK: "/auth/complete-unlock",
  
  // Checkout endpoints
  CHECKOUT_SESSION: "/checkout/session",
  
  // Analytics endpoints
  ANALYTICS: "/analytics",
};

/**
 * Error Messages
 * Standardized error messages for API errors
 */
export const ERROR_MESSAGES = {
  CONNECTION_FAILED: "Connection failed. Is the server running?",
  UNAUTHORIZED: "Session expired. Please log in again.",
  INVALID_REQUEST: "Invalid request. Please check your input.",
  ACCESS_DENIED: "Access denied. You don't have permission to access this.",
  NOT_FOUND: "Resource not found.",
  TOO_MANY_REQUESTS: "Too many requests. Please wait a moment and try again.",
  SERVER_ERROR: "Server error. The backend is having issues. Please try again later.",
  UNKNOWN_ERROR: "An unexpected error occurred",
};

/**
 * Application Constants
 */
export const APP_CONSTANTS = {
  // OTP code length
  OTP_LENGTH: 6,
  
  // Maximum retry attempts for API calls
  MAX_RETRY_ATTEMPTS: 3,
  
  // Retry delay (milliseconds)
  RETRY_DELAY_MS: 1000,
};

