import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../utils/constants';

/**
 * A utility component that logs authentication state changes
 * This is useful for debugging authorization issues
 */
const AuthStateLogger = () => {
  const { user, refreshUserState } = useAuth();
  const [hasCookies, setHasCookies] = useState(false);
  // Check if cookies are valid whenever user state changes
  useEffect(() => {
    const checkAuthCookies = async () => {
      try {
        // Add a small delay to give other authentication processes a chance to complete
        await new Promise(resolve => setTimeout(resolve, 300));
        
        const response = await fetch(`${API_BASE_URL}/api/user/profile`, {
          method: 'GET',
          credentials: 'include',
          // Only use Content-Type header to avoid any CORS issues
          headers: {
            'Content-Type': 'application/json'
          }
        });
          if (response.ok) {
          // Try to get the data to also verify the content
          const data = await response.json();
          setHasCookies(true);
          
          // Debug premium status
          console.log('[AuthStateLogger] User premium status check:', { 
            apiPremiumStatus: data.has_premium_access,
            currentPremiumStatus: user?.has_premium_access,
            fullApiResponse: data
          });
          
          // Check if has_premium_access status has changed
          if (data.has_premium_access !== user?.has_premium_access) {
            console.log('[AuthStateLogger] Premium status changed, refreshing user data');
            if (user && typeof refreshUserState === 'function') {
              refreshUserState();
            }
          }
        } else {
          setHasCookies(false);
        }
      } catch (error) {
        console.error('[AuthStateLogger] Error checking auth cookies:', error);
        setHasCookies(false);
      }
    };
    
    checkAuthCookies();
  }, [user, API_BASE_URL, refreshUserState]);
  
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
