import { apiRequest } from "./client";
import { API_ENDPOINTS } from "./constants";

/**
 * Send quiz answers to create a trading plan
 * @param {Object} answers - Quiz answers object
 * @returns {Promise<Object>} Created plan data
 */
export async function sendAnswers(answers) {
  try {
    return await apiRequest(API_ENDPOINTS.PLAN, "POST", answers);
  } catch (error) {
    console.error("Error calling backend:", error);
    throw error;
  }
}

/**
 * Send magic link email for authentication
 * @param {string} email - User email address
 * @returns {Promise<Object>} Response data
 */
export async function sendMagicLink(email) {
  try {
    return await apiRequest(API_ENDPOINTS.AUTH_MAGIC_LINK, "POST", { email });
  } catch (error) {
    console.error("Error calling backend:", error);
    throw error;
  }
}

/**
 * Verify magic link token
 * @param {string} email - User email address
 * @param {string} token - Verification token
 * @returns {Promise<Object>} Verification response
 */
export async function verifyToken(email, token) {
  try {
    return await apiRequest(API_ENDPOINTS.AUTH_VERIFY, "POST", { email, token });
  } catch (error) {
    console.error("Error calling backend:", error);
    throw error;
  }
}

/**
 * Create checkout session for plan unlock
 * @param {string} planId - Plan ID
 * @param {string} userId - User ID
 * @param {string} sessionToken - Session authentication token
 * @returns {Promise<Object>} Checkout session data
 */
export async function createCheckoutSession(planId, userId, sessionToken) {
  try {
    // Note: This uses apiRequest which automatically adds Authorization header
    // We need to temporarily set the token for this request
    const originalToken = localStorage.getItem("trading_path_token");
    if (sessionToken) {
      localStorage.setItem("trading_path_token", sessionToken);
    }
    
    try {
      return await apiRequest(API_ENDPOINTS.CHECKOUT_SESSION, "POST", {
        plan_id: planId,
        user_id: userId,
      });
    } finally {
      // Restore original token
      if (originalToken) {
        localStorage.setItem("trading_path_token", originalToken);
      } else if (sessionToken) {
        localStorage.removeItem("trading_path_token");
      }
    }
  } catch (error) {
    console.error("Error calling backend:", error);
    throw error;
  }
}