import React, { useState, useEffect } from "react";
import { sendLoginCode, verifyLoginCode } from "../api/auth";
import { useAuth } from "../contexts/AuthContext";

const AuthModal = ({ isOpen, onClose, onSuccess, purpose }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [step, setStep] = useState("email"); // "email" or "code"
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [timer, setTimer] = useState(600); // Countdown timer (10 minutes)
  const [resendCooldown, setResendCooldown] = useState(0);

  // Countdown effect
  useEffect(() => {
    if (step === "code" && timer > 0) {
      const countdown = setInterval(() => setTimer(prev => prev - 1), 1000);
      return () => clearInterval(countdown);
    }
  }, [step, timer]);
  // Resend cooldown
  useEffect(() => {
    if (resendCooldown > 0) {
      const cooldown = setInterval(() => setResendCooldown(prev => prev - 1), 1000);
      return () => clearInterval(cooldown);
    }
  }, [resendCooldown]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }
    return () => {
      document.body.style.overflow = 'auto';
    }
  }, [isOpen]);

  const handleSendCode = async () => {
    if (!email) {
      setError("Please enter your email");
      return;
    }
    
    setLoading(true);
    setError("");
    
    try {
      await sendLoginCode(email);
      setStep("code");
      setTimer(600); // Reset timer
      setResendCooldown(60); // Set cooldown for resend
    } catch (err) {
      console.error("Send code error:", err);
      // Show more detailed error message
      const errorMsg = err.message || "Failed to send code. Please try again.";
      if (errorMsg.includes("Connection failed") || errorMsg.includes("fetch")) {
        setError("Cannot connect to server. Make sure backend is running.");
      } else if (errorMsg.includes("429") || errorMsg.includes("Too many")) {
        setError("Too many requests. Please wait a moment and try again.");
      } else {
        setError(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async () => {
    if (!code || code.length !== 6) {
      setError("Please enter the 6-digit code");
      return;
    }
    
    setLoading(true);
    setError("");
    
    try {
      const result = await verifyLoginCode(email, code);
      
      // Use AuthContext login function to persist auth state
      login(result.session_token, result.user_id, email);
      
      // Reset modal state
      setEmail("");
      setCode("");
      setStep("email");
      setError("");
      
      // Close modal
      onClose();
      
      // Call onSuccess callback if provided (for pending actions like unlock)
      if (onSuccess) {
        setTimeout(() => {
          onSuccess();
        }, 300);
      }
    } catch (err) {
      console.error("Verify code error:", err);
      const errorMsg = err.message || "Invalid code or email.";
      if (errorMsg.includes("Invalid or expired")) {
        setError("Code expired or invalid. Please request a new code.");
      } else if (errorMsg.includes("429") || errorMsg.includes("Too many")) {
        setError("Too many attempts. Please wait and try again.");
      } else {
        setError(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResendCode = async () => {
    if (resendCooldown > 0) return;
    
    setLoading(true);
    setError("");
    
    try {
      await sendLoginCode(email);
      setTimer(600); // Reset timer
      setResendCooldown(60); // Reset cooldown
      setError(""); // Clear any previous errors
    } catch (err) {
      console.error("Resend code error:", err);
      const errorMsg = err.message || "Failed to resend code.";
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setEmail("");
    setCode("");
    setStep("email");
    setError("");
    setTimer(600);
    setResendCooldown(0);
    onClose();
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div
        className="modal-content"
        onClick={e => e.stopPropagation()}
        style={{ 
          maxWidth: '420px', 
          width: '90%',
          borderRadius: '16px', 
          overflow: 'hidden', 
          boxShadow: '0 20px 25px -5px rgba(0,0,0,0.3), 0 10px 10px -5px rgba(0,0,0,0.2)',
          margin: 'auto',
          position: 'relative'
        }}
        role="dialog" aria-modal="true" aria-labelledby="authModalTitle"
        tabIndex={-1}
        onKeyDown={e => {
          if (e.key === 'Escape') handleClose();
          if (e.key === 'Enter') {
            if (step === 'email') handleSendCode();
            if (step === 'code') handleVerifyCode();
          }
        }}
      >
        <div className="modal-header"><h2 id="authModalTitle">Sign Up / Sign In</h2>
          <button className="modal-close" onClick={handleClose}>×</button>
        </div>
        
        <div className="modal-body">
          {step === "email" ? (
            <>
              <p>Enter your email to receive a verification code:</p>
              <p style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.55)', marginTop: '4px', marginBottom: '16px', fontWeight: '400' }}>
                {purpose === 'unlocking' ? '💡 New users will be automatically signed up' : 'New users will be automatically signed up'}
              </p>
              <div style={{ position: 'relative', width: '100%' }}>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  className="input-box"
                  autoFocus
                />
              </div>
              <button 
                className="button-primary" 
                onClick={handleSendCode}
                disabled={loading}
              >
                {loading ? "Sending..." : "Send Code"}
              </button>
            </>
          ) : (
            <>
              <p>Enter the 6-digit code sent to {email}:</p>
              <div style={{ position: 'relative', width: '100%' }}>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                  placeholder="123456"
                  className="input-box"
                  maxLength="6"
                  autoFocus
                  style={{
                    textAlign: 'center',
                    letterSpacing: '0.5em',
                    fontSize: '1.1rem',
                    fontWeight: '600'
                  }}
                />
              </div>
              
              {timer > 0 && (
                <p style={{ fontSize: '0.85rem', color: 'rgba(255, 255, 255, 0.65)', marginTop: '8px', fontWeight: '400' }}>
                  Code expires in: <strong style={{ color: 'rgba(255, 255, 255, 0.9)' }}>{formatTime(timer)}</strong>
                </p>
              )}
              
              <button 
                className="button-primary" 
                onClick={handleVerifyCode}
                disabled={loading || timer === 0}
              >
                {loading ? "Verifying..." : "Sign In"}
              </button>
              
              <div style={{ marginTop: '12px', textAlign: 'center' }}>
                <p style={{ fontSize: '0.875rem', color: 'rgba(255, 255, 255, 0.6)', marginBottom: '8px', fontWeight: '400' }}>
                  Didn't receive the code?
                </p>
                <button 
                  className="button-secondary" 
                  onClick={handleResendCode}
                  disabled={loading || resendCooldown > 0}
                  style={{ marginRight: '8px' }}
                >
                  {resendCooldown > 0 ? `Resend (${resendCooldown}s)` : "Resend Code"}
                </button>
                <button 
                  className="button-secondary" 
                  onClick={() => setStep("email")}
                >
                  Change Email
                </button>
              </div>
            </>
          )}
          
          {error && (
            <div className="error-text" aria-live="polite" style={{
              padding: '12px',
              marginTop: '12px',
              borderRadius: '10px',
              background: 'rgba(255, 123, 156, 0.2)',
              border: '1px solid rgba(255, 123, 156, 0.4)',
              color: '#ffb3c6',
              fontSize: '0.93rem',
              fontWeight: '500',
              boxShadow: '0 4px 12px rgba(255, 123, 156, 0.15)'
            }}>
              ⚠️ {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AuthModal;
