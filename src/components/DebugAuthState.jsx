import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { STORAGE_KEYS, API_BASE_URL } from '../utils/constants';

/**
 * Component for debugging authentication state
 * Only shown in development environment
 */
const DebugAuthState = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [cookieState, setCookieState] = useState({ 
    hasCookies: false, 
    accessCookie: false, 
    refreshCookie: false 
  });
  const [authCookieExists, setAuthCookieExists] = useState(false);
  const [cookieCount, setCookieCount] = useState(0);
  const { user } = useAuth();
  
  // Get localStorage values (still used for user data)
  const storedUser = localStorage.getItem(STORAGE_KEYS.USER);
  
  // Check for cookies (indirectly by testing a profile fetch)
  useEffect(() => {
    const checkAuthCookies = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/users/me/profile`, {
          method: 'GET',
          credentials: 'include'
        });
        
        setCookieState({
          hasCookies: response.ok,
          accessCookie: response.ok, // If the request worked, access token cookie exists
          refreshCookie: response.ok // We can't directly check refresh cookies, but assume it's there too
        });
      } catch (error) {
        console.error('Cookie check failed:', error);
        setCookieState({ 
          hasCookies: false, 
          accessCookie: false, 
          refreshCookie: false 
        });
      }
    };
    
    if (isVisible) {
      checkAuthCookies();
    }
  }, [isVisible]);
    // Check cookie state periodically
  useEffect(() => {
    const updateCookieInfo = () => {
      const cookies = document.cookie;
      const hasAuthCookie = cookies.includes('auth_success');
      const count = cookies.split(';').filter(c => c.trim().length > 0).length;
      
      setAuthCookieExists(hasAuthCookie);
      setCookieCount(count);
      
      // Log auth state info for debugging
      if (user && !hasAuthCookie) {
        console.warn('[AuthStateLogger] User present but no auth cookies - possible sync issue');
      }
    };
    
    updateCookieInfo();
    const timer = setInterval(updateCookieInfo, 2000); // Check more frequently
    return () => clearInterval(timer);
  }, [user]);
  
  // This effect logs auth state changes to help with debugging
  useEffect(() => {
    console.log('[AuthStateLogger] Auth state changed:', {
      isLoggedIn: !!user,
      userId: user?.id || null,
      hasCookies: cookieState.hasCookies
    });
  }, [user, cookieState]);
  
  if (import.meta.env.DEV !== true) {
    return null; // Only show in development
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
        <div>          <h4>Auth Context State:</h4>
          <div>User: {user ? `ID: ${user.id}` : 'Not logged in'}</div>
          
          <h4>HTTP-Only Cookies:</h4>
          <div>Auth Cookies: {cookieState.hasCookies ? 'Present ✅' : 'Not present ❌'}</div>
          <div>Access Token Cookie: {cookieState.accessCookie ? 'Valid ✅' : 'Missing/Invalid ❌'}</div>
          <div>Refresh Token Cookie: {cookieState.refreshCookie ? 'Likely present ✅' : 'Likely missing ❌'}</div>
          <div>Auth Success Cookie: {authCookieExists ? 'Present ✅' : 'Missing ❌'}</div>
          <div>Total Cookies: {cookieCount}</div>
          
          <h4>localStorage Values:</h4>
          <div>User: {storedUser ? `Present ✅ (${storedUser.substring(0, 20)}...)` : 'Not present ❌'}</div>
          
          <div style={{ marginTop: '10px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>            <button 
              onClick={async () => {
                try {
                  // Call the logout API endpoint to clear cookies
                  await fetch(`${API_BASE_URL}/api/logout`, {
                    method: 'POST',
                    credentials: 'include'
                  });
                } catch (error) {
                  console.error('Error during debug logout:', error);
                }
                
                // Also clear localStorage
                localStorage.removeItem(STORAGE_KEYS.USER);
                window.location.reload();
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
              Clear Auth Data
            </button>
            
            <button 
              onClick={async () => {
                try {
                  // Check auth status
                  const response = await fetch(`${API_BASE_URL}/api/debug/auth`, {
                    credentials: 'include'
                  });
                  
                  if (response.ok) {
                    const debugInfo = await response.json();
                    console.log("Debug auth info:", debugInfo);
                    alert(JSON.stringify(debugInfo, null, 2));
                  } else {
                    alert("Debug endpoint returned an error");
                  }
                } catch (error) {
                  console.error('Error checking debug auth:', error);
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
            </button>            <button 
              onClick={async () => {
                try {
                  // Test cookies specifically
                  // First, handle OPTIONS request explicitly
                  await fetch(`${API_BASE_URL}/api/test-auth-cookies`, {
                    method: 'OPTIONS',
                    credentials: 'include',
                    headers: {
                      'Access-Control-Request-Method': 'GET',
                      'Access-Control-Request-Headers': 'Content-Type',
                    }
                  });
                  
                  // Then make the actual request
                  const response = await fetch(`${API_BASE_URL}/api/test-auth-cookies`, {
                    method: 'GET',
                    credentials: 'include',
                    headers: { 'Content-Type': 'application/json' }
                  });
                  
                  if (response.ok) {
                    const testInfo = await response.json();
                    console.log("Cookie test results:", testInfo);
                    alert(`Cookie test results:\n- JWT Valid: ${testInfo.jwt_valid}\n- User ID: ${testInfo.user_id || 'None'}\n- Error: ${testInfo.error || 'None'}\n- Cookies: ${Object.keys(testInfo.cookies).length}`);
                    
                    // Check visible cookies after test
                    console.log("Current cookies:", document.cookie);
                    setTimeout(() => {
                      // Check if cookies were successfully set
                      const currentCookies = document.cookie;
                      setCookieState(prevState => ({
                        ...prevState,
                        // Update state if cookies changed
                        hasCookies: currentCookies.includes('test_visible_cookie')
                      }));
                    }, 500);
                  } else {
                    alert("Cookie test endpoint returned an error");
                  }
                } catch (error) {
                  console.error('Error testing cookies:', error);
                  alert(`Error: ${error.message}`);
                }
              }}
              style={{
                background: '#2196F3',
                color: 'white',
                border: 'none',
                padding: '5px 10px',
                borderRadius: '3px',
                cursor: 'pointer',
                flex: '1'
              }}
            >
              Test Cookies
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DebugAuthState;
