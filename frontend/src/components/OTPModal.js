import React, { useState, useEffect } from "react";
import "../styles/OTPModal.css";
import { apiRequest } from "../api/client";
import { API_ENDPOINTS, UI_CONFIG, APP_CONSTANTS } from "../constants";

const OTPModal = ({ isOpen, email, onVerified, onCancel, purpose = "login" }) => {
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [timeLeft, setTimeLeft] = useState(UI_CONFIG.OTP_EXPIRATION_SECONDS);
  const [canResend, setCanResend] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);

  // Timer for OTP expiration
  useEffect(() => {
    if (!isOpen) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          setError("OTP expired. Please request a new code.");
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isOpen]);

  // Timer for resend cooldown
  useEffect(() => {
    if (resendCooldown <= 0) {
      setCanResend(true);
      return;
    }

    const timer = setTimeout(() => {
      setResendCooldown((prev) => prev - 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [resendCooldown]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const handleOTPChange = (e) => {
    const value = e.target.value.replace(/\D/g, "").slice(0, 6);
    setOtp(value);
    setError("");
  };

  const handleVerify = async () => {
    if (otp.length !== APP_CONSTANTS.OTP_LENGTH) {
      setError(`Please enter a ${APP_CONSTANTS.OTP_LENGTH}-digit code`);
      return;
    }

    setLoading(true);
    try {
      const endpoint =
        purpose === "login"
          ? API_ENDPOINTS.AUTH_VERIFY_LOGIN_CODE
          : API_ENDPOINTS.AUTH_COMPLETE_UNLOCK;

      const data = await apiRequest(endpoint, "POST", {
        email,
        code: otp,
        plan_id: purpose === "unlock" ? localStorage.getItem("planId") : undefined,
      });

      onVerified(data);
    } catch (err) {
      setError(err.message || "Verification failed. Please try again.");
      console.error("Verification error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (!canResend) return;

    setLoading(true);
    setCanResend(false);
    setResendCooldown(UI_CONFIG.OTP_RESEND_COOLDOWN);

    try {
      const endpoint =
        purpose === "login"
          ? API_ENDPOINTS.AUTH_SEND_LOGIN_CODE
          : API_ENDPOINTS.AUTH_UNLOCK_PLAN;

      await apiRequest(endpoint, "POST", { email });

      setOtp("");
      setTimeLeft(UI_CONFIG.OTP_EXPIRATION_SECONDS);
      setError("");
    } catch (err) {
      setError(err.message || "Failed to resend code. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const titleText =
    purpose === "login"
      ? "Enter Your Login Code"
      : "Enter Your Unlock Code";
  const subtitleText =
    purpose === "login"
      ? "We've sent a 6-digit code to your email"
      : "We've sent a 6-digit code to verify your purchase";

  return (
    <div className="otp-modal-overlay" onClick={onCancel}>
      <div className="otp-modal" onClick={(e) => e.stopPropagation()}>
        <div className="otp-modal-header">
          <h2>{titleText}</h2>
          <button className="otp-close-btn" onClick={onCancel}>
            ✕
          </button>
        </div>

        <div className="otp-modal-body">
          <p className="otp-subtitle">{subtitleText}</p>
          <p className="otp-email">{email}</p>

          <div className="otp-input-container">
            <input
              type="text"
              className={`otp-input ${error ? "error" : ""}`}
              placeholder="000000"
              value={otp}
              onChange={handleOTPChange}
              maxLength="6"
              disabled={loading}
              autoFocus
            />
          </div>

          {error && <div className="otp-error">{error}</div>}

          <div className="otp-timer">
            <span>Code expires in: {formatTime(timeLeft)}</span>
          </div>

          <button
            className="otp-verify-btn"
            onClick={handleVerify}
            disabled={loading || otp.length !== APP_CONSTANTS.OTP_LENGTH || timeLeft === 0}
          >
            {loading ? "Verifying..." : "Verify Code"}
          </button>

          <div className="otp-resend">
            <p>Didn't receive the code?</p>
            <button
              className={`otp-resend-btn ${!canResend ? "disabled" : ""}`}
              onClick={handleResend}
              disabled={!canResend || loading}
            >
              {canResend ? "Resend Code" : `Resend in ${resendCooldown}s`}
            </button>
          </div>
        </div>

        <div className="otp-security-note">
          <span>🔒</span>
          <p>Never share your verification code with anyone</p>
        </div>
      </div>
    </div>
  );
};

export default OTPModal;
