/**
 * Summary Component
 * Displays Stage 1 summary after quiz completion
 * Shows locked stages 2 and 3 with unlock CTA
 * Handles plan generation and unlock flow
 * 
 * @component
 * @param {Object} answers - Quiz answers object
 * @param {Function} onComplete - Callback when user completes summary (navigates to plan view)
 * @param {Function} onUnlock - Unused parameter (kept for compatibility)
 * @param {Function} registerPlanRefresh - Callback to register plan refresh function
 */

import React, { useState, useEffect } from "react";
import { createPlan, generateSummary, startCheckout } from "../api/plan";
import { usePlan } from "../hooks/usePlan";
import { logEvent } from "../api/analytics";
import { useAuth } from "../contexts/AuthContext";
import { renderMarkdown } from "../utils/markdownRenderer";

const Summary = React.memo(({ answers, onComplete, onUnlock: _onUnlock, registerPlanRefresh }) => {
  const { userId } = useAuth();
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [planId, setPlanId] = useState(null);
  const [unlocking, setUnlocking] = useState(false);
  const [unlockProgress, setUnlockProgress] = useState("");
  const [showSuccess, setShowSuccess] = useState(false);
  const [toast, setToast] = useState(null);
  
  // Use the plan hook (without auto-fetch since we create the plan first)
  const { refreshPlan, clearPlan } = usePlan(planId, false);

  useEffect(() => {
    const generatePlan = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // First, try to generate summary (Stage 1) for faster display
        try {
          const summaryData = await generateSummary(answers);
          
          // Validate response
          if (!summaryData) {
            throw new Error("No data received from summary endpoint");
          }
          
          const newPlanId = summaryData.plan_id;
          const summaryContent = summaryData.summary;
          
          if (!newPlanId) {
            throw new Error("No plan_id received from summary endpoint");
          }
          
          if (!summaryContent || summaryContent.trim() === "") {
            throw new Error("Summary content is empty");
          }
          
          setPlanId(newPlanId);
          setSummary(summaryContent);
          // Store in localStorage immediately
          localStorage.setItem("current_plan_id", newPlanId);
          
          // Then create full plan in background (for Stages 2 & 3)
          // This ensures we have all stages ready when user unlocks
          createPlan(answers).catch((err) => {
            // Non-critical - summary is already displayed, background plan creation can fail silently
            // But log it for debugging
            console.warn("Background plan creation failed (non-critical):", err);
          });
          
          setError(null);
        } catch (summaryErr) {
          // If generateSummary fails, fallback to createPlan
          console.warn("generateSummary failed, trying createPlan fallback:", summaryErr);
          
          const planData = await createPlan(answers);
          
          if (!planData) {
            throw new Error("No data received from createPlan endpoint");
          }
          
          const newPlanId = planData.plan_id;
          
          if (!newPlanId) {
            throw new Error("No plan_id received from createPlan endpoint");
          }
          
          setPlanId(newPlanId);
          localStorage.setItem("current_plan_id", newPlanId);
          
          // Extract Stage 1 content from plan
          const stages = planData.stages || [];
          const stage1Content = stages.find(s => s.id === 1 || s.stage_number === 1);
          
          if (stage1Content && stage1Content.content) {
            setSummary(stage1Content.content);
          } else if (planData.overview_md) {
            // Fallback to overview_md if stage content not found
            setSummary(planData.overview_md);
          } else {
            setSummary("Your personalized trading plan has been created! Please proceed to view your plan.");
          }
          
          setError(null);
        }
      } catch (err) {
        // Final error handling
        let errorMessage = "Failed to create plan. Please try again.";
        
        if (err.isTimeout) {
          errorMessage = err.message || "Request timed out. AI generation can take 30-90 seconds. Please check if the backend server is running and try again.";
        } else if (err.isNetworkError) {
          errorMessage = "Cannot connect to server. Please check if the backend server is running.";
        } else if (err.message) {
          errorMessage = err.message;
        }
        
        console.error("Error generating plan:", err);
        setError(errorMessage);
        setPlanId(null);
        setSummary(""); // Clear summary on error
      } finally {
        // Always clear loading state, even on error
        setLoading(false);
      }
    };

    // Only generate if answers exist
    if (answers && Object.keys(answers).length > 0) {
      generatePlan();
    } else {
      setError("No quiz answers provided. Please complete the quiz first.");
      setLoading(false);
    }
  }, [answers]);

  // Register refresh callback when planId is available
  useEffect(() => {
    if (registerPlanRefresh && planId) {
      registerPlanRefresh(refreshPlan, clearPlan);
    }
  }, [registerPlanRefresh, planId, refreshPlan, clearPlan]);

  const handleUnlockClick = async () => {
    // Try to get planId from multiple sources
    let effectivePlanId = planId;
    
    // Fallback 1: Check localStorage
    if (!effectivePlanId) {
      const storedPlanId = localStorage.getItem("current_plan_id");
      if (storedPlanId && storedPlanId !== "pending" && storedPlanId !== "null") {
        effectivePlanId = storedPlanId;
        setPlanId(storedPlanId); // Update state for future use
      }
    }
    
    // Fallback 2: If still loading, wait a bit and try again
    if (!effectivePlanId && loading) {
      setToast({ type: 'info', message: 'Please wait, your plan is still being generated...', duration: 3000 });
      return;
    }
    
    // Final check
    if (!effectivePlanId) {
      setToast({ type: 'warning', message: 'Plan is not ready yet. Please wait a few seconds and try again.', duration: 4000 });
      return;
    }
    
    // Track unlock_click event
    logEvent("unlock_click", {
      plan_id: effectivePlanId,
      user_id: userId || "anon"
    });
    
    // Instant unlock - no email required, no modal, no auth check
    setUnlocking(true);
    setUnlockProgress("Initializing unlock...");
    setShowSuccess(false);
    
    try {
      // Use "anon" as user_id if not logged in (mock payment mode)
      const userIdentifier = userId || "anon";
      
      // Store planId in localStorage for future use
      localStorage.setItem("current_plan_id", effectivePlanId);
      
      // Step 1: Processing payment
      setUnlockProgress("Processing unlock...");
      await new Promise(resolve => setTimeout(resolve, 300));
      
      const result = await startCheckout(effectivePlanId, "", userIdentifier);
      
      if (result && result.success) {
        // Step 2: Unlock successful
        setUnlockProgress("Unlock successful!");
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // Step 3: Updating your plan
        setUnlockProgress("Updating your plan...");
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Refresh plan to get updated tier (stages 2 & 3 unlocked)
        // Wait a moment for database to be ready
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Refresh plan multiple times if needed (sometimes needs a moment)
        let refreshedPlan = null;
        for (let i = 0; i < 3; i++) {
          refreshedPlan = await refreshPlan();
          
          if (refreshedPlan && refreshedPlan.tier === "pro") {
            break;
          }
          
          if (i < 2) {
            await new Promise(resolve => setTimeout(resolve, 1000));
          }
        }
        
        // Step 4: Success animation
        setUnlockProgress("All set! Redirecting...");
        setShowSuccess(true);
        setToast({ type: 'success', message: '🎉 Plan unlocked successfully! All stages are now available.', duration: 3000 });
        
        // Mark that we just unlocked, so plan view can force refresh
        localStorage.setItem("just_unlocked", "true");
        
        // Navigate to plan view after success animation
        setTimeout(() => {
          if (onComplete) {
            onComplete(effectivePlanId);
          }
        }, 1500);
      } else {
        throw new Error(result?.message || "Unlock failed - no success response");
      }
    } catch (err) {
      console.error("Unlock failed:", err);
      
      // Show user-friendly error message
      const errorMsg = err.message || "Unable to unlock the plan";
      setToast({ type: 'error', message: `Unlock failed: ${errorMsg}. Please try again.`, duration: 5000 });
      setUnlockProgress("");
      setShowSuccess(false);
    } finally {
      // Reset unlocking state after a delay to allow animations
      setTimeout(() => {
        setUnlocking(false);
        setUnlockProgress("");
      }, 2000);
    }
  };

  // Auto-dismiss toast
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => {
        setToast(null);
      }, toast.duration || 3000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  if (loading) {
    return (
      <div className="card-stage">
        <div className="card-shell">
          <div className="card-surface">
            <div className="card-header">
              <div className="badge">Generating Your Plan</div>
              <h1>Creating Your Trading Path</h1>
              <p>Analyzing your responses and building your personalized plan...</p>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
                This may take 30-90 seconds. Please wait...
              </p>
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
                <p style={{ 
                  fontSize: '0.85rem',
                  color: 'var(--text-secondary)',
                  marginTop: '12px',
                  fontWeight: '400',
                  textTransform: 'none',
                  letterSpacing: 'normal'
                }}>
                  Generating personalized content with AI...
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Toast Notification */}
      {toast && (
        <div 
          style={{
            position: 'fixed',
            top: '20px',
            right: '20px',
            zIndex: 10000,
            padding: '16px 24px',
            borderRadius: '12px',
            background: toast.type === 'success' 
              ? 'linear-gradient(135deg, rgba(76, 175, 80, 0.95), rgba(56, 142, 60, 0.95))'
              : toast.type === 'error'
              ? 'linear-gradient(135deg, rgba(244, 67, 54, 0.95), rgba(198, 40, 40, 0.95))'
              : toast.type === 'warning'
              ? 'linear-gradient(135deg, rgba(255, 152, 0, 0.95), rgba(245, 124, 0, 0.95))'
              : 'linear-gradient(135deg, rgba(33, 150, 243, 0.95), rgba(25, 118, 210, 0.95))',
            color: '#ffffff',
            fontSize: '0.95rem',
            fontWeight: '500',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3), 0 4px 16px rgba(0, 0, 0, 0.2)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            backdropFilter: 'blur(10px)',
            animation: 'slideInRight 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            maxWidth: '400px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}
        >
          <span style={{ fontSize: '1.5rem' }}>
            {toast.type === 'success' ? '✅' : toast.type === 'error' ? '❌' : toast.type === 'warning' ? '⚠️' : 'ℹ️'}
          </span>
          <span>{toast.message}</span>
        </div>
      )}

      {/* Success Confetti Effect */}
      {showSuccess && (
        <div 
          style={{
            position: 'fixed',
            inset: 0,
            pointerEvents: 'none',
            zIndex: 9999,
            overflow: 'hidden'
          }}
        >
          {[...Array(50)].map((_, i) => (
            <div
              key={i}
              style={{
                position: 'absolute',
                width: '8px',
                height: '8px',
                background: ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336'][i % 5],
                left: `${Math.random() * 100}%`,
                top: `${-10 + Math.random() * 20}%`,
                borderRadius: '50%',
                animation: `confettiFall ${2 + Math.random() * 2}s linear forwards`,
                animationDelay: `${Math.random() * 0.5}s`,
                opacity: 0.9
              }}
            />
          ))}
        </div>
      )}

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
              {/* Summary Text with Markdown Rendering */}
              {summary && summary.trim() !== "" ? (
                <div className="summary-text" style={{ marginBottom: '32px', color: '#e5e7eb', lineHeight: '1.75' }}>
                  {renderMarkdown(summary)}
                </div>
              ) : !loading && !error ? (
                <div style={{ 
                  textAlign: 'center', 
                  padding: '40px', 
                  color: '#9ca3af',
                  fontStyle: 'italic',
                  marginBottom: '32px'
                }}>
                  No summary content available. Please wait for the plan to be generated.
                </div>
              ) : null}

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
                  background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(244, 63, 94, 0.15), rgba(219, 39, 119, 0.2))',
                  border: '2px solid rgba(236, 72, 153, 0.4)',
                  position: 'relative',
                  boxShadow: '0 4px 20px rgba(236, 72, 153, 0.2)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                    <span style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #ec4899, #f43f5e)',
                      border: '2px solid rgba(236, 72, 153, 0.6)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      fontWeight: '700',
                      fontSize: '1rem',
                      boxShadow: '0 2px 8px rgba(236, 72, 153, 0.4)'
                    }}>2</span>
                    <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: '600', color: '#f9a8d4' }}>
                      Stage 2: Insights and Routine
                    </h3>
                  </div>
                  <span style={{
                    display: 'inline-block',
                    padding: '4px 10px',
                    borderRadius: '999px',
                    background: 'rgba(236, 72, 153, 0.3)',
                    border: '1px solid rgba(236, 72, 153, 0.5)',
                    color: '#f9a8d4',
                    fontSize: '0.7rem',
                    fontWeight: '700',
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    marginBottom: '12px',
                    boxShadow: '0 2px 8px rgba(236, 72, 153, 0.3)'
                  }}>🔒 LOCKED</span>
                  <p style={{ margin: 0, color: '#f9a8d4', fontSize: '0.9rem', lineHeight: '1.6', fontWeight: '500' }}>
                    Personalized insights and a weekly routine, tool setup, 3 to 5 concrete drills, a simple practice loop.
                  </p>
                </div>

                {/* Stage 3 - LOCKED */}
                <div style={{
                  padding: '20px',
                  borderRadius: '18px',
                  background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.2), rgba(139, 92, 246, 0.15), rgba(124, 58, 237, 0.2))',
                  border: '2px solid rgba(168, 85, 247, 0.4)',
                  position: 'relative',
                  boxShadow: '0 4px 20px rgba(168, 85, 247, 0.2)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                    <span style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #a855f7, #8b5cf6)',
                      border: '2px solid rgba(168, 85, 247, 0.6)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      fontWeight: '700',
                      fontSize: '1rem',
                      boxShadow: '0 2px 8px rgba(168, 85, 247, 0.4)'
                    }}>3</span>
                    <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: '600', color: '#c4b5fd' }}>
                      Stage 3: Frameworks and Playbooks
                    </h3>
                  </div>
                  <span style={{
                    display: 'inline-block',
                    padding: '4px 10px',
                    borderRadius: '999px',
                    background: 'rgba(168, 85, 247, 0.3)',
                    border: '1px solid rgba(168, 85, 247, 0.5)',
                    color: '#c4b5fd',
                    fontSize: '0.7rem',
                    fontWeight: '700',
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    marginBottom: '12px',
                    boxShadow: '0 2px 8px rgba(168, 85, 247, 0.3)'
                  }}>🔒 LOCKED</span>
                  <p style={{ margin: 0, color: '#c4b5fd', fontSize: '0.9rem', lineHeight: '1.6', fontWeight: '500' }}>
                    Frameworks and playbooks, risk protocol, entry and exit checklist, review cadence, a growth ladder for 4 to 8 weeks.
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
                  disabled={unlocking || loading}
                  title={loading ? "Plan is being generated..." : !planId ? "Click to try unlock (will check localStorage)" : "Unlock all stages for $5"}
                  style={{ 
                    width: '100%',
                    fontSize: '1.05rem',
                    padding: '16px 32px',
                    cursor: (unlocking || loading) ? 'wait' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '12px',
                    visibility: 'visible',
                    opacity: (unlocking || loading) ? 0.9 : 1,
                    position: 'relative',
                    zIndex: 1000,
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    transform: (unlocking || loading) ? 'scale(0.98)' : 'scale(1)',
                    filter: (unlocking || loading) ? 'brightness(0.95)' : 'brightness(1)',
                    overflow: 'hidden'
                  }}
                >
                  {unlocking && (
                    <>
                      {/* Animated Spinner */}
                      <div style={{
                        width: '20px',
                        height: '20px',
                        border: '3px solid rgba(255, 255, 255, 0.2)',
                        borderTop: '3px solid #ffffff',
                        borderRight: '3px solid rgba(255, 255, 255, 0.8)',
                        borderRadius: '50%',
                        animation: 'spin 0.7s cubic-bezier(0.5, 0, 0.5, 1) infinite',
                        flexShrink: 0,
                        boxShadow: '0 0 10px rgba(255, 255, 255, 0.3)'
                      }}></div>
                      {/* Pulsing Background Effect */}
                      <div style={{
                        position: 'absolute',
                        inset: 0,
                        background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent)',
                        animation: 'shimmer 2s infinite',
                        pointerEvents: 'none'
                      }}></div>
                    </>
                  )}
                  {showSuccess && (
                    <span style={{
                      fontSize: '1.2rem',
                      animation: 'bounce 0.5s ease-in-out'
                    }}>🎉</span>
                  )}
                  <span style={{
                    position: 'relative',
                    zIndex: 1,
                    transition: 'opacity 0.3s ease',
                    opacity: unlocking ? 0.95 : 1
                  }}>
                    {showSuccess 
                      ? "Unlocked! Redirecting..." 
                      : unlocking 
                        ? (unlockProgress || "Unlocking Your Plan...") 
                        : "View Full Plan & Unlock for $5 →"}
                  </span>
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
    </>
  );
});

Summary.displayName = 'Summary';

export default Summary;
