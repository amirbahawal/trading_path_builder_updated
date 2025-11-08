import { useState, useEffect, useCallback } from "react";
import { getPlan } from "../api/plan";

/**
 * Custom hook for managing plan data with refresh capabilities
 * 
 * @param {string} planId - The ID of the plan to fetch
 * @param {boolean} autoFetch - Whether to automatically fetch on mount (default: true)
 * @returns {Object} Plan data and control functions
 */
export const usePlan = (planId, autoFetch = true) => {
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastFetchTime, setLastFetchTime] = useState(null);

  /**
   * Fetch plan data from API
   */
  const fetchPlan = useCallback(async () => {
    if (!planId) {
      return null;
    }

    // Clean planId: remove "plan-" prefix if present
    const cleanPlanId = planId.startsWith("plan-") ? planId.substring(5) : planId;

    setLoading(true);
    setError(null);

    try {
      const data = await getPlan(cleanPlanId);
      if (data) {
        setPlan(data);
        setLastFetchTime(Date.now());
        return data;
      } else {
        setError("Plan data is empty. The server returned no data.");
        return null;
      }
    } catch (err) {
      // Set user-friendly error message
      let errorMsg = "Failed to load plan.";
      if (err.message) {
        errorMsg = err.message;
      } else if (err.isNetworkError) {
        errorMsg = "Cannot connect to server. Please check if the backend is running.";
      } else if (err.status === 404) {
        errorMsg = "Plan not found. Please create a new plan.";
        // Clear invalid plan ID from localStorage to prevent repeated requests
        try {
          localStorage.removeItem("current_plan_id");
          localStorage.removeItem("planId");
        } catch (e) {
          // Ignore localStorage errors
        }
      } else if (err.status === 500) {
        errorMsg = "Server error. Please try again later.";
      }
      setError(errorMsg);
      return null;
    } finally {
      setLoading(false);
    }
  }, [planId]);

  /**
   * Refresh plan data (force refetch)
   */
  const refreshPlan = useCallback(async () => {
    return await fetchPlan();
  }, [fetchPlan]);

  /**
   * Clear plan data (useful on logout)
   */
  const clearPlan = useCallback(() => {
    setPlan(null);
    setError(null);
    setLastFetchTime(null);
  }, []);

  /**
   * Check if plan is unlocked (tier === "pro")
   */
  const isUnlocked = useCallback(() => {
    return plan?.tier === "pro";
  }, [plan]);

  /**
   * Get plan tier
   */
  const getTier = useCallback(() => {
    return plan?.tier || "free";
  }, [plan]);

  /**
   * Auto-fetch on mount if enabled
   * Only fetch if planId is valid (not empty, not "pending", not too short)
   */
  useEffect(() => {
    if (autoFetch && planId) {
      // Validate planId before fetching
      const cleanPlanId = planId.startsWith("plan-") ? planId.substring(5) : planId;
      
      // Skip if planId is clearly invalid (too short, empty, or "pending")
      if (cleanPlanId && cleanPlanId !== "pending" && cleanPlanId.length >= 8) {
        fetchPlan();
      } else {
        // Invalid planId - clear it and set error
        setError("Invalid plan ID. Please create a new plan.");
        setLoading(false);
        // Clear invalid plan ID from localStorage
        try {
          localStorage.removeItem("current_plan_id");
          localStorage.removeItem("planId");
        } catch (e) {
          // Ignore localStorage errors
        }
      }
    }
  }, [autoFetch, planId, fetchPlan]);

  return {
    plan,
    loading,
    error,
    lastFetchTime,
    fetchPlan,
    refreshPlan,
    clearPlan,
    isUnlocked,
    getTier
  };
};

export default usePlan;

