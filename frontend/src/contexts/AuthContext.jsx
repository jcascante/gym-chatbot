import React, { createContext, useContext, useState, useEffect } from 'react';
import { API_BASE_URL } from '../config';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('authToken'));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check if user is authenticated on mount
  useEffect(() => {
    console.log("Token:", token);
    if (token) {
      checkAuthStatus();
    } else {
      setLoading(false);
    }
  }, []); // Only run once on mount, not when token changes

  const checkAuthStatus = async () => {
    console.log("Checking auth status with token:", token);
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'ngrok-skip-browser-warning': 'true'
        }
      });
      console.log("/auth/me status:", response.status);
      console.log("/auth/me response headers:", response.headers);

      if (response.ok) {
        const userData = await response.json();
        console.log("User data received:", userData);
        setUser(userData);
      } else {
        const errorData = await response.text();
        console.error("Auth check failed with status:", response.status, "Error:", errorData);
        // Token is invalid, clear it
        logout();
      }
    } catch (error) {
      console.error('Auth check failed with exception:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  // Add a timeout to prevent loading state from getting stuck
  useEffect(() => {
    if (loading) {
      const timeout = setTimeout(() => {
        console.warn('Loading state timeout - resetting to false');
        setLoading(false);
      }, 10000); // 10 second timeout

      return () => clearTimeout(timeout);
    }
  }, [loading]);

  const login = async (username, password) => {
    setError(null);
    setLoading(true);
    console.log("Starting login process for user:", username);
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true'
        },
        body: JSON.stringify({ username, password })
      });

      const data = await response.json();
      console.log("Login response status:", response.status);
      console.log("Login response data:", data);

      if (response.ok) {
        setToken(data.access_token);
        setUser(data.user);
        localStorage.setItem('authToken', data.access_token);
        console.log("Login success, token:", data.access_token);
        console.log("Login success, user:", data.user);
        return { success: true };
      } else {
        setError(data.detail || 'Login failed');
        return { success: false, error: data.detail };
      }
    } catch (error) {
      console.error('Login network error:', error);
      setError('Network error. Please try again.');
      return { success: false, error: 'Network error' };
    } finally {
      setLoading(false);
    }
  };

  const createGuestSession = async () => {
    setError(null);
    setLoading(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/guest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true'
        }
      });

      const data = await response.json();

      if (response.ok) {
        setToken(data.access_token);
        setUser(data.user);
        localStorage.setItem('authToken', data.access_token);
        
        // Store session code for guest users
        if (data.session_code) {
          localStorage.setItem('guestSessionCode', data.session_code);
        }
        
        return { success: true, session_code: data.session_code };
      } else {
        setError(data.detail || 'Guest session creation failed');
        return { success: false, error: data.detail };
      }
    } catch (error) {
      setError('Network error. Please try again.');
      return { success: false, error: 'Network error' };
    } finally {
      setLoading(false);
    }
  };

  const joinGuestSession = async (sessionCode) => {
    setError(null);
    setLoading(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/guest/join`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true'
        },
        body: JSON.stringify({ session_code: sessionCode })
      });

      const data = await response.json();

      if (response.ok) {
        setToken(data.access_token);
        setUser(data.user);
        localStorage.setItem('authToken', data.access_token);
        localStorage.setItem('guestSessionCode', sessionCode);
        return { success: true };
      } else {
        setError(data.detail || 'Invalid session code');
        return { success: false, error: data.detail };
      }
    } catch (error) {
      setError('Network error. Please try again.');
      return { success: false, error: 'Network error' };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    console.log("Logging out!");
    setUser(null);
    setToken(null);
    setError(null);
    localStorage.removeItem('authToken');
    localStorage.removeItem('guestSessionCode');
    // Removed window.location.reload() to prevent double refresh
  };

  const clearError = () => {
    setError(null);
  };

  const value = {
    user,
    token,
    loading,
    error,
    login,
    createGuestSession,
    joinGuestSession,
    logout,
    clearError,
    isAuthenticated: !!token
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export { AuthContext }; 