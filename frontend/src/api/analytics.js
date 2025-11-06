import { apiRequest } from "./client";

/**
 * Log frontend events (optional analytics)
 */
export async function logEvent(eventType, data = {}) {
  try {
    await apiRequest("/events", "POST", { event: eventType, ...data });
  } catch (err) {
    console.warn("Analytics error:", err.message);
  }
}
