// filepath: d:\wysypisko\backend\projekt\quiz-app\src\pages\OAuthCallback.jsx
import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL, STORAGE_KEYS } from '../utils/constants';

const OAuthCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('Processing login...');
  const { setTokens, refreshUserState, updateAuthStateFromTokens } = useAuth();

  useEffect(() => {
    const accessToken = searchParams.get('access_token');
    const refreshToken = searchParams.get('refresh_token');
    const error = searchParams.get('error');

    if (error) {
      console.error('OAuth error:', error);
      setStatus('Authentication error');
      setTimeout(() => navigate('/login'), 2000);
      return;
    }

    if (accessToken && refreshToken) {
      setTokens({ accessToken, refreshToken });
      console.log('OAuth tokens saved');
      
      try {
        const payload = JSON.parse(atob(accessToken.split('.')[1]));
        if (payload && payload.sub) {          // Zapisz podstawowe dane użytkownika z uwzględnieniem wymaganych właściwości
          const userData = { 
            id: payload.sub, 
            email: payload.email || null,
            stats: { quizzes: [], bestTime: '0min', correctAnswers: 0 }
          };
          localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
          
          // Spróbuj pobrać pełne dane używając funkcji z kontekstu
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
            });
        }
      } catch (err) {
        console.error('Error processing token:', err);
        setStatus('Error processing authentication data');
        setTimeout(() => navigate('/login'), 2000);
      }
    } else {
      navigate('/login');
    }
  }, [searchParams, navigate, setTokens, refreshUserState, updateAuthStateFromTokens]);

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
