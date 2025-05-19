import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../utils/constants';

/**
 * This component is for debugging user data sync issues
 */
const UserDebugPanel = () => {
  const { user, updateAuthStateFromTokens } = useAuth();
  const [serverData, setServerData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchUserDebugData = async () => {
    setLoading(true);
    setError(null);
    
    try {      const response = await fetch(`${API_BASE_URL}/api/debug/current-user`, {
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
  };

  const refreshUserState = async () => {
    setLoading(true);
    try {
      await updateAuthStateFromTokens();
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  if (!user) {
    return <div>Not logged in - no user data to debug</div>;
  }
  return (
    <div style={{ 
      backgroundColor: '#2b3a4a', 
      padding: '20px', 
      borderRadius: '8px',
      marginTop: '20px',
      color: 'white',
      boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
    }}>
      <h3 style={{ color: '#ffffff', marginBottom: '15px' }}>User Data Debug</h3>
      
      <div style={{ marginBottom: '15px' }}>
        <button 
          onClick={fetchUserDebugData} 
          disabled={loading}
          style={{
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            padding: '8px 15px',
            borderRadius: '4px',
            marginRight: '10px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Loading...' : 'Fetch Server Data'}
        </button>
        
        <button 
          onClick={refreshUserState} 
          disabled={loading}
          style={{
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            padding: '8px 15px',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Loading...' : 'Refresh User State'}
        </button>
      </div>
      
      {error && (
        <div style={{ 
          color: '#ff4d4d', 
          backgroundColor: 'rgba(255, 77, 77, 0.1)', 
          padding: '10px', 
          borderRadius: '4px', 
          marginBottom: '15px' 
        }}>
          Error: {error}
        </div>
      )}
      
      <div style={{ 
        display: 'flex', 
        gap: '20px', 
        flexDirection: window.innerWidth < 768 ? 'column' : 'row'
      }}>
        <div style={{ flex: 1 }}>
          <h4 style={{ color: '#4dabf7', marginBottom: '10px' }}>Client-side User Data:</h4>
          <pre style={{ 
            backgroundColor: '#1a2533', 
            color: '#ffffff',
            padding: '15px', 
            borderRadius: '4px',
            overflow: 'auto',
            maxHeight: '300px',
            fontFamily: 'monospace',
            fontSize: '14px',
            border: '1px solid #3a4d63'
          }}>
            {JSON.stringify(user, null, 2)}
          </pre>
        </div>
        
        {serverData && (
          <div style={{ flex: 1 }}>
            <h4 style={{ color: '#4dabf7', marginBottom: '10px' }}>Server-side User Data:</h4>
            <pre style={{ 
              backgroundColor: '#1a2533', 
              color: '#ffffff',
              padding: '15px', 
              borderRadius: '4px',
              overflow: 'auto',
              maxHeight: '300px',
              fontFamily: 'monospace',
              fontSize: '14px',
              border: '1px solid #3a4d63'
            }}>
              {JSON.stringify(serverData, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserDebugPanel;
