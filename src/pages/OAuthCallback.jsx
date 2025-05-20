// filepath: d:\wysypisko\backend\projekt\quiz-app\src\pages\OAuthCallback.jsx
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../utils/constants';

const OAuthCallback = () => {
  const navigate = useNavigate();
  const [status, setStatus] = useState('Processing login...');
  const { verifyAuthState, updateAuthStateFromTokens, refreshToken } = useAuth();
  
  useEffect(() => {
    const processOAuthLogin = async () => {
      try {
        setStatus('Verifying authentication...');
        
        // First try to directly verify the auth state
        const isVerified = await verifyAuthState();
        
        if (isVerified) {
          console.log('OAuth login verified successfully');
          setStatus('Login successful!');
          setTimeout(() => navigate('/home'), 1000);
          return;
        }
        
        // If not verified, try to update auth state from tokens
        setStatus('Updating authentication state...');
        const isUpdated = await updateAuthStateFromTokens();
        
        if (isUpdated) {
          console.log('Updated auth state from tokens successfully');
          setStatus('Login successful!');
          setTimeout(() => navigate('/home'), 1000);
          return;
        }
        
        // If still not authenticated, try refreshing the token
        setStatus('Refreshing authentication...');
        const isRefreshed = await refreshToken();
        
        if (isRefreshed && await verifyAuthState()) {
          console.log('Authentication refreshed successfully');
          setStatus('Login successful!');
          setTimeout(() => navigate('/home'), 1000);
          return;
        }
        
        // If all attempts fail, redirect to login
        console.error('All authentication attempts failed');
        setStatus('Authentication failed.');
        setTimeout(() => navigate('/login'), 2000);
      } catch (error) {
        console.error('Error processing OAuth callback:', error);
        setStatus('Authentication error');
        setTimeout(() => navigate('/login'), 2000);
      }
    };
    
    // Add a small delay to ensure cookies are properly set
    setTimeout(processOAuthLogin, 1000);
  }, [navigate, verifyAuthState, updateAuthStateFromTokens, refreshToken]);

  return (
    <div className="oauth-callback">
      <div className="container">
        <div className="auth-form">
          <h2>Processing Login</h2>
          <p>{status}</p>
          <div className="loading-spinner"></div>
        </div>
      </div>
    </div>
  );
};

export default OAuthCallback;
