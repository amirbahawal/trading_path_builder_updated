import React, { useState, useEffect, useRef } from "react";
import { useAuth } from "../contexts/AuthContext";

const Header = ({ onSignIn, onSignOut }) => {
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

  return (
    <header className="app-header">
      <div className="header-content">
        <h1 className="header-title">Trading Path Builder</h1>
        <div className="header-actions">
          {isLoggedIn ? (
            <div className="user-menu" ref={menuRef}>
              <button onClick={() => setShowMenu(!showMenu)}>
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
};

export default Header;
