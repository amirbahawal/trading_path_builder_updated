/**
 * Validation utilities for forms
 */

/**
 * Validate email format
 * @param {string} email - Email address to validate
 * @returns {Object} { isValid: boolean, error: string }
 */
export const validateEmail = (email) => {
  if (!email || email.trim() === "") {
    return {
      isValid: false,
      error: "Email is required"
    };
  }

  // Basic email regex pattern
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  
  if (!emailPattern.test(email)) {
    return {
      isValid: false,
      error: "Please enter a valid email address"
    };
  }

  // Check for common typos
  const commonTypos = ['@gmail.con', '@yahoo.con', '@hotmail.con'];
  const hasTypo = commonTypos.some(typo => email.toLowerCase().includes(typo));
  
  if (hasTypo) {
    return {
      isValid: false,
      error: "Did you mean .com instead of .con?"
    };
  }

  return {
    isValid: true,
    error: null
  };
};

/**
 * Validate 6-digit code format
 * @param {string} code - Code to validate
 * @returns {Object} { isValid: boolean, error: string }
 */
export const validateCode = (code) => {
  if (!code || code.trim() === "") {
    return {
      isValid: false,
      error: "Code is required"
    };
  }

  // Remove any spaces or dashes
  const cleanCode = code.replace(/[\s-]/g, '');

  if (cleanCode.length !== 6) {
    return {
      isValid: false,
      error: "Code must be 6 digits"
    };
  }

  if (!/^\d{6}$/.test(cleanCode)) {
    return {
      isValid: false,
      error: "Code must contain only numbers"
    };
  }

  return {
    isValid: true,
    error: null
  };
};

/**
 * Get friendly error message for common errors
 * @param {Error|string} error - Error object or message
 * @returns {string} User-friendly error message
 */
export const getFriendlyErrorMessage = (error) => {
  const errorMessage = typeof error === 'string' ? error : error?.message || '';

  const errorMap = {
    'Network request failed': 'Unable to connect to server. Please check your internet connection.',
    'Failed to fetch': 'Unable to reach the server. Please try again.',
    'Unauthorized': 'Your session has expired. Please log in again.',
    '401': 'Please log in to continue.',
    '403': 'You don\'t have permission to access this.',
    '404': 'The requested resource was not found.',
    '500': 'Server error. Please try again later.',
    'timeout': 'Request timed out. Please try again.'
  };

  // Check for matching error patterns
  for (const [key, message] of Object.entries(errorMap)) {
    if (errorMessage.toLowerCase().includes(key.toLowerCase())) {
      return message;
    }
  }

  // Return original message if no match
  return errorMessage || 'An unexpected error occurred. Please try again.';
};

/**
 * Format validation errors for display
 * @param {Object} errors - Object with field names and error messages
 * @returns {string} Formatted error message
 */
export const formatValidationErrors = (errors) => {
  if (!errors || Object.keys(errors).length === 0) {
    return '';
  }

  const errorMessages = Object.values(errors).filter(Boolean);
  
  if (errorMessages.length === 1) {
    return errorMessages[0];
  }

  return errorMessages.join('. ');
};

/**
 * Sanitize user input
 * @param {string} input - User input string
 * @returns {string} Sanitized string
 */
export const sanitizeInput = (input) => {
  if (!input) return '';
  
  return input
    .trim()
    .replace(/[<>]/g, '') // Remove potential HTML tags
    .substring(0, 500); // Limit length
};

/**
 * Check if string is empty or whitespace
 * @param {string} str - String to check
 * @returns {boolean} True if empty
 */
export const isEmpty = (str) => {
  return !str || str.trim() === '';
};

