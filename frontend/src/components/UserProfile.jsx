import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './UserProfile.css';

const UserProfile = () => {
  const { user, logout } = useAuth();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const handleLogout = (e) => {
    e.preventDefault();
    e.stopPropagation();
    logout();
    setIsDropdownOpen(false);
  };

  const toggleDropdown = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDropdownOpen(!isDropdownOpen);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen]);

  if (!user) return null;

  return (
    <div className="user-profile" ref={dropdownRef}>
      <button 
        className="user-profile-button"
        onClick={toggleDropdown}
        type="button"
      >
        <div className="user-avatar">
          {user.username.charAt(0).toUpperCase()}
        </div>
        <span className="user-name">{user.username}</span>
        <span className="user-type">
          {user.is_guest ? 'Guest' : 'User'}
        </span>
        <span className="dropdown-arrow">▼</span>
      </button>

      {isDropdownOpen && (
        <div className="user-dropdown">
          <div className="dropdown-header">
            <div className="dropdown-avatar">
              {user.username.charAt(0).toUpperCase()}
            </div>
            <div className="dropdown-user-info">
              <div className="dropdown-username">{user.username}</div>
              <div className="dropdown-type">
                {user.is_guest ? 'Guest Session' : 'Registered User'}
              </div>
            </div>
          </div>
          
          <div className="dropdown-divider"></div>
          
          <button 
            className="dropdown-item logout-button"
            onClick={handleLogout}
            type="button"
          >
            <span className="logout-icon">🚪</span>
            Sign Out
          </button>
        </div>
      )}
    </div>
  );
};

export default UserProfile; 