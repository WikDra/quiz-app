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
        
        // Try to refresh the token with force=true to bypass the time check
        const refreshSuccess = await refreshToken(true);
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
    let mounted = true;
    
    const runVerification = async () => {
      if (!mounted || !user) return;
      
      // Get last verification time
      const lastVerifyTime = localStorage.getItem('lastAuthVerifyTime');
      const now = Date.now();
      
      // Don't verify if we checked in the last 30 seconds
      if (lastVerifyTime && now - parseInt(lastVerifyTime, 10) < 30000) {
        return;
      }
      
      await performVerification();
    };

    // First verification on mount with slight delay to prevent race conditions
    const initialTimeout = setTimeout(runVerification, 1000);
    
    // Then run verification every 5 minutes
    const interval = setInterval(runVerification, 5 * 60 * 1000);
    
    setTimer(interval);

    return () => {
      mounted = false;
      clearTimeout(initialTimeout);
      if (timer) {
        clearInterval(timer);
      }
    };
  }, [performVerification, user]);

  // Ten komponent nie renderuje nic, jest tylko do weryfikacji stanu auth
  return null;
};

export default AuthVerifier;
