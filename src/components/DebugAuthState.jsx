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
          <div>Auth Cookies: {cookieState.hasCookies ? 'Present' : 'Not present'}</div>
          <div>Access Token Cookie: {cookieState.accessCookie ? 'Valid' : 'Missing/Invalid'}</div>
          <div>Refresh Token Cookie: {cookieState.refreshCookie ? 'Likely present' : 'Likely missing'}</div>
          
          <h4>localStorage Values:</h4>
          <div>User: {storedUser ? `Present (${storedUser.substring(0, 20)}...)` : 'Not present'}</div>
          
          <div style={{ marginTop: '10px' }}>
            <button 
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
                cursor: 'pointer'
              }}
            >
              Clear Auth Data
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DebugAuthState;
