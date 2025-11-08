/**
 * Analytics API
 * Handles frontend event logging for analytics tracking
 */

import { apiRequest } from "./client";

/**
 * Log frontend events for analytics tracking
 * Fails silently if analytics endpoint is unavailable
 * 
 * @param {string} eventType - Type of event to log (e.g., "quiz_completed", "unlock_click")
 * @param {Object} data - Additional event data to include
 * @returns {Promise<void>}
 */
export async function logEvent(eventType, data = {}) {
  try {
    await apiRequest("/events", "POST", { event: eventType, ...data });
  } catch (err) {
    // Analytics failures should not break the app - fail silently
  }
}
