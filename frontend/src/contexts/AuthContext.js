import React, { createContext, useContext, useState, useEffect } from "react";

// Create the Auth Context
const AuthContext = createContext(null);

// Storage keys
const STORAGE_KEYS = {
  TOKEN: "trading_path_token",
  USER_ID: "trading_path_user_id",
  EMAIL: "trading_path_email",
  EXPIRES_AT: "trading_path_expires_at"
};

// Token expiration time (24 hours in milliseconds)
const TOKEN_EXPIRATION_MS = 24 * 60 * 60 * 1000;

/**
 * AuthProvider component that wraps the app and provides authentication state
 */
export const AuthProvider = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userId, setUserId] = useState(null);
  const [email, setEmail] = useState(null);
  const [token, setToken] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  /**
   * Check if token is expired
   */
  const isTokenExpired = (expiresAt) => {
    if (!expiresAt) return true;
    return Date.now() > parseInt(expiresAt);
  };

  /**
   * Load authentication state from localStorage on mount
   */
  useEffect(() => {
    const loadAuthState = () => {
      try {
        const storedToken = localStorage.getItem(STORAGE_KEYS.TOKEN);
        const storedUserId = localStorage.getItem(STORAGE_KEYS.USER_ID);
        const storedEmail = localStorage.getItem(STORAGE_KEYS.EMAIL);
        const storedExpiresAt = localStorage.getItem(STORAGE_KEYS.EXPIRES_AT);

        // Check if all required data exists
        if (storedToken && storedUserId && storedEmail && storedExpiresAt) {
          // Check if token is expired
          if (isTokenExpired(storedExpiresAt)) {
            console.log("Token expired, clearing auth state");
            clearAuthState();
          } else {
            // Restore auth state
            setToken(storedToken);
            setUserId(storedUserId);
            setEmail(storedEmail);
            setIsLoggedIn(true);
            console.log("Auth state loaded from localStorage");
          }
        }
      } catch (error) {
        console.error("Error loading auth state:", error);
        clearAuthState();
      } finally {
        setIsLoading(false);
      }
    };

    loadAuthState();

    // Listen for 401 unauthorized events from API client
    const handleUnauthorized = () => {
      console.log("Received unauthorized event, logging out");
      clearAuthState();
    };

    window.addEventListener("auth:unauthorized", handleUnauthorized);

    // Cleanup
    return () => {
      window.removeEventListener("auth:unauthorized", handleUnauthorized);
    };
  }, []);

  /**
   * Login function - stores auth data in state and localStorage
   */
  const login = (authToken, userIdValue, emailValue) => {
    try {
      const expiresAt = Date.now() + TOKEN_EXPIRATION_MS;

      // Store in localStorage
      localStorage.setItem(STORAGE_KEYS.TOKEN, authToken);
      localStorage.setItem(STORAGE_KEYS.USER_ID, userIdValue);
      localStorage.setItem(STORAGE_KEYS.EMAIL, emailValue);
      localStorage.setItem(STORAGE_KEYS.EXPIRES_AT, expiresAt.toString());

      // Update state
      setToken(authToken);
      setUserId(userIdValue);
      setEmail(emailValue);
      setIsLoggedIn(true);

      console.log("User logged in:", { userId: userIdValue, email: emailValue });
    } catch (error) {
      console.error("Error during login:", error);
      throw error;
    }
  };

  /**
   * Logout function - clears auth data from state and localStorage
   */
  const logout = () => {
    clearAuthState();
    console.log("User logged out");
  };

  /**
   * Clear all auth state and localStorage
   */
  const clearAuthState = () => {
    // Clear localStorage
    localStorage.removeItem(STORAGE_KEYS.TOKEN);
    localStorage.removeItem(STORAGE_KEYS.USER_ID);
    localStorage.removeItem(STORAGE_KEYS.EMAIL);
    localStorage.removeItem(STORAGE_KEYS.EXPIRES_AT);

    // Clear state
    setToken(null);
    setUserId(null);
    setEmail(null);
    setIsLoggedIn(false);
  };

  /**
   * Get current auth token (useful for API calls)
   */
  const getToken = () => {
    const storedToken = localStorage.getItem(STORAGE_KEYS.TOKEN);
    const storedExpiresAt = localStorage.getItem(STORAGE_KEYS.EXPIRES_AT);

    // Check if token is expired
    if (storedToken && storedExpiresAt && !isTokenExpired(storedExpiresAt)) {
      return storedToken;
    }

    // Token is expired or doesn't exist
    if (isLoggedIn) {
      logout(); // Auto-logout on expired token
    }
    return null;
  };

  /**
   * Check if user is authenticated and token is valid
   */
  const isAuthenticated = () => {
    const storedExpiresAt = localStorage.getItem(STORAGE_KEYS.EXPIRES_AT);
    return isLoggedIn && token && !isTokenExpired(storedExpiresAt);
  };

  const value = {
    isLoggedIn,
    userId,
    email,
    token,
    isLoading,
    login,
    logout,
    getToken,
    isAuthenticated
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

/**
 * Custom hook to use the Auth context
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export default AuthContext;

