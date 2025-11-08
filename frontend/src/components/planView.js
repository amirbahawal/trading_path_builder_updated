/**
 * Plan View Component
 * Displays the complete trading plan with all 3 stages
 * Shows locked/unlocked states based on user tier
 * Handles stage expansion and unlock flow
 * 
 * @component
 * @param {string} planId - Plan ID to display
 * @param {Function} onUnlock - Callback when user clicks to unlock
 * @param {Function} registerPlanRefresh - Callback to register plan refresh function
 */

import React, { useState, useEffect, useCallback } from "react";
import { usePlan } from "../hooks/usePlan";
import { logEvent } from "../api/analytics";
import { Lock, CheckCircle, Target, Zap, BookOpen } from 'lucide-react';
import { renderMarkdown } from "../utils/markdownRenderer";

/**
 * Split Screen Layout Component
 * Internal component that renders the stage cards layout
 * 
 * @param {boolean} isPro - Whether user has pro tier (all stages unlocked)
 * @param {Function} onUnlock - Callback to trigger unlock flow
 * @param {Array} stages - Array of stage objects
 */
const SplitScreenLayout = ({ isPro, onUnlock, stages }) => {
  const [animateStages, setAnimateStages] = useState(false);
  
  useEffect(() => {
    // Animate stages in after mount
    setTimeout(() => setAnimateStages(true), 300);
  }, []);

  // Get all 3 stages with fallbacks
  // Use locked property from backend response, not just isPro
  const stage1 = stages?.find(s => s.id === 1) || {
    id: 1,
    title: "Intro and Diagnostic",
    locked: false,
    content: "",
    teaser: null
  };
  
  const stage2 = stages?.find(s => s.id === 2) || {
    id: 2,
    title: "Insights and Routine",
    locked: !isPro, // Fallback to isPro if stage not found
    content: "",
    teaser: null
  };
  // Override with actual locked status from backend
  if (stages?.find(s => s.id === 2)) {
    stage2.locked = stages.find(s => s.id === 2).locked;
  }
  
  const stage3 = stages?.find(s => s.id === 3) || {
    id: 3,
    title: "Frameworks and Playbooks",
    locked: !isPro, // Fallback to isPro if stage not found
    content: "",
    teaser: null
  };
  // Override with actual locked status from backend
  if (stages?.find(s => s.id === 3)) {
    stage3.locked = stages.find(s => s.id === 3).locked;
  }

  // Stage colors and icons
  const stageConfig = [
    { 
      gradient: 'from-violet-500 to-purple-500', 
      bg: 'bg-violet-500/10', 
      border: 'border-violet-500/30',
      text: 'text-violet-400',
      icon: BookOpen,
      title: "Intro and Diagnostic"
    },
    { 
      gradient: 'from-pink-500 to-rose-500', 
      bg: 'bg-pink-500/10', 
      border: 'border-pink-500/30',
      text: 'text-pink-400',
      icon: Target,
      title: "Insights and Routine"
    },
    { 
      gradient: 'from-purple-500 to-fuchsia-500', 
      bg: 'bg-purple-500/10', 
      border: 'border-purple-500/30',
      text: 'text-purple-400',
      icon: Zap,
      title: "Frameworks and Playbooks"
    }
  ];

  return (
    <div className="w-full max-w-5xl mx-auto space-y-6">
      {/* Intro Text Above Stage 1 - Conditional based on unlock status */}
      <div className="bg-zinc-900/60 backdrop-blur-xl border border-violet-500/30 rounded-2xl p-6 text-center">
        {!stage2.locked && !stage3.locked ? (
          <p className="text-gray-300 text-lg leading-relaxed">
            🚀 You've invested in your trading success. This complete plan is tailored to your trading style—dive into your routines, frameworks, and playbooks to level up your journey.
          </p>
        ) : (
          <p className="text-gray-300 text-lg leading-relaxed">
            This plan is built for how you actually trade. Below is your quick diagnostic. If it speaks to you, unlock the full routine and frameworks for 5 USD.
          </p>
        )}
      </div>

      {/* Stage 1 - Expanded by Default */}
      <div
        className={`relative bg-zinc-900/80 backdrop-blur-xl border-2 rounded-3xl overflow-hidden transition-all duration-500 ${
          animateStages ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
        } ${stageConfig[0].border}`}
      >
        {/* Top Gradient Bar */}
        <div className={`absolute top-0 left-0 w-full h-1 bg-gradient-to-r ${stageConfig[0].gradient} rounded-t-3xl`}></div>

        {/* Header */}
        <div className="p-6">
          <div className="flex items-center gap-4 mb-4">
            <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${stageConfig[0].gradient} flex items-center justify-center shadow-lg`}>
              <BookOpen className="w-7 h-7 text-white" />
            </div>
            <div className="flex-1">
              <h4 className={`text-2xl font-bold ${stageConfig[0].text}`}>
                {stage1.title || stageConfig[0].title}
              </h4>
              <p className="text-sm text-gray-400">Your quick diagnostic</p>
            </div>
            <div className={`flex items-center gap-2 px-3 py-1 ${stageConfig[0].bg} ${stageConfig[0].border} border rounded-full text-xs font-bold ${stageConfig[0].text}`}>
              <CheckCircle className="w-3 h-3" /> Free
            </div>
          </div>

          {/* Stage 1 Content - Always Visible (Expanded) */}
          {stage1.content && (
            <div className="mt-4">
              <div className="text-gray-300 text-base leading-relaxed">
                {renderMarkdown(stage1.content)}
              </div>
            </div>
          )}
        </div>
      </div>


      {/* Stage 2 - Locked with Blur and Teaser */}
      <div
        className={`relative backdrop-blur-xl border-2 rounded-3xl overflow-hidden transition-all duration-500 ${
          animateStages ? 'opacity-100 translate-y-0 delay-150' : 'opacity-0 translate-y-8'
        } ${stage2.locked ? 'bg-gradient-to-br from-pink-500/20 via-rose-500/15 to-fuchsia-500/20 border-pink-500/40 cursor-pointer hover:border-pink-500/60 hover:shadow-2xl hover:shadow-pink-500/20' : 'bg-zinc-900/80 border-pink-500/30'}`}
        onClick={() => stage2.locked && onUnlock()}
      >
        {/* Top Gradient Bar */}
        <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-pink-500 via-rose-500 to-fuchsia-500 rounded-t-3xl"></div>

        {/* Blur Overlay for Locked State */}
        {stage2.locked && (
          <div className="absolute inset-0 backdrop-blur-md bg-black/40 z-10 rounded-3xl"></div>
        )}

        {/* Header */}
        <div className="p-6 relative z-0">
          <div className="flex items-center gap-4 mb-4">
            <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br from-pink-500 via-rose-500 to-fuchsia-500 flex items-center justify-center shadow-xl ${!stage2.locked ? 'ring-2 ring-pink-400 ring-offset-2 ring-offset-zinc-900' : 'ring-2 ring-pink-400/50'}`}>
              {stage2.locked ? <Lock className="w-8 h-8 text-white" /> : <Target className="w-8 h-8 text-white" />}
            </div>
            <div className="flex-1">
              <h4 className={`text-2xl font-bold ${!stage2.locked ? 'text-pink-300' : 'text-pink-200'}`}>
                {stage2.title || stageConfig[1].title}
              </h4>
              <p className={`text-sm ${!stage2.locked ? 'text-gray-400' : 'text-pink-300/70'}`}>
                Personalized insights and a weekly routine, tool setup, 3 to 5 concrete drills, a simple practice loop
              </p>
            </div>
            {!stage2.locked ? (
              <div className="flex items-center gap-2 px-3 py-1 bg-pink-500/20 border border-pink-500/30 rounded-full text-xs font-bold text-pink-400">
                <CheckCircle className="w-3 h-3" /> Unlocked
              </div>
            ) : (
              <div className="flex items-center gap-2 px-3 py-1 bg-pink-500/30 border border-pink-500/50 rounded-full text-xs font-bold text-pink-200 shadow-lg">
                <Lock className="w-3 h-3" /> Locked
              </div>
            )}
          </div>

          {/* Teaser Snippet - 3 to 5 bullets per CONTEXT.md */}
          {stage2.locked && stage2.teaser && stage2.teaser.length > 0 && (
            <div className="mt-4 space-y-2 relative z-20">
              <p className="text-sm text-pink-300/80 mb-3 font-semibold">✨ Preview of what's inside:</p>
              {stage2.teaser.slice(0, 5).map((item, i) => (
                <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-pink-500/10 border border-pink-500/30 hover:bg-pink-500/15 transition-colors">
                  <div className="w-5 h-5 border-2 border-pink-400 rounded-full mt-0.5 flex-shrink-0 flex items-center justify-center">
                    <div className="w-2 h-2 bg-pink-400 rounded-full"></div>
                  </div>
                  <p className="text-sm text-pink-100">{item}</p>
                </div>
              ))}
            </div>
          )}

          {/* Unlocked Content */}
          {!stage2.locked && stage2.content && (
            <div className="mt-4">
              <div className="text-gray-300 text-base leading-relaxed">
                {renderMarkdown(stage2.content)}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Stage 3 - Locked with Blur and Teaser */}
      <div
        className={`relative backdrop-blur-xl border-2 rounded-3xl overflow-hidden transition-all duration-500 ${
          animateStages ? 'opacity-100 translate-y-0 delay-300' : 'opacity-0 translate-y-8'
        } ${stage3.locked ? 'bg-gradient-to-br from-purple-500/20 via-violet-500/15 to-fuchsia-500/20 border-purple-500/40 cursor-pointer hover:border-purple-500/60 hover:shadow-2xl hover:shadow-purple-500/20' : 'bg-zinc-900/80 border-purple-500/30'}`}
        onClick={() => stage3.locked && onUnlock()}
      >
        {/* Top Gradient Bar */}
        <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-purple-500 via-violet-500 to-fuchsia-500 rounded-t-3xl"></div>

        {/* Blur Overlay for Locked State */}
        {stage3.locked && (
          <div className="absolute inset-0 backdrop-blur-md bg-black/40 z-10 rounded-3xl"></div>
        )}

        {/* Header */}
        <div className="p-6 relative z-0">
          <div className="flex items-center gap-4 mb-4">
            <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 via-violet-500 to-fuchsia-500 flex items-center justify-center shadow-xl ${!stage3.locked ? 'ring-2 ring-purple-400 ring-offset-2 ring-offset-zinc-900' : 'ring-2 ring-purple-400/50'}`}>
              {stage3.locked ? <Lock className="w-8 h-8 text-white" /> : <Zap className="w-8 h-8 text-white" />}
            </div>
            <div className="flex-1">
              <h4 className={`text-2xl font-bold ${!stage3.locked ? 'text-purple-300' : 'text-purple-200'}`}>
                {stage3.title || stageConfig[2].title}
              </h4>
              <p className={`text-sm ${!stage3.locked ? 'text-gray-400' : 'text-purple-300/70'}`}>
                Frameworks and playbooks, risk protocol, entry and exit checklist, review cadence, a growth ladder for 4 to 8 weeks
              </p>
            </div>
            {!stage3.locked ? (
              <div className="flex items-center gap-2 px-3 py-1 bg-purple-500/20 border border-purple-500/30 rounded-full text-xs font-bold text-purple-400">
                <CheckCircle className="w-3 h-3" /> Unlocked
              </div>
            ) : (
              <div className="flex items-center gap-2 px-3 py-1 bg-purple-500/30 border border-purple-500/50 rounded-full text-xs font-bold text-purple-200 shadow-lg">
                <Lock className="w-3 h-3" /> Locked
              </div>
            )}
          </div>

          {/* Teaser Snippet - 3 to 5 bullets per CONTEXT.md */}
          {stage3.locked && stage3.teaser && stage3.teaser.length > 0 && (
            <div className="mt-4 space-y-2 relative z-20">
              <p className="text-sm text-purple-300/80 mb-3 font-semibold">✨ Preview of what's inside:</p>
              {stage3.teaser.slice(0, 5).map((item, i) => (
                <div key={i} className="flex items-start gap-3 p-3 rounded-xl bg-purple-500/10 border border-purple-500/30 hover:bg-purple-500/15 transition-colors">
                  <div className="w-5 h-5 border-2 border-purple-400 rounded-full mt-0.5 flex-shrink-0 flex items-center justify-center">
                    <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
                  </div>
                  <p className="text-sm text-purple-100">{item}</p>
                </div>
              ))}
            </div>
          )}

          {/* Unlocked Content */}
          {!stage3.locked && stage3.content && (
            <div className="mt-4">
              <div className="text-gray-300 text-base leading-relaxed">
                {renderMarkdown(stage3.content)}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

function PlanViewComponent({ planId, onUnlock, registerPlanRefresh }) {
  const { plan, loading, error, refreshPlan, clearPlan } = usePlan(planId);
  const isPro = plan?.tier === "pro";
  
  // Force refresh on mount if coming from unlock (check localStorage)
  useEffect(() => {
    const shouldRefresh = localStorage.getItem("just_unlocked") === "true";
    if (shouldRefresh && planId && !loading) {
      // Add a small delay to ensure backend has processed the entitlement
      setTimeout(() => {
        refreshPlan().then((refreshedPlan) => {
          if (refreshedPlan) {
            localStorage.removeItem("just_unlocked");
            
            // If still not pro, try refreshing again after a delay
            if (refreshedPlan.tier !== "pro") {
              setTimeout(() => {
                refreshPlan().catch(() => {
                  // Silently handle retry errors
                });
              }, 1000);
            }
          }
        }).catch(() => {
          // Silently handle refresh errors - don't remove just_unlocked flag to allow retry
        });
      }, 500);
    }
  }, [planId, refreshPlan, loading]);

  useEffect(() => {
    if (registerPlanRefresh) registerPlanRefresh(refreshPlan, clearPlan);
  }, [registerPlanRefresh, refreshPlan, clearPlan]);

  const handleUnlockClick = useCallback(() => {
    const effectivePlanId = planId || plan?.plan_id;
    logEvent("unlock_click", { plan_id: effectivePlanId, user_id: plan?.user_id || "anon" });
    
    if (!effectivePlanId) {
      alert("Plan is not ready yet. Please wait a moment.");
      return;
    }
    
    onUnlock?.();
  }, [planId, plan, onUnlock]);

  const handleManualRefresh = useCallback(() => refreshPlan(), [refreshPlan]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-violet-950 to-black flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-violet-500 mx-auto mb-4"></div>
          <p className="text-gray-300">Loading your path...</p>
        </div>
      </div>
    );
  }

  if (error || (!plan && !loading)) {
    // Get user-friendly error message
    let errorMessage = "Failed to load your plan.";
    let isPlanNotFound = false;
    
    if (error) {
      if (typeof error === 'string') {
        errorMessage = error;
      } else if (error.message) {
        errorMessage = error.message;
      } else if (error.detail) {
        errorMessage = error.detail;
      }
      
      // Make error messages more user-friendly
      if (errorMessage.includes("Failed to fetch") || errorMessage.includes("CORS")) {
        errorMessage = "Cannot connect to server. Please check if the backend is running.";
      } else if (errorMessage.includes("404") || errorMessage.includes("not found") || errorMessage.includes("Plan not found")) {
        errorMessage = "Plan not found. Please create a new plan.";
        isPlanNotFound = true;
        // Clear invalid plan ID from localStorage
        try {
          localStorage.removeItem("current_plan_id");
          localStorage.removeItem("planId");
          localStorage.removeItem("just_unlocked");
        } catch (e) {
          // Ignore localStorage errors
        }
      } else if (errorMessage.includes("500") || errorMessage.includes("Internal Server")) {
        errorMessage = "Server error. Please try again later.";
      }
    }
    
    return (
      <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-violet-950 to-black flex items-center justify-center p-4">
        <div className="bg-zinc-900/80 backdrop-blur-xl rounded-2xl p-8 border border-violet-500/30 max-w-md text-center shadow-2xl">
          <h2 className="text-violet-400 text-xl font-bold mb-4">Unable to Load Plan</h2>
          <p className="text-gray-300 mb-6">{errorMessage}</p>
          <div className="flex gap-4 justify-center">
            {isPlanNotFound ? (
              <button 
                onClick={() => {
                  // Clear localStorage and redirect to home/quiz
                  try {
                    localStorage.removeItem("current_plan_id");
                    localStorage.removeItem("planId");
                    window.location.href = "/";
                  } catch (e) {
                    window.location.href = "/";
                  }
                }}
                className="px-6 py-3 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white rounded-xl font-semibold hover:scale-105 transition-transform shadow-lg"
              >
                Start New Quiz
              </button>
            ) : (
              <button 
                onClick={handleManualRefresh} 
                className="px-6 py-3 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white rounded-xl font-semibold hover:scale-105 transition-transform shadow-lg"
                aria-label="Retry loading plan"
                disabled={loading}
              >
                {loading ? "Loading..." : "Retry"}
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-violet-950 to-black relative overflow-hidden">
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-1/4 -left-48 w-96 h-96 bg-violet-600/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 -right-48 w-96 h-96 bg-fuchsia-600/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>
      <div className="relative z-10 p-8 pt-24">
        <SplitScreenLayout 
          isPro={isPro} 
          onUnlock={handleUnlockClick} 
          stages={plan?.stages}
        />
      </div>
    </div>
  );
}

const PlanView = React.memo(PlanViewComponent);
PlanView.displayName = 'PlanView';

export default PlanView;
