import React, { useState, useEffect } from "react";
import { createPlan, generateSummary } from "../api/plan";
import { usePlan } from "../hooks/usePlan";
import { logEvent } from "../api/analytics";
import { useAuth } from "../contexts/AuthContext";

const Summary = ({ answers, onComplete, onUnlock, registerPlanRefresh }) => {
  const { userId } = useAuth();
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [planId, setPlanId] = useState(null);
  
  // Use the plan hook (without auto-fetch since we create the plan first)
  const { refreshPlan, clearPlan } = usePlan(planId, false);

  useEffect(() => {
    const generatePlan = async () => {
      try {
        setLoading(true);
        
        // First, generate summary (Stage 1) for faster display
        const summaryData = await generateSummary(answers);
        setPlanId(summaryData.plan_id);
        setSummary(summaryData.summary || "Your personalized trading plan has been created!");
        
        // Then create full plan in background (for Stages 2 & 3)
        // This ensures we have all stages ready when user unlocks
        createPlan(answers).catch(err => {
          console.warn("Background plan creation failed:", err);
          // Non-critical - summary is already displayed
        });
        
        setError(null);
      } catch (err) {
        console.error("Error generating summary:", err);
        // Fallback: try createPlan if generateSummary fails
        try {
          const planData = await createPlan(answers);
          setPlanId(planData.plan_id);
          const stage1Content = planData.stages.find(s => s.id === 1);
          setSummary(stage1Content ? stage1Content.content : "Your personalized trading plan has been created!");
          setError(null);
        } catch (fallbackErr) {
          console.error("Error creating plan (fallback):", fallbackErr);
          setError(fallbackErr.message || "Failed to create plan. Please try again. Make sure the backend server is running.");
          setPlanId(null);
        }
      } finally {
        setLoading(false);
      }
    };

    generatePlan();
  }, [answers]);

  // Register refresh callback when planId is available
  useEffect(() => {
    if (registerPlanRefresh && planId) {
      registerPlanRefresh(refreshPlan, clearPlan);
    }
  }, [registerPlanRefresh, planId, refreshPlan, clearPlan]);

  const handleContinue = () => {
    console.log("handleContinue called - planId:", planId, "error:", error, "onComplete:", typeof onComplete);
    
    if (!onComplete) {
      console.error("onComplete function is not provided!");
      return;
    }
    
    if (planId && !error) {
      console.log("Continuing to plan view with planId:", planId);
      try {
        onComplete(planId);
      } catch (err) {
        console.error("Error calling onComplete:", err);
      }
    } else {
      console.error("Cannot continue: planId=", planId, "error=", error);
    }
  };

  const handleUnlockClick = () => {
    console.log("=== UNLOCK BUTTON CLICKED ===");
    console.log("planId:", planId);
    console.log("error:", error);
    console.log("loading:", loading);
    console.log("onUnlock type:", typeof onUnlock);
    
    // Track unlock_click event
    logEvent("unlock_click", {
      plan_id: planId,
      user_id: userId || "anon"
    });
    
    if (loading) {
      alert("Please wait, your plan is still being generated...");
      return;
    }
    
    if (error) {
      alert("Error occurred. Please refresh the page and try again.");
      return;
    }
    
    if (!planId) {
      alert("Plan is not ready yet. Please wait...");
      return;
    }
    
    // Open unlock modal which will ask for email
    if (onUnlock) {
      console.log("Opening unlock modal...");
      onUnlock();
    } else {
      console.error("onUnlock function is not provided! Falling back to direct continue.");
      // Fallback: if onUnlock is not available, go directly to plan view
      handleContinue();
    }
  };

  if (loading) {
    return (
      <div className="card-stage">
        <div className="card-shell">
          <div className="card-surface">
            <div className="card-header">
              <div className="badge">Generating Your Plan</div>
              <h1>Creating Your Trading Path</h1>
              <p>Analyzing your responses and building your personalized plan...</p>
            </div>
            <div className="card-main" style={{ minHeight: '300px', position: 'relative' }}>
              <div className="loading-overlay" style={{ zIndex: 10 }}>
                <div className="loading-spinner"></div>
                <p style={{ 
                  fontSize: '1.05rem',
                  fontWeight: '600',
                  color: 'var(--accent)',
                  marginTop: '20px',
                  letterSpacing: '0.05em',
                  textTransform: 'uppercase',
                  position: 'relative',
                  zIndex: 11
                }}>
                  Creating Your Trading Path...
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card-stage">
      <div className="card-shell">
        <div className="card-surface">
          <div className="card-header">
            <div className="badge">Step 2 of 3</div>
            <h1>Your Trading Profile Summary</h1>
            <p>Review your personalized assessment</p>
          </div>

          <div className="card-main">
            {error && (
              <div className="error-text" style={{ 
                textAlign: 'center', 
                marginBottom: '20px',
                padding: '12px',
                background: 'rgba(255, 123, 156, 0.15)',
                border: '1px solid rgba(255, 123, 156, 0.3)',
                borderRadius: '12px'
              }}>
                ⚠️ {error}
              </div>
            )}

            <div className="summary-panel">
              {/* Summary Text */}
              <div className="summary-text" style={{ marginBottom: '32px' }}>
                {summary}
              </div>

              {/* Divider */}
              <div style={{
                height: '1px',
                background: 'linear-gradient(90deg, transparent, rgba(167, 139, 250, 0.3), transparent)',
                margin: '32px 0'
              }}></div>

              {/* Stages Grid - Horizontal Layout */}
              <div className="summary-stages-grid" style={{
                marginBottom: '32px'
              }}>
                {/* Stage 1 - FREE */}
                <div style={{
                  padding: '20px',
                  borderRadius: '18px',
                  background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(16, 185, 129, 0.1))',
                  border: '2px solid rgba(34, 197, 94, 0.3)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                    <span style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #10b981, #059669)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      fontWeight: '700',
                      fontSize: '1rem'
                    }}>1</span>
                    <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: '600', color: '#10b981' }}>
                      Stage 1: Foundation
                    </h3>
                  </div>
                  <span style={{
                    display: 'inline-block',
                    padding: '4px 10px',
                    borderRadius: '999px',
                    background: 'rgba(34, 197, 94, 0.2)',
                    border: '1px solid rgba(34, 197, 94, 0.3)',
                    color: '#10b981',
                    fontSize: '0.7rem',
                    fontWeight: '700',
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    marginBottom: '12px'
                  }}>✓ FREE</span>
                  <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.6' }}>
                    Master the fundamentals, risk management, and build your first strategy.
                  </p>
                </div>

                {/* Stage 2 - LOCKED */}
                <div style={{
                  padding: '20px',
                  borderRadius: '18px',
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '2px solid rgba(255, 123, 156, 0.3)',
                  position: 'relative',
                  opacity: 0.7
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                    <span style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      background: 'rgba(255, 123, 156, 0.25)',
                      border: '1px solid rgba(255, 123, 156, 0.5)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#ff7b9c',
                      fontWeight: '700',
                      fontSize: '1rem'
                    }}>2</span>
                    <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                      Stage 2: Strategy
                    </h3>
                  </div>
                  <span style={{
                    display: 'inline-block',
                    padding: '4px 10px',
                    borderRadius: '999px',
                    background: 'rgba(255, 123, 156, 0.2)',
                    border: '1px solid rgba(255, 123, 156, 0.4)',
                    color: '#ff7b9c',
                    fontSize: '0.7rem',
                    fontWeight: '700',
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    marginBottom: '12px'
                  }}>🔒 LOCKED</span>
                  <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.6' }}>
                    Advanced strategies, backtesting, and optimization frameworks.
                  </p>
                </div>

                {/* Stage 3 - LOCKED */}
                <div style={{
                  padding: '20px',
                  borderRadius: '18px',
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '2px solid rgba(255, 123, 156, 0.3)',
                  position: 'relative',
                  opacity: 0.7
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                    <span style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      background: 'rgba(255, 123, 156, 0.25)',
                      border: '1px solid rgba(255, 123, 156, 0.5)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#ff7b9c',
                      fontWeight: '700',
                      fontSize: '1rem'
                    }}>3</span>
                    <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                      Stage 3: Automation
                    </h3>
                  </div>
                  <span style={{
                    display: 'inline-block',
                    padding: '4px 10px',
                    borderRadius: '999px',
                    background: 'rgba(255, 123, 156, 0.2)',
                    border: '1px solid rgba(255, 123, 156, 0.4)',
                    color: '#ff7b9c',
                    fontSize: '0.7rem',
                    fontWeight: '700',
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    marginBottom: '12px'
                  }}>🔒 LOCKED</span>
                  <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.6' }}>
                    Portfolio optimization and automated trading systems.
                  </p>
                </div>
              </div>

              {/* CTA Button */}
              <div className="summary-actions" style={{ 
                marginTop: '40px',
                marginBottom: '20px',
                width: '100%'
              }}>
                <button 
                  className="cta-button"
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    handleUnlockClick();
                  }}
                  style={{ 
                    width: '100%',
                    fontSize: '1.05rem',
                    padding: '16px 32px',
                    cursor: 'pointer',
                    display: 'block',
                    visibility: 'visible',
                    opacity: 1,
                    position: 'relative',
                    zIndex: 1000
                  }}
                >
                  View Full Plan & Unlock for $5 →
                </button>
                <p className="summary-disclaimer" style={{ marginTop: '12px', textAlign: 'center' }}>
                  ✓ One-time payment • ✓ Lifetime access • ✓ Educational only
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Summary;
