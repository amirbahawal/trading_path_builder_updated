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
      console.warn("usePlan: No planId provided");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      console.log(`Fetching plan: ${planId}`);
      const data = await getPlan(planId);
      setPlan(data);
      setLastFetchTime(Date.now());
      console.log(`Plan fetched successfully:`, data);
      return data;
    } catch (err) {
      console.error("Error fetching plan:", err);
      setError(err.message || "Failed to load plan");
      return null;
    } finally {
      setLoading(false);
    }
  }, [planId]);

  /**
   * Refresh plan data (force refetch)
   */
  const refreshPlan = useCallback(async () => {
    console.log("Refreshing plan data...");
    return await fetchPlan();
  }, [fetchPlan]);

  /**
   * Clear plan data (useful on logout)
   */
  const clearPlan = useCallback(() => {
    setPlan(null);
    setError(null);
    setLastFetchTime(null);
    console.log("Plan data cleared");
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
   */
  useEffect(() => {
    if (autoFetch && planId) {
      fetchPlan();
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

