import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './AuthForms.css';

const LoginForm = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login, createGuestSession, error, loading, clearError } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) return;

    clearError();
    const result = await login(username, password);

    if (!result.success) {
      // Error is already set in the context
      return;
    }
  };

  const handleGuestAccess = async () => {
    clearError();
    const result = await createGuestSession();

    if (!result.success) {
      // Error is already set in the context
      return;
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h2>Welcome to MTC Assistant</h2>
          <p>Sign in to continue or try as a guest</p>
        </div>

        {error && (
          <div className="auth-error">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              disabled={loading}
            />
          </div>

          <button 
            type="submit" 
            className={`auth-button primary ${loading ? 'loading' : ''}`}
            disabled={loading || !username.trim() || !password.trim()}
            title={!username.trim() || !password.trim() ? "Please fill in all fields" : ""}
          >
            {loading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        <div className="auth-divider">
          <span>or</span>
        </div>

        <button 
          onClick={handleGuestAccess}
          className="auth-button secondary"
          disabled={loading}
        >
          {loading ? 'Creating Guest Session...' : 'Continue as Guest'}
        </button>

        <div className="auth-footer">
          <p>
            Contact your administrator to create an account
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginForm; 