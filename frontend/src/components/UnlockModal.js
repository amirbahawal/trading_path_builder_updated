import React, { useState, useEffect } from "react";
import { startCheckout } from "../api/plan";
import { useAuth } from "../contexts/AuthContext";
import { logEvent } from "../api/analytics";

const UnlockModal = ({ isOpen, onClose, onUnlockSuccess, planId, onNeedAuth }) => {
  const { userId, isLoggedIn } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

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
    // Track unlock_click event when user initiates unlock
    logEvent("unlock_click", {
      plan_id: planId,
      user_id: userId || "anon"
    });
    
    // If not logged in, require sign up first
    if (!isLoggedIn) {
      if (onNeedAuth) {
        onClose();
        setTimeout(() => onNeedAuth(), 300);
        return;
      } else {
        setError("Please sign up or sign in first to unlock your plan");
        return;
      }
    }
    
    if (!planId) {
      setError("Plan is not ready yet. Please try again in a moment.");
      return;
    }
    
    setLoading(true);
    setError("");
    
    try {
      // Use userId from auth context, or fallback identifier
      const userIdentifier = userId || "user";
      
      // Instant unlock - single click unlocks stages 2 and 3
      const result = await startCheckout(planId, "", userIdentifier);
      console.log("Unlock result:", result);
      
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
    } catch (err) {
      console.error("Unlock failed:", err);
      setError("Unable to unlock the plan. Please try again.");
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
          {!isLoggedIn && (
            <div style={{ 
              marginBottom: '16px', 
              padding: '12px',
              borderRadius: '8px',
              background: 'rgba(255, 215, 0, 0.15)',
              border: '1px solid rgba(255, 215, 0, 0.3)'
            }}>
              <p style={{ margin: '0 0 8px', color: '#ffd700', fontSize: '0.9rem', fontWeight: '600' }}>
                💡 Please sign up or sign in first
              </p>
              {onNeedAuth && (
                <button
                  onClick={() => {
                    onClose();
                    setTimeout(() => onNeedAuth(), 300);
                  }}
                  style={{
                    background: 'transparent',
                    border: '1px solid #ffd700',
                    color: '#ffd700',
                    padding: '6px 16px',
                    borderRadius: '6px',
                    fontSize: '0.85rem',
                    cursor: 'pointer',
                    width: '100%'
                  }}
                >
                  Sign Up / Sign In
                </button>
              )}
            </div>
          )}
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
};

export default UnlockModal;