import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../utils/constants';

/**
 * Component for debugging authentication state
 * Only shown in development environment
 */
const DebugAuthState = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [cookieInfo, setCookieInfo] = useState({
    hasCookies: false,
    hasAuthCookie: false,
    cookieCount: 0
  });
  const { user } = useAuth();
    // Check for cookies and update state
  const updateCookieInfo = useCallback(() => {
    const cookies = document.cookie;
    const hasAuthCookie = cookies.includes('auth_success');
    const count = cookies.split(';').filter(c => c.trim().length > 0).length;
    
    // First update with client-side info
    setCookieInfo({
      hasCookies: count > 0,
      hasAuthCookie,
      cookieCount: count
    });
    
    // Then check with the server to get more accurate info about HttpOnly cookies
    if (user) {
      fetch(`${API_BASE_URL}/api/debug/auth`, {
        credentials: 'include'
      })
      .then(response => {
        if (response.ok) {
          return response.json();
        }
        return null;
      })
      .then(data => {
        if (data) {
          // Update with server information which includes HttpOnly cookies
          setCookieInfo(info => ({
            ...info,
            hasCookies: data.jwt_access_present || data.jwt_refresh_present,
            serverCookieCount: Object.keys(data.cookies || {}).length,
            jwt_valid: !!data.jwt_identity
          }));
        }
      })
      .catch(err => {
        console.error("Error checking auth cookies:", err);
      });
    }
    
    // Log auth state info for debugging
    if (user && !hasAuthCookie) {
      console.warn('[AuthStateLogger] User present but no auth cookies - possible sync issue');
    }
  }, [user]);
  
  // Check for cookies periodically
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
      hasCookies: cookieInfo.hasAuthCookie
    });
  }, [user, cookieInfo.hasAuthCookie]);
  
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
        <div>          <h4>Auth Status:</h4>
          <div>User: {user ? `ID: ${user.id}, Email: ${user.email || 'N/A'}` : 'Not logged in'}</div>
          
          <h4>Cookies:</h4>
          <div>Client Cookies: {cookieInfo.cookieCount > 0 ? `${cookieInfo.cookieCount} cookies ✅` : 'None detected in browser ❌'}</div>
          <div>Auth Success Cookie: {cookieInfo.hasAuthCookie ? 'Present ✅' : 'Missing ❌'}</div>
          <div>JWT Cookies: {cookieInfo.hasCookies ? 'Present on server ✅' : 'Not detected ❌'}</div>
          {cookieInfo.serverCookieCount !== undefined && (
            <div>Server Cookies: {cookieInfo.serverCookieCount} detected</div>
          )}
          {cookieInfo.jwt_valid !== undefined && (
            <div>JWT Valid: {cookieInfo.jwt_valid ? 'Yes ✅' : 'No ❌'}</div>
          )}
            <div style={{ marginTop: '10px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            <button 
              onClick={async () => {
                try {
                  const response = await fetch(`${API_BASE_URL}/api/debug/auth`, {
                    credentials: 'include'
                  });
                  
                  if (response.ok) {
                    const data = await response.json();
                    console.log("Debug auth info:", data);
                    alert(JSON.stringify({
                      jwt_present: data.jwt_access_present,
                      user_id: data.jwt_identity,
                      cookies_count: Object.keys(data.cookies).length,
                      cookies: Object.keys(data.cookies)
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
              onClick={() => {
                try {
                  // Set a test cookie directly from JavaScript
                  document.cookie = "js_test_cookie=true; path=/; SameSite=None; Secure";
                  
                  // Force creation of the auth_success cookie
                  const expires = new Date();
                  expires.setTime(expires.getTime() + 3600 * 1000); // 1 hour
                  document.cookie = `auth_success=true; path=/; expires=${expires.toUTCString()}; SameSite=None; Secure`;
                  
                  // Update immediately to show the new cookie
                  setTimeout(updateCookieInfo, 100);
                  
                  alert("Test cookies set directly from JavaScript. If they don't appear, your browser may be blocking cookies.");
                } catch (error) {
                  console.error("Error setting test cookies:", error);
                  alert(`Failed to set test cookies: ${error.message}`);
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
              Test Set Cookie
            </button>
            
            <button
              onClick={async () => {
                try {
                  // Force refresh cookies
                  const response = await fetch(`${API_BASE_URL}/api/token/refresh`, {
                    method: 'POST',
                    credentials: 'include'
                  });
                  if (response.ok) {
                    alert("Token refreshed successfully");
                    updateCookieInfo();
                  } else {
                    alert("Failed to refresh token");
                  }
                } catch (error) {
                  console.error('Error:', error);
                  alert(`Error: ${error.message}`);
                }
              }}
              style={{
                background: '#009688',
                color: 'white',
                border: 'none',
                padding: '5px 10px',
                borderRadius: '3px',
                cursor: 'pointer',
                flex: '1'
              }}
            >
              Refresh Token
            </button>
            
            <button 
              onClick={async () => {
                try {
                  // Call the logout API endpoint to clear cookies
                  await fetch(`${API_BASE_URL}/api/logout`, {
                    method: 'POST',
                    credentials: 'include'
                  });
                  window.location.reload();
                } catch (error) {
                  console.error('Error:', error);
                  alert(`Error: ${error.message}`);
                }
              }}
              style={{
                background: '#f44336',
                color: 'white',
                border: 'none',
                padding: '5px 10px',
                borderRadius: '3px',
                cursor: 'pointer',
                flex: '1'
              }}
            >
              Logout
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DebugAuthState;
