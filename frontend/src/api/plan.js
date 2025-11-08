/**
 * Trading Plan API functions
 * Handles all API calls related to plan creation, retrieval, and unlocking
 */

import { apiRequest } from "./client";

/**
 * Create a complete trading plan from quiz answers
 * Generates all 3 stages and stores them in the database
 * 
 * @param {Object} answers - Quiz answers object containing user's trading preferences
 * @returns {Promise<Object>} Plan object with plan_id and stages array
 */
export async function createPlan(answers) {
  return apiRequest("/plan", "POST", { answers });
}

/**
 * Generate summary (Stage 1 content) from quiz answers
 * Faster than createPlan as it only generates Stage 1 and uses fingerprint caching
 * 
 * @param {Object} answers - Quiz answers object
 * @returns {Promise<Object>} Summary object with plan_id, summary content, and persona
 */
export async function generateSummary(answers) {
  return apiRequest("/plan/summary", "POST", { answers });
}

/**
 * Get a specific trading plan by ID
 * Returns plan with tier-based access control (free users see Stage 1, pro users see all)
 * 
 * @param {string} planId - Unique plan identifier
 * @returns {Promise<Object>} Plan object with stages, tier, and metadata
 */
export async function getPlan(planId) {
  return apiRequest(`/plan/${planId}`, "GET");
}

/**
 * Start checkout session to unlock stages 2 and 3
 * Instant unlock mode - grants pro tier immediately without payment
 * 
 * @param {string} planId - Plan ID to unlock
 * @param {string} email - User email (optional, not used in instant unlock mode)
 * @param {string} userId - User identifier (can be "anon" for anonymous users)
 * @returns {Promise<Object>} Checkout response with success status and session_id
 */
export async function startCheckout(planId, email, userId) {
  return apiRequest("/checkout/session", "POST", {
    plan_id: planId,
    email: email || "",
    user_id: userId
  });
}

/**
 * Check payment status for a plan
 * Alias for getPlan - returns current plan with tier information
 * 
 * @param {string} planId - Plan ID to check
 * @returns {Promise<Object>} Plan object with tier information
 */
export async function checkPaymentStatus(planId) {
  return apiRequest(`/plan/${planId}`, "GET");
}

/**
 * Update plan stage progress (future feature)
 * Allows tracking user progress through stages
 * 
 * @param {string} planId - Plan ID
 * @param {Object} stageData - Stage progress data
 * @returns {Promise<Object>} Updated plan object
 */
export async function updatePlanStage(planId, stageData) {
  return apiRequest(`/plan/${planId}`, "PATCH", stageData);
}