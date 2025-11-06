import React from "react";
import PlanView from "../components/planView";

const PlanPage = ({ planId }) => {
  if (!planId) {
    return (
      <div className="flow-card--intro">
        <p className="flow-card__subtitle">
          No plan selected. Please complete the quiz first.
        </p>
      </div>
    );
  }

  return (
    <div>
      <PlanView planId={planId} />
    </div>
  );
};

export default PlanPage;
