import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { STORAGE_KEYS } from '../utils/constants';

/**
 * Component for debugging authentication state
 * Only shown in development environment
 */
const DebugAuthState = () => {
  const [isVisible, setIsVisible] = useState(false);
  const { user, tokens } = useAuth();
  
  // Get localStorage values
  const storedUser = localStorage.getItem(STORAGE_KEYS.USER);
  const accessToken = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
  
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
        <div>
          <h4>Auth Context State:</h4>
          <div>User: {user ? `ID: ${user.id}` : 'Not logged in'}</div>
          <div>Access Token: {tokens?.accessToken ? 'Present' : 'Not present'}</div>
          <div>Refresh Token: {tokens?.refreshToken ? 'Present' : 'Not present'}</div>
          
          <h4>localStorage Values:</h4>
          <div>User: {storedUser ? `Present (${storedUser.substring(0, 20)}...)` : 'Not present'}</div>
          <div>Access Token: {accessToken ? `Present (${accessToken.substring(0, 20)}...)` : 'Not present'}</div>
          <div>Refresh Token: {refreshToken ? 'Present' : 'Not present'}</div>
          
          <div style={{ marginTop: '10px' }}>
            <button 
              onClick={() => {
                localStorage.removeItem(STORAGE_KEYS.USER);
                localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
                localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
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
