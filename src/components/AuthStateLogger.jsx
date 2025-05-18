import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../utils/constants';

/**
 * A utility component that logs authentication state changes
 * This is useful for debugging authorization issues
 */
const AuthStateLogger = () => {
  const { user } = useAuth();
  const [hasCookies, setHasCookies] = useState(false);
  
  // Check if cookies are valid whenever user state changes
  useEffect(() => {
    const checkAuthCookies = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/users/me/profile`, {
          method: 'GET',
          credentials: 'include'
        });
        setHasCookies(response.ok);
      } catch (error) {
        setHasCookies(false);
      }
    };
    
    checkAuthCookies();
  }, [user]);
  
  useEffect(() => {
    console.log('[AuthStateLogger] Auth state changed:', { 
      isLoggedIn: !!user,
      userId: user?.id || null,
      hasCookies: hasCookies,
    });
    
    if (!user && hasCookies) {
      console.warn('[AuthStateLogger] Auth cookies present but no user - possible sync issue');
    } else if (user && !hasCookies) {
      console.warn('[AuthStateLogger] User present but no auth cookies - possible sync issue');
    }
  }, [user, hasCookies]);
  
  // This is a utility component that doesn't render anything
  return null;
};

export default AuthStateLogger;
