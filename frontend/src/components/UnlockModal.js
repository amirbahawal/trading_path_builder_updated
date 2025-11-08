/**
 * Unlock Modal Component
 * Handles the unlock flow for stages 2 and 3
 * Instant unlock mode - grants pro tier immediately
 * 
 * @component
 * @param {boolean} isOpen - Whether modal is visible
 * @param {Function} onClose - Callback to close modal
 * @param {Function} onUnlockSuccess - Callback when unlock succeeds
 * @param {string} planId - Plan ID to unlock
 * @param {Function} onNeedAuth - Callback if authentication is needed (unused in instant unlock mode)
 */

import React, { useState, useEffect } from "react";
import { startCheckout } from "../api/plan";
import { useAuth } from "../contexts/AuthContext";
import { logEvent } from "../api/analytics";

const UnlockModal = React.memo(({ isOpen, onClose, onUnlockSuccess, planId }) => {
  const { userId } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [resolvedPlanId, setResolvedPlanId] = useState(null);
  
  // Try to resolve planId when modal opens
  useEffect(() => {
    if (isOpen && !planId) {
      // Try to get planId from localStorage or try to fetch the latest plan
      const storedPlanId = localStorage.getItem("current_plan_id");
      if (storedPlanId) {
        setResolvedPlanId(storedPlanId);
      }
    } else if (isOpen && planId) {
      setResolvedPlanId(planId);
      // Store for future use
      if (planId && planId !== "pending") {
        localStorage.setItem("current_plan_id", planId);
      }
    }
  }, [isOpen, planId]);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setSuccess(false);
      setError("");
    }
  }, [isOpen]);

  // Stripe return check removed - instant unlock only

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }
    return () => {
      document.body.style.overflow = 'auto';
    }
  }, [isOpen]);

  const handleUnlock = async () => {
    // Use resolved planId (from props, localStorage, or try to get from current plan)
    let currentPlanId = resolvedPlanId || planId;
    
    // If still no planId, try to get it from the most recent plan
    if (!currentPlanId || currentPlanId === "pending") {
      try {
        // Try to get plan from localStorage or fetch
        const storedPlanId = localStorage.getItem("current_plan_id");
        if (storedPlanId && storedPlanId !== "pending") {
          currentPlanId = storedPlanId;
        }
      } catch (e) {
        // Silently handle planId resolution errors
      }
    }
    
    // Track unlock_click event when user initiates unlock
    logEvent("unlock_click", {
      plan_id: currentPlanId,
      user_id: userId || "anon"
    });
    
    // Check if planId is available
    if (!currentPlanId || currentPlanId === "pending") {
      setError("Plan is not ready yet. Please wait a moment and try again.");
      return;
    }
    
    // Instant unlock - no login required (mock payment mode)
    setLoading(true);
    setError("");
    
    try {
      // Use "anon" as user_id if not logged in (instant unlock without auth)
      const userIdentifier = userId || "anon";
      
      // Instant unlock - single click unlocks stages 2 and 3
      const result = await startCheckout(currentPlanId, "", userIdentifier);
      
      if (result && result.success) {
        // Immediate success
        setSuccess(true);
        
        // Show success message briefly, then call callback
        setTimeout(() => {
          if (onUnlockSuccess) {
            onUnlockSuccess(result);
          }
          // Reset state
          setError("");
          setSuccess(false);
        }, 1500);
      } else {
        throw new Error(result?.message || "Unlock failed");
      }
    } catch (err) {
      console.error("Unlock failed:", err);
      setError(err.message || "Unable to unlock the plan. Please try again.");
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setError("");
      setSuccess(false);
      onClose();
    }
  };

  if (!isOpen) return null;

  // Success state
  if (success) {
    return (
      <div className="modal-overlay">
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="modal-body" style={{ textAlign: 'center', padding: '40px 24px' }}>
            <div style={{
              fontSize: '4rem',
              marginBottom: '16px',
              animation: 'bounce 0.5s ease-in-out'
            }}>
              ✅
            </div>
            <h2 style={{ 
              margin: '0 0 12px', 
              color: '#76f7bf',
              fontSize: '1.8rem' 
            }}>
              Plan Unlocked!
            </h2>
            <p style={{ 
              margin: '0', 
              color: 'var(--text-secondary)',
              fontSize: '1.05rem' 
            }}>
              All stages are now available. Refreshing your plan...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div
        className="modal-content"
        onClick={e => e.stopPropagation()}
        role="dialog" aria-modal="true" aria-labelledby="unlockModalTitle"
        tabIndex={-1}
        onKeyDown={e => {
          if (e.key === 'Escape') handleClose();
          if (e.key === 'Enter') handleUnlock();
        }}
      >
        <div className="modal-header"><h2 id="unlockModalTitle">Unlock Full Plan - $5</h2>
          <button className="modal-close" onClick={handleClose} disabled={loading}>×</button>
        </div>
        
        <div className="modal-body">
          <p style={{ marginBottom: '20px', fontSize: '1rem' }}>
            Click below to unlock the full plan and access all stages (Stages 2 & 3):
          </p>
          
          <button 
            className="button-primary" 
            onClick={handleUnlock}
            disabled={loading}
            style={{
              width: '100%',
              padding: '14px 28px',
              fontSize: '1.05rem',
              fontWeight: '700'
            }}
          >
            {loading ? "Unlocking..." : "Unlock Full Plan ($5)"}
          </button>
          
          {error && (
            <div style={{
              padding: '12px',
              marginTop: '12px',
              borderRadius: '8px',
              background: 'rgba(255, 123, 156, 0.15)',
              border: '1px solid rgba(255, 123, 156, 0.3)',
              color: '#ff7b9c',
              fontSize: '0.9rem'
            }}>
              ⚠️ {error}
            </div>
          )}
          
          <p style={{
            margin: '16px 0 0',
            fontSize: '0.85rem',
            color: 'rgba(167, 180, 217, 0.7)',
            textAlign: 'center'
          }}>
            Instant unlock • Lifetime access • All stages included
          </p>
        </div>
      </div>
    </div>
  );
});

UnlockModal.displayName = 'UnlockModal';

export default UnlockModal;