// filepath: d:\wysypisko\backend\projekt\quiz-app\src\pages\OAuthCallback.jsx
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const OAuthCallback = () => {
  const navigate = useNavigate();
  const [status, setStatus] = useState('Processing login...');
  const { refreshUserState, updateAuthStateFromTokens } = useAuth();
  useEffect(() => {
    // Add a small delay to ensure cookies are properly set
    setTimeout(() => {
      updateAuthStateFromTokens()
        .then(success => {
          if (success) {
            console.log('Successfully updated user state from token');
          } else {
            console.warn('Could not update complete user state, using basic data');
            refreshUserState();
          }
          setStatus('Login successful...');
          setTimeout(() => navigate('/home'), 1000);
        })
        .catch(error => {
          console.error('Error during OAuth callback:', error);
          setStatus('Authentication error');
          setTimeout(() => navigate('/login'), 2000);
        });
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
