// src/api/plan.js
import { apiRequest } from "./client";

// Create a plan from quiz answers
export async function createPlan(answers) {
  return apiRequest("/plan", "POST", { answers });
}

// Generate summary (Stage 1 content) from quiz answers
// Uses fingerprint caching for faster responses
export async function generateSummary(answers) {
  return apiRequest("/plan/summary", "POST", { answers });
}

// Get a specific plan by ID
export async function getPlan(planId) {
  return apiRequest(`/plan/${planId}`, "GET");
}

// Start checkout session (instant unlock - no payment)
export async function startCheckout(planId, email, userId) {
  return apiRequest("/checkout/session", "POST", {
    plan_id: planId,
    email: email || "",  // Optional - not used for instant unlock
    user_id: userId
  });
}

// Check payment status
export async function checkPaymentStatus(planId) {
  return apiRequest(`/plan/${planId}`, "GET");
}

// Optional: Update stage progress (for future)
export async function updatePlanStage(planId, stageData) {
  return apiRequest(`/plan/${planId}`, "PATCH", stageData);
}