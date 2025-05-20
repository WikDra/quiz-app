import React, { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

/**
 * Komponent odpowiedzialny za weryfikację stanu uwierzytelniania co określony czas
 * Zapobiega sytuacji, gdy użytkownik jest nadal zalogowany w UI, ale token JWT wygasł
 * Dodatkowo obsługuje odświeżanie tokenów JWT przed ich wygaśnięciem
 */
const AuthVerifier = () => {
  const { verifyAuthState, refreshToken, logout, user } = useAuth();
  const [timer, setTimer] = useState(null);
  const [lastVerified, setLastVerified] = useState(Date.now());
  const [consecutiveFailures, setConsecutiveFailures] = useState(0);
  const navigate = useNavigate();

  // Verification logic extracted to a function
  const performVerification = useCallback(async () => {
    console.log("AuthVerifier: weryfikacja stanu uwierzytelniania...");
    try {
      // If no user, don't bother verifying
      if (!user) {
        console.log("AuthVerifier: No active user, skipping verification");
        return;
      }

      // Try to verify auth state
      const isValid = await verifyAuthState();
      
      if (isValid) {
        console.log("AuthVerifier: Auth state valid");
        setLastVerified(Date.now());
        setConsecutiveFailures(0);
      } else {
        console.warn("AuthVerifier: Auth state invalid, attempting token refresh");
        setConsecutiveFailures(prev => prev + 1);
        
        // Try to refresh the token
        const refreshSuccess = await refreshToken();
        
        if (refreshSuccess) {
          console.log("AuthVerifier: Token refreshed successfully");
          setConsecutiveFailures(0);
        } else {
          console.error("AuthVerifier: Token refresh failed");
          
          // After 3 consecutive failures, log out
          if (consecutiveFailures >= 2) { // 2 + current = 3 total
            console.error("AuthVerifier: Multiple auth verification failures, logging out");
            await logout();
            navigate('/login');
          }
        }
      }
    } catch (error) {
      console.error("AuthVerifier: błąd weryfikacji stanu uwierzytelniania", error);
      setConsecutiveFailures(prev => prev + 1);
      
      // After 3 consecutive failures, log out
      if (consecutiveFailures >= 2) { // 2 + current = 3 total
        console.error("AuthVerifier: Multiple auth verification failures, logging out");
        await logout();
        navigate('/login');
      }
    }
  }, [verifyAuthState, refreshToken, logout, user, consecutiveFailures, navigate]);

  useEffect(() => {
    // First verification on mount 
    if (user) {
      performVerification();
    }
    
    // Uruchom weryfikację co 5 minut (5 * 60 * 1000 ms)
    const interval = setInterval(performVerification, 5 * 60 * 1000); 
    
    setTimer(interval);

    // Czyszczenie interwału po odmontowaniu komponentu
    return () => {
      if (timer) {
        clearInterval(timer);
      }
    };
  }, [performVerification, user]);

  // Ten komponent nie renderuje nic, jest tylko do weryfikacji stanu auth
  return null;
};

export default AuthVerifier;
