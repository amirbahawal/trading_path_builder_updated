import React, { useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { getPlan } from "../api/plan";

const CheckoutPage = ({ onUnlock }) => {
  const [params] = useSearchParams();
  const planId = params.get("plan_id");

  useEffect(() => {
    if (planId) {
      getPlan(planId).then((data) => {
        onUnlock(data.plan_id);
      });
    }
  }, [planId, onUnlock]);

  return (
    <div className="flow-card--intro">
      <div className="loading-spinner"></div>
      <p className="flow-card__subtitle">Verifying payment and unlocking your plan...</p>
    </div>
  );
};

export default CheckoutPage;
