import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./style.css";

// Suppress browser extension errors (Grammarly, writing assistants, etc.)
const originalError = console.error;
console.error = (...args) => {
  // Filter out extension-related errors
  const errorMessage = args.join(' ');
  if (
    errorMessage.includes('Extension context invalidated') ||
    errorMessage.includes('writing_mode_assistant') ||
    errorMessage.includes('chrome-extension://') ||
    errorMessage.includes('moz-extension://') ||
    errorMessage.includes('safari-extension://')
  ) {
    // Silently ignore extension errors
    return;
  }
  // Log all other errors normally
  originalError.apply(console, args);
};

// Also catch unhandled errors and rejections
window.addEventListener('error', (event) => {
  const errorMessage = event.message || event.error?.message || '';
  if (
    errorMessage.includes('Extension context invalidated') ||
    errorMessage.includes('writing_mode_assistant') ||
    errorMessage.includes('chrome-extension://') ||
    errorMessage.includes('moz-extension://') ||
    errorMessage.includes('safari-extension://')
  ) {
    event.preventDefault(); // Prevent error from showing in console
    return false;
  }
});

window.addEventListener('unhandledrejection', (event) => {
  const errorMessage = event.reason?.message || event.reason?.toString() || '';
  if (
    errorMessage.includes('Extension context invalidated') ||
    errorMessage.includes('writing_mode_assistant') ||
    errorMessage.includes('chrome-extension://') ||
    errorMessage.includes('moz-extension://') ||
    errorMessage.includes('safari-extension://')
  ) {
    event.preventDefault(); // Prevent error from showing in console
    return false;
  }
});

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
