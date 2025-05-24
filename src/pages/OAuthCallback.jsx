// filepath: d:\wysypisko\backend\projekt\quiz-app\src\pages\OAuthCallback.jsx
import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../utils/constants';

const OAuthCallback = () => {
  const navigate = useNavigate();
  const [status, setStatus] = useState('Processing login...');
  const { verifyAuthState, updateAuthStateFromTokens } = useAuth();
  const processedRef = useRef(false);
  
  useEffect(() => {
    // Prevent multiple executions
    if (processedRef.current) {
      return;
    }
    
    const processOAuthLogin = async () => {
      try {
        processedRef.current = true;
        setStatus('Verifying authentication...');
        
        // Wait a bit for cookies to be set by the backend
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // First try to directly verify the auth state
        const isVerified = await verifyAuthState();
        
        if (isVerified) {
          console.log('OAuth login verified successfully');
          setStatus('Login successful!');
          setTimeout(() => navigate('/home'), 1000);
          return;
        }
        
        // If not verified, try to update auth state from tokens (ONE attempt only)
        setStatus('Updating authentication state...');
        const isUpdated = await updateAuthStateFromTokens();
        
        if (isUpdated) {
          console.log('Updated auth state from tokens successfully');
          setStatus('Login successful!');
          setTimeout(() => navigate('/home'), 1000);
          return;
        }
        
        // If all attempts fail, redirect to login
        console.error('OAuth authentication failed');
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
  }, []); // Remove dependencies to prevent re-execution

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
