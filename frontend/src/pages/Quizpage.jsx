import React, { useState } from "react";
import Quiz from "./quiz";
import Summary from "./summary";
import PlanView from "./PlanView"; // Fixed import

const QuizPage = () => {
  const [stage, setStage] = useState("quiz");
  const [answers, setAnswers] = useState(null);
  const [plan, setPlan] = useState(null);

  const handleQuizComplete = (data) => {
    setAnswers(data);
    setStage("summary");
  };

  const handleSummaryComplete = (generatedPlan) => {
    setPlan(generatedPlan);
    setStage("plan");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-violet-950 to-black">
      {stage === "quiz" && <Quiz onComplete={handleQuizComplete} />}
      {stage === "summary" && <Summary answers={answers} onComplete={handleSummaryComplete} />}
      {stage === "plan" && plan && <PlanView plan={plan} />}
    </div>
  );
};

export default QuizPage;