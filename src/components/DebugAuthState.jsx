import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../utils/constants';
import { authApi } from '../utils/apiUtils';

/**
 * Component for debugging cookie-based authentication state
 * Only shown in development environment
 */
const DebugAuthState = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [cookieInfo, setCookieInfo] = useState({
    hasCookies: false,
    hasSession: false,
    cookieCount: 0,
    cookieNames: [],
    isAuthenticated: false,
    user: null
  });
  const { user } = useAuth();

  // Check for cookies and update state
  const updateCookieInfo = useCallback(() => {
    const cookies = document.cookie;
    console.log("Document cookies:", cookies);
    
    // Parse cookies into an object
    const cookieObj = cookies.split(';').reduce((acc, cookie) => {
      const [key, value] = cookie.trim().split('=');
      if (key && key.length > 0) {
        acc[key] = value;
      }
      return acc;
    }, {});
    
    console.log("Parsed cookies:", cookieObj);
    
    // Check for session cookie (either real session or our visible indicator)
    const hasSession = 'session' in cookieObj || 
                      'visible_session' in cookieObj || 
                      'session_debug' in cookieObj;
    const count = Object.keys(cookieObj).length;
    
    // Update with client-side info
    setCookieInfo({
      hasCookies: count > 0,
      hasSession,
      cookieCount: count,
      cookieNames: Object.keys(cookieObj),
      isAuthenticated: false,
      user: null
    });
    
    // Check with the server for auth status
    fetch(`${API_BASE_URL}/api/auth/debug`, {
      credentials: 'include',
      cache: 'no-store' // Don't cache auth check
    })
    .then(response => {
      if (response.ok) {
        return response.json();
      }
      return null;
    })
    .then(data => {
      if (data) {
        console.log("Auth debug info:", data);
        setCookieInfo(info => ({
          ...info,
          isAuthenticated: data.authenticated,
          hasSession: data.session_cookie_present,
          serverCookieCount: Object.keys(data.cookies || {}).length,
          serverCookieNames: Object.keys(data.cookies || {}),
          sessionData: data.session_data,
          user: data.user
        }));
      }
    })
    .catch(err => {
      console.error("Error checking auth state:", err);
    });
  }, [user]);

  // Check cookies periodically
  useEffect(() => {
    updateCookieInfo();
    const timer = setInterval(updateCookieInfo, 2000);
    return () => clearInterval(timer);
  }, [updateCookieInfo]);

  // Log auth state changes
  useEffect(() => {
    console.log('[AuthStateLogger] Auth state changed:', {
      isLoggedIn: !!user,
      userId: user?.id || null,
      hasSession: cookieInfo.hasSession,
      isAuthenticated: cookieInfo.isAuthenticated
    });
  }, [user, cookieInfo.hasSession, cookieInfo.isAuthenticated]);
  
  // Only show in development
  if (import.meta.env.DEV !== true) {
    return null;
  }
  
  return (
    <div style={{ 
      position: 'fixed',
      bottom: '10px',
      right: '10px',
      background: 'rgba(0,0,0,0.8)',
      color: '#fff',
      padding: '10px',
      borderRadius: '5px',
      fontSize: '12px',
      zIndex: 9999,
      maxWidth: '400px',
      maxHeight: isVisible ? '400px' : '30px',
      overflow: 'auto',
      transition: 'max-height 0.3s'
    }}>
      <button 
        onClick={() => setIsVisible(!isVisible)}
        style={{
          background: 'transparent',
          border: 'none',
          color: '#fff',
          cursor: 'pointer',
          padding: '0',
          margin: '0'
        }}
      >
        {isVisible ? 'Hide Auth Debug' : 'Show Auth Debug'}
      </button>
      
      {isVisible && (
        <div>
          <h4>Auth Status:</h4>
          <div>User: {user ? `ID: ${user.id}, Email: ${user.email || 'N/A'}` : 'Not logged in'}</div>
          
          <h4>Cookies:</h4>
          <div>Client Cookies: {cookieInfo.cookieCount > 0 ? `${cookieInfo.cookieCount} cookies ✅` : 'None detected in browser ❌'}</div>
          <div>Cookie Names: {cookieInfo.cookieNames?.join(', ') || 'None'}</div>
          <div>Session Cookie: {cookieInfo.hasSession ? 'Present ✅' : 'Missing ❌'}</div>
          <div>Server Auth: {cookieInfo.isAuthenticated ? 'Authenticated ✅' : 'Not authenticated ❌'}</div>
          {cookieInfo.serverCookieCount !== undefined && (
            <div>Server Cookies: {cookieInfo.serverCookieCount} detected</div>
          )}
          {cookieInfo.serverCookieNames && (
            <div>Server Cookie Names: {cookieInfo.serverCookieNames.join(', ')}</div>
          )}
          {cookieInfo.sessionData && (
            <div>
              <h4>Session Data:</h4>
              <div>User ID in Session: {cookieInfo.sessionData.user_id || 'None'}</div>
              <div>Session ID: {cookieInfo.sessionData.session_id || 'None'}</div>
              <div>Fresh: {cookieInfo.sessionData.fresh ? 'Yes' : 'No'}</div>
            </div>
          )}
            
          <div style={{ marginTop: '10px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button 
              onClick={async () => {
                try {
                  const response = await fetch(`${API_BASE_URL}/api/auth/debug`, {
                    credentials: 'include'
                  });
                  
                  if (response.ok) {
                    const data = await response.json();
                    console.log("Debug auth info:", data);
                    alert(JSON.stringify({
                      authenticated: data.authenticated,
                      user_id: data.user?.id,
                      session_info: data.session_data,
                      cookies_count: Object.keys(data.cookies || {}).length,
                      cookies: data.cookies
                    }, null, 2));
                  } else {
                    alert("Failed to get debug info");
                  }
                } catch (error) {
                  console.error('Error:', error);
                  alert(`Error: ${error.message}`);
                }
              }}
              style={{
                background: '#4285F4',
                color: 'white',
                border: 'none',
                padding: '5px 10px',
                borderRadius: '3px',
                cursor: 'pointer',
                flex: '1'
              }}
            >
              Debug Auth
            </button>
            
            <button
              onClick={async () => {
                try {
                  const response = await fetch(`${API_BASE_URL}/api/auth/set-session`, {
                    credentials: 'include'
                  });
                  
                  if (response.ok) {
                    const data = await response.json();
                    console.log("Set session response:", data);
                    if (data.cookie_set) {
                      alert("Session cookie explicitly set. Check cookie status again.");
                      updateCookieInfo();
                    } else {
                      alert("Failed to set session cookie: " + data.message);
                    }
                  } else {
                    alert("Failed to set session cookie");
                  }
                } catch (error) {
                  console.error('Error:', error);
                  alert(`Error: ${error.message}`);
                }
              }}
              style={{
                background: '#FF9800',
                color: 'white',
                border: 'none',
                padding: '5px 10px',
                borderRadius: '3px',
                cursor: 'pointer',
                flex: '1'
              }}
            >
              Set Session Cookie
            </button>
            
            <button              onClick={async () => {
                try {
                  const response = await authApi.refreshToken();
                  console.log("Refresh response:", response);
                  if (response.success) {
                    updateCookieInfo();
                    alert("Session refreshed successfully");
                  } else {
                    alert("Failed to refresh session: " + response.message);
                  }
                } catch (error) {
                  console.error("Error refreshing session:", error);
                  alert(`Failed to refresh session: ${error.message}`);
                }
              }}
              style={{
                background: '#4CAF50',
                color: 'white',
                border: 'none',
                padding: '5px 10px',
                borderRadius: '3px',
                cursor: 'pointer',
                flex: '1'
              }}
            >
              Refresh Session
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DebugAuthState;
