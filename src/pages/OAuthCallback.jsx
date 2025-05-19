// filepath: d:\wysypisko\backend\projekt\quiz-app\src\pages\OAuthCallback.jsx
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../utils/constants';

const OAuthCallback = () => {
  const navigate = useNavigate();
  const [status, setStatus] = useState('Processing login...');
  const { refreshUserState, updateAuthStateFromTokens } = useAuth();
  
  useEffect(() => {
    // Try to ensure auth_success cookie is set (as a backup if server didn't set it)
    try {
      const expires = new Date();
      expires.setTime(expires.getTime() + 3600 * 1000); // 1 hour
      document.cookie = `auth_success=true; path=/; expires=${expires.toUTCString()}; SameSite=None; Secure`;
      
      // Log the cookie state
      console.log('Current cookies:', document.cookie);
      console.log('Set auth_success cookie as backup');
    } catch (error) {
      console.error('Error setting backup auth_success cookie:', error);
    }
  
    // Add a small delay to ensure cookies are properly set
    setTimeout(() => {
      let retryCount = 0;
      const maxRetries = 3;
      
      const tryGetProfile = async () => {
        try {
          console.log(`Attempt ${retryCount + 1} to get user profile...`);
          const success = await updateAuthStateFromTokens();
          
          if (success) {
            console.log('Successfully updated user state from token');
            setStatus('Login successful...');
            setTimeout(() => navigate('/home'), 1000);
          } else {
            console.warn(`Attempt ${retryCount + 1} failed to get user profile`);
            
            if (retryCount < maxRetries) {
              retryCount++;
              setStatus(`Retrying... (${retryCount}/${maxRetries})`);
              setTimeout(tryGetProfile, 1000); // Try again after 1 second
            } else {
              console.warn('Could not update complete user state after retries, using basic data');
              const userFromStorage = refreshUserState();
              
              if (userFromStorage) {
                setStatus('Using cached user data...');
                setTimeout(() => navigate('/home'), 1000);
              } else {
                setStatus('Authentication failed.');
                setTimeout(() => navigate('/login'), 2000);
              }
            }
          }
        } catch (error) {
          console.error('Error during OAuth callback:', error);
          setStatus('Authentication error');
          setTimeout(() => navigate('/login'), 2000);
        }
      };
      
      tryGetProfile();
    }, 500); // Added delay to ensure cookies are set
  }, [navigate, refreshUserState, updateAuthStateFromTokens]);

  return (
    <div className="oauth-callback">
      <div className="container">
        <div className="auth-form">
          <h2>Processing Login</h2>
          <p>{status}</p>
          <div className="loading-spinner"></div>
        </div>
      </div>
    </div>  );
};

export default OAuthCallback;
