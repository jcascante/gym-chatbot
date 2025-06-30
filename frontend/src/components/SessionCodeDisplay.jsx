import React, { useState } from 'react';
import './SessionCodeDisplay.css';

const SessionCodeDisplay = ({ sessionCode, onClose }) => {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(sessionCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy: ', err);
    }
  };

  return (
    <div className="session-code-overlay">
      <div className="session-code-modal">
        <div className="session-code-header">
          <h3>Your Session Code</h3>
          <button className="close-button" onClick={onClose}>×</button>
        </div>
        
        <div className="session-code-content">
          <p>Use this code to access your conversations on other devices:</p>
          
          <div className="session-code-display">
            <span className="session-code">{sessionCode}</span>
            <button 
              className="copy-button"
              onClick={copyToClipboard}
            >
              {copied ? '✓ Copied!' : '📋 Copy'}
            </button>
          </div>
          
          <div className="session-code-info">
            <p><strong>How to use:</strong></p>
            <ol>
              <li>Open MTC Assistant on another device</li>
              <li>Click "Join Session" on the login screen</li>
              <li>Enter this code: <strong>{sessionCode}</strong></li>
              <li>Your conversations will be available</li>
            </ol>
            
            <div className="session-code-warning">
              <p>⚠️ This code expires in 7 days. Keep it safe!</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SessionCodeDisplay; 