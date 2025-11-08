/**
 * Header Component
 * Application header with title, sign in button, and user menu
 * 
 * @component
 * @param {Function} onSignIn - Callback when user clicks sign in
 * @param {Function} onSignOut - Callback when user clicks sign out
 */

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useAuth } from "../contexts/AuthContext";

const Header = React.memo(({ onSignIn, onSignOut }) => {
  const { isLoggedIn, email } = useAuth();
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleMenuToggle = useCallback(() => {
    setShowMenu(prev => !prev);
  }, []);

  return (
    <header className="app-header">
      <div className="header-content">
        <h1 className="header-title">Trading Path Builder</h1>
        <div className="header-actions">
          {isLoggedIn ? (
            <div className="user-menu" ref={menuRef}>
              <button onClick={handleMenuToggle}>
                {email} ▾
              </button>
              {showMenu && (
                <div className="dropdown">
                  <button onClick={onSignOut}>Logout</button>
                </div>
              )}
            </div>
          ) : (
            <button className="button-primary" onClick={onSignIn}>Sign In</button>
          )}
        </div>
      </div>
    </header>
  );
});

Header.displayName = 'Header';

export default Header;
