import React, { useState, useCallback, useRef } from "react";
import Quiz from "./components/quiz";
import Summary from "./components/summary";
import PlanView from "./components/planView";
import Header from "./components/header";
import AuthModal from "./components/AuthModal";
import UnlockModal from "./components/UnlockModal";
import ErrorBoundary from "./components/ErrorBoundary";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import "./style.css";
import "./header_modal_styles.css";

function AppContent() {
  const { isLoggedIn, logout } = useAuth();
  const [stage, setStage] = useState("quiz"); // quiz → summary → plan
  const [quizAnswers, setQuizAnswers] = useState(null);
  const [planId, setPlanId] = useState(null);
  
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
    console.log("Quiz submitted with answers:", answers);
    setQuizAnswers(answers);
    setStage("summary");
  };

  // Handle summary confirmation (create plan and go to plan view)
  const handleSummaryComplete = async (generatedPlanId) => {
    setPlanId(generatedPlanId);
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
    // Check if user is logged in
    if (!isLoggedIn) {
      // Show auth modal first, with unlock as pending action
      openAuthModal('unlocking', () => {
        setModalState(prev => ({ ...prev, showUnlock: true }));
      });
    } else {
      // User is logged in, open unlock modal directly
      setModalState(prev => ({ ...prev, showUnlock: true }));
    }
  }, [isLoggedIn, openAuthModal]);

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
    console.log("Global plan refresh triggered");
    
    // Call the refresh callback if it's registered
    if (planRefreshCallbackRef.current?.refreshPlan) {
      await planRefreshCallbackRef.current.refreshPlan();
    } else {
      console.warn("Plan refresh callback not registered yet");
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
    console.log("Plan refresh callback registered");
  }, []);

  // Handle plan unlock success
  const handleUnlockSuccess = useCallback(async (result) => {
    console.log("Plan unlock success:", result);
    
    // Refresh plan data to get updated tier
    await handlePlanRefresh();
    
    // Close unlock modal
    closeUnlockModal();
    
    // If we're on summary stage and have a planId, navigate to plan view
    if (stage === "summary" && planId) {
      console.log("Navigating to plan view after unlock success");
      setStage("plan");
    }
  }, [handlePlanRefresh, closeUnlockModal, stage, planId]);

  // Render based on current stage
  return (
    <div className="app-wrapper">
      {/* Header */}
      <Header 
        isLoggedIn={isLoggedIn}
        onSignIn={() => openAuthModal('viewing')}
        onSignOut={handleSignOut}
      />

      {/* Background effects */}
      <div className="background-grid"></div>
      <div className="background-orb orb-one"></div>
      <div className="background-orb orb-two"></div>

      {/* Stage components wrapped in error boundaries */}
      {stage === "quiz" && (
        <ErrorBoundary title="Quiz Error" message="We couldn't load the quiz. Please refresh the page.">
          <Quiz onComplete={handleQuizSubmit} />
        </ErrorBoundary>
      )}

      {stage === "summary" && (
        <ErrorBoundary title="Summary Error" message="We couldn't load your summary. Please try again.">
          <Summary 
            answers={quizAnswers} 
            onComplete={handleSummaryComplete}
            onUnlock={openUnlockModal}
            registerPlanRefresh={registerPlanRefresh}
          />
        </ErrorBoundary>
      )}

      {stage === "plan" && planId && (
        <ErrorBoundary title="Plan Error" message="We couldn't load your plan. Please refresh to try again.">
          <PlanView 
            planId={planId} 
            onUnlock={openUnlockModal}
            registerPlanRefresh={registerPlanRefresh}
          />
        </ErrorBoundary>
      )}

      {/* Modals */}
      <AuthModal
        isOpen={modalState.showAuth}
        onClose={closeAuthModal}
        onSuccess={handleAuthSuccess}
        purpose={modalState.authPurpose}
      />

      <UnlockModal
        isOpen={modalState.showUnlock}
        onClose={closeUnlockModal}
        onUnlockSuccess={handleUnlockSuccess}
        planId={planId}
        onNeedAuth={() => openAuthModal('unlocking', openUnlockModal)}
      />
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