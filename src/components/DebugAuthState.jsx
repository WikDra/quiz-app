import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../utils/constants';

/**
 * Component for debugging authentication state
 * Only shown in development environment
 */
const DebugAuthState = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [isMinimized, setIsMinimized] = useState(true);
  const [cookieInfo, setCookieInfo] = useState({
    hasCookies: false,
    hasAuthCookie: false,
    cookieCount: 0
  });
  const { user, updateAuthStateFromTokens } = useAuth();
  const [serverData, setServerData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [panelPosition, setPanelPosition] = useState({ top: '10px', right: '10px', left: 'auto', bottom: 'auto' });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  
  // Create a ref to avoid re-renders when accessing the latest user state
  const userRef = useRef(user);
  
  // Update the ref when user changes
  useEffect(() => {
    userRef.current = user;
  }, [user]);

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
    // Use userRef.current instead of user to avoid dependency issues
    if (userRef.current) {
      fetch(`${API_BASE_URL}/api/debug/auth-state`, {
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
      .catch(err => console.error('Error checking auth debug endpoint:', err));
    }
  }, [API_BASE_URL]); // Removed user from dependencies and use userRef instead

  const fetchUserDebugData = useCallback(async () => {
    setLoading(true);
    setError(null);
      try {
      const response = await fetch(`${API_BASE_URL}/api/debug/current-user`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch user data');
      }
      
      setServerData(data);
    } catch (err) {
      console.error('Error fetching user debug data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [API_BASE_URL]);

  const refreshUserState = useCallback(async () => {
    setLoading(true);
    try {
      await updateAuthStateFromTokens();
      updateCookieInfo();
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }, [updateAuthStateFromTokens, updateCookieInfo]);
  
  // Start dragging the panel
  const handleMouseDown = useCallback((e) => {
    setIsDragging(true);
    // Calculate the offset from the pointer to the panel corner
    const rect = e.currentTarget.getBoundingClientRect();
    setDragOffset({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    });
  }, []);

  // Handle dragging the panel
  const handleMouseMove = useCallback((e) => {
    if (!isDragging) return;
    
    // Set new position based on mouse position and offset
    setPanelPosition({
      top: `${e.clientY - dragOffset.y}px`,
      left: `${e.clientX - dragOffset.x}px`,
      right: 'auto',
      bottom: 'auto'
    });
  }, [isDragging, dragOffset]);

  // End dragging
  const handleMouseUp = useCallback(() => {
    if (!isDragging) return;
    
    setIsDragging(false);
    
    // Save position to localStorage
    try {
      const positionToSave = {
        top: panelPosition.top,
        left: panelPosition.left,
        right: panelPosition.right,
        bottom: panelPosition.bottom
      };
      localStorage.setItem('debugPanelPosition', JSON.stringify(positionToSave));
    } catch (err) {
      console.error('Failed to save debug panel position:', err);
    }
  }, [isDragging, panelPosition]);

  // Add and remove document event listeners for mouse events
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }
    
    // Clean up
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);
  
  // Load saved position
  useEffect(() => {
    // Try to load saved position
    try {
      const savedPosition = localStorage.getItem('debugPanelPosition');
      if (savedPosition) {
        setPanelPosition(JSON.parse(savedPosition));
      }
    } catch (err) {
      console.error('Failed to load debug panel position:', err);
    }
  }, []);
  
  // Check at component mount if we're in development mode
  useEffect(() => {
    // Only show in development by default
    const shouldShow = process.env.NODE_ENV === 'development';
    
    // Allow override with localStorage
    try {
      const debugSetting = localStorage.getItem('showAuthDebug');
      if (debugSetting !== null) {
        setIsVisible(debugSetting === 'true');
      } else {
        setIsVisible(shouldShow);
      }    
    } catch (err) {
      setIsVisible(shouldShow);
    }    
    
    // Initial cookie check
    updateCookieInfo();
    
    // Setup interval for cookie updates
    const intervalId = setInterval(() => {
      updateCookieInfo();
    }, 30000);
    
    return () => {
      clearInterval(intervalId);
    };
  }, [updateCookieInfo]);
  
  // Provide keyboard shortcut to toggle panel
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl+Alt+D to toggle debug panel
      if (e.ctrlKey && e.altKey && e.key === 'd') {
        setIsVisible(prev => {
          // Save new state right away, using the current prev value
          try {
            localStorage.setItem('showAuthDebug', (!prev).toString());
          } catch (err) {
            console.error('Failed to save debug panel visibility:', err);          
          }
          return !prev;
        });
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);
  
  // Don't render if not visible
  if (!isVisible) {
    return null;
  }

  // Style for the floating panel
  const panelStyle = {
    position: 'fixed',
    ...panelPosition,
    zIndex: 9999,
    backgroundColor: isMinimized ? 'rgba(0,123,255,0.8)' : 'rgba(43,58,74,0.95)',
    color: 'white',
    borderRadius: '8px',
    boxShadow: '0 4px 8px rgba(0,0,0,0.3)',
    transition: 'all 0.2s ease, left 0s, top 0s',
    width: isMinimized ? 'auto' : '350px',
    maxWidth: '90vw',
    opacity: isDragging ? 0.7 : 1,
    cursor: isDragging ? 'grabbing' : 'default'
  };

  const headerStyle = {
    padding: '6px 12px',
    cursor: 'grab',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottom: isMinimized ? 'none' : '1px solid #3a4d63',
    borderRadius: '8px 8px 0 0',
    userSelect: 'none',
    fontSize: '13px',
    fontWeight: 'bold'
  };

  const contentStyle = {
    padding: isMinimized ? '0' : '12px',
    maxHeight: isMinimized ? '0' : '70vh',
    overflow: 'hidden',
    transition: 'all 0.3s ease',
  };

  const buttonStyle = {
    appearance: 'none',
    border: 'none',
    color: 'white',
    padding: '5px 10px',
    borderRadius: '4px',
    cursor: loading ? 'not-allowed' : 'pointer',
    fontSize: '11px',
    opacity: 0.9,
    transition: 'opacity 0.2s',
    flex: 1
  };

  return (
    <div style={panelStyle}>
      <div 
        style={headerStyle}
        onMouseDown={handleMouseDown}
      >
        <span style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <span 
            onClick={(e) => {
              e.stopPropagation();
              setIsMinimized(!isMinimized);
            }}
            style={{ cursor: 'pointer' }}
          >
            {isMinimized ? '▲' : '▼'}
          </span>
          <span>Auth Debug</span>
        </span>
        
        <span 
          style={{ 
            fontSize: '14px', 
            marginLeft: '10px', 
            cursor: 'pointer',
            padding: '0 4px'
          }}
          onClick={(e) => {
            e.stopPropagation();
            setIsVisible(false);
            try {
              localStorage.setItem('showAuthDebug', 'false');
            } catch {}
          }}
          title="Close (Ctrl+Alt+D to show again)"
        >
          ×
        </span>
      </div>
      
      <div style={contentStyle}>
        {!isMinimized && (
          <>
            <div style={{ marginBottom: '10px', display: 'flex', gap: '8px' }}>
              <button 
                onClick={fetchUserDebugData} 
                disabled={loading}
                style={{
                  ...buttonStyle,
                  backgroundColor: '#007bff',
                }}
                title="Get current user data from server"
              >
                {loading ? '...' : 'Get Server Data'}
              </button>
              
              <button 
                onClick={refreshUserState} 
                disabled={loading}
                style={{
                  ...buttonStyle,
                  backgroundColor: '#28a745',
                }}
                title="Refresh authentication state from server"
              >
                {loading ? '...' : 'Refresh Auth'}
              </button>
            </div>
            
            {error && (
              <div style={{ 
                color: '#ff4d4d', 
                backgroundColor: 'rgba(255, 77, 77, 0.1)', 
                padding: '8px', 
                borderRadius: '4px', 
                marginBottom: '10px',
                fontSize: '11px'
              }}>
                Error: {error}
              </div>
            )}
            
            <div style={{ marginBottom: '8px' }}>
              <h4 style={{ color: '#4dabf7', fontSize: '13px', margin: '0 0 4px 0' }}>
                Auth Status: {user ? '✅ Logged In' : '❌ Not Logged In'}
              </h4>
              {user && (
                <div style={{ color: '#e2e2e2', fontSize: '11px' }}>
                  ID: {user.id} | Name: {user.fullName || user.username}
                </div>
              )}
            </div>
            
            <div style={{ 
              backgroundColor: 'rgba(26, 37, 51, 0.8)', 
              padding: '8px', 
              borderRadius: '4px',
              marginBottom: '8px',
              fontSize: '11px'
            }}>
              <h4 style={{ color: '#4dabf7', fontSize: '13px', margin: '0 0 4px 0' }}>Cookie Info:</h4>
              <div style={{ color: '#e2e2e2' }}>
                <div>Client Cookies: {cookieInfo.cookieCount}</div>
                {cookieInfo.serverCookieCount !== undefined && (
                  <div>Server Cookies: {cookieInfo.serverCookieCount}</div>
                )}
                <div>JWT Valid: {cookieInfo.jwt_valid ? '✅ Yes' : '❌ No'}</div>
              </div>
            </div>
            
            {user && (
              <div>
                <h4 style={{ color: '#4dabf7', fontSize: '13px', margin: '8px 0 4px 0' }}>
                  <span>Client-side User Data</span>
                </h4>
                <pre style={{ 
                  backgroundColor: 'rgba(26, 37, 51, 0.8)', 
                  color: '#e2e2e2',
                  padding: '8px', 
                  borderRadius: '4px',
                  overflow: 'auto',
                  maxHeight: '100px',
                  fontFamily: 'monospace',
                  fontSize: '10px',
                  border: '1px solid rgba(58, 77, 99, 0.5)',
                  margin: '0'
                }}>
                  {JSON.stringify(user, null, 2)}
                </pre>
              </div>
            )}
            
            {serverData && (
              <div style={{ marginTop: '8px' }}>
                <h4 style={{ color: '#4dabf7', fontSize: '13px', margin: '8px 0 4px 0' }}>
                  <span>Server-side User Data</span>
                </h4>
                <pre style={{ 
                  backgroundColor: 'rgba(26, 37, 51, 0.8)', 
                  color: '#e2e2e2',
                  padding: '8px', 
                  borderRadius: '4px',
                  overflow: 'auto',
                  maxHeight: '100px',
                  fontFamily: 'monospace',
                  fontSize: '10px',
                  border: '1px solid rgba(58, 77, 99, 0.5)',
                  margin: '0'
                }}>
                  {JSON.stringify(serverData, null, 2)}
                </pre>
              </div>
            )}
            
            <div style={{ 
              marginTop: '8px',
              fontSize: '10px',
              color: '#aaa',
              textAlign: 'center'
            }}>
              Hold and drag title bar to move • Ctrl+Alt+D to toggle
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default DebugAuthState;
