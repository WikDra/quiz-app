import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../utils/constants';

/**
 * This component helps diagnose issues with JWT tokens and authentication
 * You can include it temporarily in your app for debugging purposes
 */
const TokenDiagnostics = () => {
  const { user, verifyAuthState, refreshToken } = useAuth();
  const [cookiesText, setCookiesText] = useState('');
  const [tokenStatus, setTokenStatus] = useState('Unknown');
  const [refreshStatus, setRefreshStatus] = useState('Not Attempted');
  const [showDetails, setShowDetails] = useState(false);
  const [diagnosticLog, setDiagnosticLog] = useState([]);

  // Add to diagnostic log
  const logMessage = useCallback((message, type = 'info') => {
    const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
    setDiagnosticLog(prev => [...prev, { 
      time: timestamp, 
      message, 
      type 
    }]);
  }, []);

  // Fetch cookies info
  const updateCookiesInfo = useCallback(() => {
    try {
      setCookiesText(document.cookie || 'No cookies found');
      const cookies = document.cookie.split(';').map(c => c.trim());
      
      logMessage(`Found ${cookies.length} cookies`, 'info');
      cookies.forEach(cookie => {
        const name = cookie.split('=')[0];
        logMessage(`Cookie: ${name}`, 'detail');
      });
      
      const hasAccessToken = document.cookie.includes('access_token_cookie');
      const hasRefreshToken = document.cookie.includes('refresh_token_cookie');
      
      if (hasAccessToken) {
        logMessage('Access token cookie present', 'success');
      } else {
        logMessage('Access token cookie missing', 'error');
      }
      
      if (hasRefreshToken) {
        logMessage('Refresh token cookie present', 'success');
      } else {
        logMessage('Refresh token cookie missing', 'error');
      }
    } catch (err) {
      logMessage(`Error reading cookies: ${err.message}`, 'error');
    }
  }, [logMessage]);

  // Check token status
  const checkTokenStatus = useCallback(async () => {
    logMessage('Checking token status...', 'info');
    try {
      const isValid = await verifyAuthState();
      if (isValid) {
        setTokenStatus('Valid');
        logMessage('JWT token is valid', 'success');
      } else {
        setTokenStatus('Invalid or Expired');
        logMessage('JWT token is invalid or expired', 'error');
      }
    } catch (err) {
      setTokenStatus('Error verifying');
      logMessage(`Error verifying token: ${err.message}`, 'error');
    }
  }, [verifyAuthState, logMessage]);

  // Attempt token refresh
  const attemptTokenRefresh = useCallback(async () => {
    logMessage('Attempting token refresh...', 'info');
    setRefreshStatus('Attempting...');
    try {
      const success = await refreshToken();
      if (success) {
        setRefreshStatus('Success');
        logMessage('Token refresh successful', 'success');
        
        // Update cookies info after refresh
        updateCookiesInfo();
      } else {
        setRefreshStatus('Failed');
        logMessage('Token refresh failed', 'error');
      }
    } catch (err) {
      setRefreshStatus('Error');
      logMessage(`Error refreshing token: ${err.message}`, 'error');
    }
  }, [refreshToken, logMessage, updateCookiesInfo]);

  // Test API connection
  const testApiConnection = useCallback(async () => {
    logMessage('Testing API connection...', 'info');
    try {
      const response = await fetch(`${API_BASE_URL}/api/health`, {
        method: 'GET',
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        logMessage(`API health check success: ${data.message || 'OK'}`, 'success');
      } else {
        logMessage(`API health check failed: ${response.status} ${response.statusText}`, 'error');
      }
    } catch (err) {
      logMessage(`API connection error: ${err.message}`, 'error');
    }
  }, [API_BASE_URL, logMessage]);

  // Initialize
  useEffect(() => {
    logMessage('Token diagnostics initialized', 'info');
    updateCookiesInfo();
  }, [updateCookiesInfo, logMessage]);

  return (
    <div style={{
      position: 'fixed',
      bottom: '10px',
      right: '10px',
      width: showDetails ? '500px' : '50px',
      maxHeight: '80vh',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      color: 'white',
      borderRadius: '5px',
      padding: '10px',
      fontFamily: 'monospace',
      fontSize: '12px',
      zIndex: 9999,
      overflowY: 'auto',
      transition: 'width 0.3s ease'
    }}>
      <button 
        onClick={() => setShowDetails(!showDetails)}
        style={{
          position: 'absolute',
          top: '5px',
          right: '5px',
          background: 'none',
          border: 'none',
          color: 'white',
          fontSize: '16px',
          cursor: 'pointer'
        }}
      >
        {showDetails ? '×' : '🔍'}
      </button>
      
      {showDetails && (
        <>
          <h3>JWT Token Diagnostics</h3>
          
          <div style={{ marginBottom: '10px' }}>
            <strong>User status:</strong> {user ? 'Logged in' : 'Not logged in'}
          </div>
          
          <div style={{ marginBottom: '10px' }}>
            <strong>Token status:</strong> {tokenStatus}
            <button 
              onClick={checkTokenStatus} 
              style={{ marginLeft: '10px', fontSize: '10px' }}
            >
              Check
            </button>
          </div>
          
          <div style={{ marginBottom: '10px' }}>
            <strong>Token refresh:</strong> {refreshStatus}
            <button 
              onClick={attemptTokenRefresh} 
              style={{ marginLeft: '10px', fontSize: '10px' }}
            >
              Refresh
            </button>
          </div>
          
          <div style={{ marginBottom: '10px' }}>
            <button onClick={testApiConnection} style={{ fontSize: '10px' }}>
              Test API Connection
            </button>
            <button onClick={updateCookiesInfo} style={{ marginLeft: '10px', fontSize: '10px' }}>
              Update Cookie Info
            </button>
          </div>
          
          <div style={{ marginBottom: '10px' }}>
            <strong>Cookies:</strong>
            <div style={{ 
              background: '#222', 
              padding: '5px', 
              borderRadius: '3px',
              wordBreak: 'break-all',
              maxHeight: '60px',
              overflowY: 'auto'
            }}>
              {cookiesText || 'No cookies found'}
            </div>
          </div>
          
          <div>
            <strong>Diagnostic Log:</strong>
            <div style={{ 
              background: '#222', 
              padding: '5px', 
              borderRadius: '3px',
              height: '200px',
              overflowY: 'auto'
            }}>
              {diagnosticLog.map((entry, i) => (
                <div 
                  key={i} 
                  style={{ 
                    color: entry.type === 'error' ? '#ff5555' : 
                           entry.type === 'success' ? '#55ff55' :
                           entry.type === 'detail' ? '#aaaaaa' : '#ffffff',
                    marginBottom: '2px'
                  }}
                >
                  [{entry.time}] {entry.message}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default TokenDiagnostics;
