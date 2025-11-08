/**
 * Quiz Component
 * Multi-step quiz component that collects user trading preferences
 * Handles intro, honesty check, and all quiz questions with progress tracking
 * 
 * @component
 * @param {Function} onComplete - Callback when quiz is completed with answers object
 */

import React, { useMemo, useState, useEffect, useRef, useCallback } from "react";
import { QUIZ_QUESTIONS } from "../constants/questions";

const TOTAL_STEPS = 2 + QUIZ_QUESTIONS.length;

function Quiz({ onComplete }) {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState({});
  const [selectedOption, setSelectedOption] = useState("");
  const [error, setError] = useState("");
  const containerRef = useRef(null);

  const currentStoredIndex = step - 2;
  const isStoredStep = step >= 2 && currentStoredIndex < QUIZ_QUESTIONS.length;

  const progressPercent = useMemo(() => {
    // When on quiz questions (step >= 2), calculate based on questions answered
    if (step >= 2) {
      const questionIndex = step - 2;
      // Show 100% when all questions are answered
      if (questionIndex >= QUIZ_QUESTIONS.length) {
        return 100;
      }
      // Calculate progress based on questions (excluding intro and honesty steps)
      // We add 1 because we're showing progress for the current question being answered
      return Math.round(((questionIndex + 1) / QUIZ_QUESTIONS.length) * 100);
    }
    // For intro (step 0) and honesty (step 1), show minimal progress
    return Math.round(((step + 1) / TOTAL_STEPS) * 100);
  }, [step]);

  const currentQuestion = isStoredStep
    ? QUIZ_QUESTIONS[currentStoredIndex]
    : null;


  const syncSelectedForStep = useCallback((targetStep, updatedAnswers) => {
    if (targetStep >= 2 && targetStep - 2 < QUIZ_QUESTIONS.length) {
      const upcomingQuestion = QUIZ_QUESTIONS[targetStep - 2];
      setSelectedOption(updatedAnswers[upcomingQuestion.key] || "");
    } else {
      setSelectedOption("");
    }
  }, []);

  const goToStep = useCallback((nextStep, updatedAnswers) => {
    const target = Math.min(nextStep, TOTAL_STEPS);
    if (target >= TOTAL_STEPS) {
      // Use updatedAnswers if provided, otherwise we need to get current answers
      // Since we can't access answers in closure, updatedAnswers must always be provided
      // or we use a callback pattern
      if (updatedAnswers !== undefined) {
        onComplete(updatedAnswers);
      } else {
        // Fallback: get current answers from state using functional update
        setAnswers(currentAnswers => {
          onComplete(currentAnswers);
          return currentAnswers;
        });
      }
      return;
    }

    setStep(target);
    // Use updatedAnswers if provided for syncing selected option
    if (updatedAnswers !== undefined) {
      syncSelectedForStep(target, updatedAnswers);
    } else {
      // Fallback: get current answers from state using functional update
      setAnswers(currentAnswers => {
        syncSelectedForStep(target, currentAnswers);
        return currentAnswers;
      });
    }
    setError("");
  }, [onComplete, syncSelectedForStep]);

  const handleQ0 = useCallback((answer) => {
    if (answer === "No") {
      alert("No problem. Come back when you are ready.");
      setStep(0);
      setSelectedOption("");
      return;
    }
    goToStep(1);
  }, [goToStep]);

  const handleContinueFromHonesty = useCallback(() => {
    goToStep(2);
  }, [goToStep]);

  const handleNext = useCallback(() => {
    if (isStoredStep && currentQuestion) {
      if (!selectedOption) {
        setError("Please choose the option that fits you best.");
        return;
      }

      const updated = {
        ...answers,
        [currentQuestion.key]: selectedOption,
      };
      setAnswers(updated);
      
      // Check if this is the last question
      const isLastQuestion = currentStoredIndex === QUIZ_QUESTIONS.length - 1;
      
      if (isLastQuestion) {
        // For last question, show 100% progress and complete
        setStep(2 + QUIZ_QUESTIONS.length);
        setTimeout(() => {
          onComplete(updated);
        }, 500);
      } else {
        goToStep(step + 1, updated);
      }
      return;
    }

    goToStep(step + 1);
  }, [isStoredStep, currentQuestion, selectedOption, answers, step, currentStoredIndex, goToStep, onComplete]);

  const handleBack = useCallback(() => {
    if (step === 0) {
      return;
    }
    const target = Math.max(0, step - 1);
    goToStep(target);
  }, [step, goToStep]);

  const handleOptionSelect = useCallback((option) => {
    if (isStoredStep && currentQuestion) {
      setSelectedOption(option);
      setError("");
      
      // Check if this is the last question
      const isLastQuestion = currentStoredIndex === QUIZ_QUESTIONS.length - 1;
      
      // Update answers
      setAnswers(prevAnswers => {
        const updated = {
          ...prevAnswers,
          [currentQuestion.key]: option,
        };
        
        // For last question, don't auto-submit - let user click "Build My Plan"
        // For other questions, auto-submit and move to next
        if (!isLastQuestion) {
          // Automatically move to next step for non-last questions
          setTimeout(() => {
            goToStep(step + 1, updated);
          }, 0);
        }
        
        return updated;
      });
    } else {
      setSelectedOption(option);
      setError("");
    }
  }, [isStoredStep, currentQuestion, currentStoredIndex, step, goToStep]);

  // Keyboard shortcuts handler
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ignore if user is typing in an input/textarea
      if (
        e.target.tagName === "INPUT" ||
        e.target.tagName === "TEXTAREA" ||
        e.target.isContentEditable
      ) {
        return;
      }

      const key = e.key.toLowerCase();

      // Step 0: Initial Yes/No question
      if (step === 0) {
        if (key === "y" || key === "enter") {
          e.preventDefault();
          handleQ0("Yes");
        } else if (key === "n" || key === "escape") {
          e.preventDefault();
          handleQ0("No");
        }
        return;
      }

      // Step 1: Honesty page
      if (step === 1) {
        if (key === "enter") {
          e.preventDefault();
          handleContinueFromHonesty();
        } else if (key === "escape" || (key === "b" && e.shiftKey)) {
          e.preventDefault();
          goToStep(0);
        }
        return;
      }

      // Quiz questions (step >= 2)
      if (isStoredStep && currentQuestion) {
        // Map a, b, c, d, e to options
        const keyMap = {
          a: 0,
          b: 1,
          c: 2,
          d: 3,
          e: 4,
        };

        if (keyMap.hasOwnProperty(key)) {
          const optionIndex = keyMap[key];
          if (optionIndex < currentQuestion.options.length) {
            e.preventDefault();
            const option = currentQuestion.options[optionIndex];
            // handleOptionSelect will now auto-submit and move to next
            handleOptionSelect(option);
          }
          return;
        }

        // Enter key to submit/next
        if (key === "enter") {
          e.preventDefault();
          if (selectedOption) {
            handleNext();
          }
          return;
        }

        // Escape or Backspace to go back
        if (key === "escape" || (key === "backspace" && !e.target.matches("button, input, textarea"))) {
          e.preventDefault();
          handleBack();
          return;
        }
      }
    };

    // Add event listener
    window.addEventListener("keydown", handleKeyDown);

    // Cleanup
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [step, isStoredStep, currentQuestion, selectedOption, handleQ0, handleContinueFromHonesty, handleOptionSelect, handleNext, handleBack, goToStep]);

  if (step === 0) {
    return (
      <div className="card-stage">
        <div className="card-shell">
          <div className="card-surface">
            <section className="flow-card flow-card--intro">
              <div className="flow-card__meta" aria-hidden>
                <span className="stage-pill">Checkpoint 01</span>
                <span className="stage-line" />
                <span className="stage-label">Set your intention</span>
              </div>
              <h2 className="flow-card__title">
                Do you want to learn more about markets?
              </h2>
              <p className="flow-card__subtitle">(Quick check - this will not be saved)</p>
              <div className="button-stack">
                <button 
                  className="cta-button" 
                  onClick={() => handleQ0("Yes")}
                  title="Press Y or Enter"
                >
                  Yes, build my plan
                </button>
                <button 
                  className="secondary-button" 
                  onClick={() => handleQ0("No")}
                  title="Press N or Escape"
                >
                  Not right now
                </button>
              </div>
              <div className="flow-card__hint">Tip: honest answers give better suggestions.</div>
              <div className="insight-chips" aria-hidden>
                <span>Curiosity</span>
                <span>Momentum</span>
                <span>Clarity</span>
              </div>
            </section>
          </div>
        </div>
      </div>
    );
  }

  if (step === 1) {
    return (
      <div className="card-stage">
        <div className="card-shell">
          <div className="card-surface">
            <section className="flow-card flow-card--intro">
              <div className="flow-card__meta" aria-hidden>
                <span className="stage-pill">Honesty Lock</span>
                <span className="stage-line" />
                <span className="stage-label">Transparency powers the AI</span>
              </div>
              <h3 className="flow-card__title">Honesty nudge</h3>
              <p className="flow-card__subtitle">
                Answer with ego off. Your path should match your truth, not your fantasy.
              </p>
              <div className="button-stack">
                <button 
                  className="cta-button" 
                  onClick={handleContinueFromHonesty}
                  title="Press Enter"
                >
                  Continue
                </button>
                <button 
                  className="secondary-button" 
                  onClick={() => goToStep(0)}
                  title="Press Escape or Shift+B"
                >
                  Back
                </button>
              </div>
            </section>
          </div>
        </div>
      </div>
    );
  }

  // Show completion screen with 100% progress when all questions are answered
  const allQuestionsAnswered = step >= 2 && currentStoredIndex >= QUIZ_QUESTIONS.length;
  
  if (allQuestionsAnswered) {
    return (
      <div className="card-stage" ref={containerRef}>
        <div className="card-shell">
          <div className="card-surface">
            <section className="flow-card">
              <div className="progress-wrapper">
                <div className="progress-track" aria-hidden>
                  <div className="progress-indicator" style={{ width: '100%' }} />
                </div>
                <div className="progress-meta">
                  <span>
                    Question {QUIZ_QUESTIONS.length} of {QUIZ_QUESTIONS.length}
                  </span>
                  <span>100% complete</span>
                </div>
              </div>
              <div className="question-header">
                <h3 className="flow-card__title">Quiz Complete!</h3>
                <p className="flow-card__subtitle flow-card__subtitle--muted">
                  Building your personalized plan...
                </p>
              </div>
            </section>
          </div>
        </div>
      </div>
    );
  }

  if (!currentQuestion) {
    return null;
  }

  const questionNumber = currentStoredIndex + 1;
  const isLastQuestion = questionNumber === QUIZ_QUESTIONS.length;

  return (
    <div className="card-stage" ref={containerRef}>
      <div className="card-shell">
        <div className="card-surface">
          <section className="flow-card">
            <div className="progress-wrapper">
              <div className="progress-track" aria-hidden>
                <div className="progress-indicator" style={{ width: `${progressPercent}%` }} />
              </div>
              <div className="progress-meta">
                <span>
                  Question {questionNumber} of {QUIZ_QUESTIONS.length}
                </span>
                <span>{progressPercent}% complete</span>
              </div>
            </div>

            <div className="question-header">
              <h3 className="flow-card__title">{currentQuestion.label}</h3>
              <p className="flow-card__subtitle flow-card__subtitle--muted">
                Choose the option that describes you best.
              </p>
            </div>

            <div className="option-grid" role="group" aria-label={currentQuestion.label}>
              {currentQuestion.options.map((option, index) => {
                const isActive = selectedOption === option;
                const keyLabel = ["a", "b", "c", "d", "e"][index];
                return (
                  <button
                    key={option}
                    type="button"
                    className={`option-button${isActive ? " is-selected" : ""}`}
                    onClick={() => handleOptionSelect(option)}
                    aria-label={`Option ${keyLabel ? keyLabel.toUpperCase() : index + 1}: ${option}. Press ${keyLabel ? keyLabel.toUpperCase() : index + 1} to select.`}
                    title={keyLabel ? `Press ${keyLabel.toUpperCase()}` : ""}
                  >
                    <span>{option}</span>
                  </button>
                );
              })}
            </div>

            {error && (
              <div className="error-text" role="alert">
                {error}
              </div>
            )}

            <div className="button-stack button-stack--stretch">
              <button 
                className="secondary-button" 
                onClick={handleBack}
                title="Press Escape or Backspace to go back"
              >
                Back
              </button>
              {isLastQuestion ? (
                <button 
                  className="cta-button" 
                  onClick={handleNext} 
                  disabled={!selectedOption}
                  title="Click to build your plan"
                  style={{ 
                    fontSize: '1.35rem',
                    fontWeight: 700,
                    padding: '20px 42px'
                  }}
                >
                  Build My Plan
                </button>
              ) : (
                <button 
                  className="secondary-button" 
                  onClick={handleNext} 
                  disabled={!selectedOption}
                  title="Press Enter to continue (optional - answer auto-submits)"
                  style={{ 
                    opacity: selectedOption ? 0.6 : 0.3,
                    cursor: selectedOption ? 'pointer' : 'not-allowed'
                  }}
                >
                  Next
                </button>
              )}
            </div>
            <div style={{ 
              marginTop: "24px", 
              fontSize: "1rem", 
              color: "var(--text-secondary)",
              textAlign: "center",
              opacity: 0.7
            }}>
              💡 Tip: Click an answer or press <strong>A-E</strong> to select and continue automatically
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

// Memoize Quiz component to prevent unnecessary re-renders
export default React.memo(Quiz);



