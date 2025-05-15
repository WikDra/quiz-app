import { useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

/**
 * A utility component that logs authentication state changes
 * This is useful for debugging authorization issues
 */
const AuthStateLogger = () => {
  const { user, tokens } = useAuth();
  
  useEffect(() => {
    console.log('[AuthStateLogger] Auth state changed:', { 
      isLoggedIn: !!user,
      userId: user?.id || null,
      hasAccessToken: !!tokens?.accessToken,
      hasRefreshToken: !!tokens?.refreshToken
    });
    
    if (!user && tokens?.accessToken) {
      console.warn('[AuthStateLogger] Tokens present but no user - possible sync issue');
    } else if (user && !tokens?.accessToken) {
      console.warn('[AuthStateLogger] User present but no tokens - possible sync issue');
    }
  }, [user, tokens]);
  
  // This is a utility component that doesn't render anything
  return null;
};

export default AuthStateLogger;
