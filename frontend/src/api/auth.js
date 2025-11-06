import { apiRequest } from "./client";

/**
 * Send login code to email
 */
export async function sendLoginCode(email) {
  return apiRequest("/auth/send-login-code", "POST", { email });
}

/**
 * Verify login code and get session token
 */
export async function verifyLoginCode(email, code) {
  return apiRequest("/auth/verify-login-code", "POST", { email, code });
}

/**
 * Check if user is logged in
 */
export async function checkLoginStatus() {
  return apiRequest("/auth/check-login", "GET");
}

/**
 * Send unlock code for $5 plan
 */
export async function sendUnlockCode(email) {
  return apiRequest("/auth/unlock-plan", "POST", { email });
}

/**
 * Complete unlock with verification code
 */
export async function completeUnlock(email, code) {
  return apiRequest("/auth/complete-unlock", "POST", { email, code });
}
