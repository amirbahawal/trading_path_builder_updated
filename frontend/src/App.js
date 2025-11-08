/**
 * Main App Component
 * Root component that manages application state and routing
 * Handles quiz → summary → plan flow
 */

import React, { useState, useCallback, useRef, useEffect, lazy, Suspense } from "react";
import ErrorBoundary from "./components/ErrorBoundary";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import LoadingSpinner from "./components/loadingSpinner";
import "./style.css";
import "./header_modal_styles.css";

// Lazy load heavy components for code splitting
const Quiz = lazy(() => import("./components/quiz"));
const Summary = lazy(() => import("./components/summary"));
const PlanView = lazy(() => import("./components/planView"));
const Header = lazy(() => import("./components/header"));
const AuthModal = lazy(() => import("./components/AuthModal"));
const UnlockModal = lazy(() => import("./components/UnlockModal"));

/**
 * App Content Component
 * Main application logic without AuthProvider wrapper
 */
function AppContent() {
  const { isLoggedIn, logout } = useAuth();
  const [stage, setStage] = useState("quiz"); // quiz → summary → plan
  const [quizAnswers, setQuizAnswers] = useState(null);
  const [planId, setPlanId] = useState(null);
  
  // Initialize planId from localStorage on mount, but validate it
  useEffect(() => {
    const storedPlanId = localStorage.getItem("current_plan_id");
    if (storedPlanId && storedPlanId !== "pending" && storedPlanId.length >= 8) {
      // Only set if it looks like a valid plan ID
      setPlanId(storedPlanId);
    } else if (storedPlanId) {
      // Clear invalid plan ID from localStorage
      localStorage.removeItem("current_plan_id");
      localStorage.removeItem("planId");
    }
  }, []);
  
  // Unified modal state management
  const [modalState, setModalState] = useState({
    showAuth: false,
    showUnlock: false,
    authPurpose: null, // 'viewing', 'unlocking', or null
    pendingAction: null // Function to execute after auth success
  });
  
  // Use ref to store refresh callbacks from child components
  const planRefreshCallbackRef = useRef(null);

  // Handle quiz submission
  const handleQuizSubmit = async (answers) => {
    setQuizAnswers(answers);
    setStage("summary");
  };

  // Handle summary confirmation (create plan and go to plan view)
  const handleSummaryComplete = async (generatedPlanId) => {
    setPlanId(generatedPlanId);
    // Store planId in localStorage for UnlockModal access
    if (generatedPlanId) {
      localStorage.setItem("current_plan_id", generatedPlanId);
    }
    setStage("plan");
  };

  /**
   * Unified modal management functions
   */
  const openAuthModal = useCallback((purpose = null, pendingAction = null) => {
    setModalState(prev => ({
      ...prev,
      showAuth: true,
      authPurpose: purpose,
      pendingAction
    }));
  }, []);

  const closeAuthModal = useCallback(() => {
    setModalState(prev => ({
      ...prev,
      showAuth: false,
      authPurpose: null,
      pendingAction: null
    }));
  }, []);

  const openUnlockModal = useCallback(() => {
    // Instant unlock - no login required (mock payment mode)
    // Open unlock modal directly without auth check
    setModalState(prev => ({ ...prev, showUnlock: true }));
  }, []);

  const closeUnlockModal = useCallback(() => {
    setModalState(prev => ({ ...prev, showUnlock: false }));
  }, []);

  /**
   * Handle successful authentication
   * Execute pending action if any
   */
  const handleAuthSuccess = useCallback(() => {
    const { pendingAction } = modalState;
    
    closeAuthModal();
    
    // Execute pending action after a brief delay
    if (pendingAction) {
      setTimeout(() => {
        pendingAction();
      }, 300);
    }
  }, [modalState, closeAuthModal]);

  // Handle sign out
  const handleSignOut = () => {
    logout();
    // Clear plan data on logout
    if (planRefreshCallbackRef.current) {
      planRefreshCallbackRef.current.clearPlan();
    }
    // Close any open modals
    setModalState({
      showAuth: false,
      showUnlock: false,
      authPurpose: null,
      pendingAction: null
    });
  };

  /**
   * Global refresh mechanism for plan data
   * Called after successful unlock to refresh plan state
   */
  const handlePlanRefresh = useCallback(async () => {
    // Call the refresh callback if it's registered
    if (planRefreshCallbackRef.current?.refreshPlan) {
      await planRefreshCallbackRef.current.refreshPlan();
    }
  }, []);

  /**
   * Register refresh callback from child components
   * This allows children to expose their refresh functions to the parent
   */
  const registerPlanRefresh = useCallback((refreshFn, clearFn) => {
    planRefreshCallbackRef.current = {
      refreshPlan: refreshFn,
      clearPlan: clearFn
    };
  }, []);

  // Handle plan unlock success
  const handleUnlockSuccess = useCallback(async (result) => {
    // Refresh plan data to get updated tier (stages 2 & 3 unlocked)
    if (planRefreshCallbackRef.current?.refreshPlan) {
      await planRefreshCallbackRef.current.refreshPlan();
    } else {
      await handlePlanRefresh();
    }
    
    // Close unlock modal
    closeUnlockModal();
    
    // If we're on summary stage and have a planId, navigate to plan view
    if (stage === "summary" && planId) {
      setStage("plan");
    }
  }, [handlePlanRefresh, closeUnlockModal, stage, planId]);

  // Render based on current stage
  return (
    <div className="app-wrapper">
      {/* Header with Suspense */}
      <Suspense fallback={<LoadingSpinner />}>
        <Header 
          isLoggedIn={isLoggedIn}
          onSignIn={() => openAuthModal('viewing')}
          onSignOut={handleSignOut}
        />
      </Suspense>

      {/* Background effects */}
      <div className="background-grid"></div>
      <div className="background-orb orb-one"></div>
      <div className="background-orb orb-two"></div>

      {/* Stage components wrapped in error boundaries and Suspense */}
      {stage === "quiz" && (
        <ErrorBoundary title="Quiz Error" message="We couldn't load the quiz. Please refresh the page.">
          <Suspense fallback={<LoadingSpinner />}>
            <Quiz onComplete={handleQuizSubmit} />
          </Suspense>
        </ErrorBoundary>
      )}

      {stage === "summary" && (
        <ErrorBoundary title="Summary Error" message="We couldn't load your summary. Please try again.">
          <Suspense fallback={<LoadingSpinner />}>
            <Summary 
              answers={quizAnswers} 
              onComplete={handleSummaryComplete}
              onUnlock={openUnlockModal}
              registerPlanRefresh={registerPlanRefresh}
            />
          </Suspense>
        </ErrorBoundary>
      )}

      {stage === "plan" && planId && (
        <ErrorBoundary title="Plan Error" message="We couldn't load your plan. Please refresh to try again.">
          <Suspense fallback={<LoadingSpinner />}>
            <PlanView 
              planId={planId} 
              onUnlock={openUnlockModal}
              registerPlanRefresh={registerPlanRefresh}
            />
          </Suspense>
        </ErrorBoundary>
      )}

      {/* Modals with Suspense */}
      {modalState.showAuth && (
        <Suspense fallback={<LoadingSpinner />}>
          <AuthModal
            isOpen={modalState.showAuth}
            onClose={closeAuthModal}
            onSuccess={handleAuthSuccess}
            purpose={modalState.authPurpose}
          />
        </Suspense>
      )}

      {modalState.showUnlock && (
        <Suspense fallback={<LoadingSpinner />}>
          <UnlockModal
            isOpen={modalState.showUnlock}
            onClose={closeUnlockModal}
            onUnlockSuccess={handleUnlockSuccess}
            planId={planId || localStorage.getItem("current_plan_id") || null}
          />
        </Suspense>
      )}
    </div>
  );
}

// Wrap the app with AuthProvider
function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;