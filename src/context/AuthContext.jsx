import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { API_BASE_URL, API_ENDPOINTS, STORAGE_KEYS, USER_LEVELS } from '../utils/constants';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState([]);
  const [error, setError] = useState(null);
  const [tokenRefreshTimer, setTokenRefreshTimer] = useState(null);

  // Create refs for functions that have circular dependencies
  const scheduleTokenRefreshRef = useRef(() => {});
  const verifyAuthStateRef = useRef(() => {});
  const refreshTokenRef = useRef(() => {});
  const logoutRef = useRef(() => {});

  // Funkcja do broadcasta wylogowania do innych kart
  const broadcastLogoutToOtherTabs = useCallback(() => {
    try {
      // Use localStorage event to notify other tabs
      localStorage.setItem('logout_broadcast', Date.now().toString());
      // Remove it immediately to trigger the event in other tabs
      localStorage.removeItem('logout_broadcast');
    } catch (error) {
      console.error('Error broadcasting logout to other tabs:', error);
    }
  }, []);

  // Wylogowanie użytkownika
  const logout = useCallback(async (logoutFromAllDevices = false) => {
    try {
      // Clear token refresh timer
      if (tokenRefreshTimer) {
        clearTimeout(tokenRefreshTimer);
        setTokenRefreshTimer(null);
      }
      
      // Call the API to clear cookies and blacklist tokens
      const response = await fetch(`${API_BASE_URL}/logout`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          logout_all: logoutFromAllDevices
        })
      });
      
      if (!response.ok) {
        console.warn("API logout endpoint nie zwrócił poprawnej odpowiedzi:", response.status);
      } else {
        const data = await response.json();
        console.log("Logout successful:", data);
        
        // If we logged out from all devices, broadcast to other tabs
        if (logoutFromAllDevices) {
          broadcastLogoutToOtherTabs();
        }
      }
    } catch (error) {
      console.error("Błąd podczas wylogowywania:", error);
    } finally {
      // Clear local state regardless of API success
      setUser(null);
      localStorage.removeItem(STORAGE_KEYS.USER);
      localStorage.removeItem('cachedUsers');
      localStorage.removeItem('lastUsersFetch');
      localStorage.removeItem('lastTokenRefresh');
      localStorage.removeItem('tokenExpiration');
      
      // Broadcast logout to other tabs
      broadcastLogoutToOtherTabs();
      
      // Opcjonalnie przekieruj na stronę logowania
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
  }, [API_BASE_URL, tokenRefreshTimer]);
  
  // Update ref to point to the latest version of the function
  logoutRef.current = logout;

  // Listen for logout broadcasts from other tabs
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'logout_broadcast' && e.newValue) {
        console.log('Logout broadcast received from another tab');
        // Another tab logged out, clear our state
        setUser(null);
        localStorage.removeItem(STORAGE_KEYS.USER);
        localStorage.removeItem('cachedUsers');
        localStorage.removeItem('lastUsersFetch');
        
        // Redirect to login if not already there
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  // Funkcja do sprawdzania, czy użytkownik jest zalogowany poprzez weryfikację JWT
  const verifyAuthState = useCallback(async () => {
    const MIN_INTERVAL = 5000; // 5 seconds between checks
    const lastVerifyTime = localStorage.getItem('lastAuthVerifyTime');
    const now = Date.now();

    if (lastVerifyTime) {
      const timeSinceLastVerify = now - parseInt(lastVerifyTime, 10);
      if (timeSinceLastVerify < MIN_INTERVAL) {
        // Use cached state if available
        const cachedUser = localStorage.getItem(STORAGE_KEYS.USER);
        if (cachedUser) {
          try {
            const parsedUser = JSON.parse(cachedUser);
            if (parsedUser && parsedUser.id) {
              return true;
            }
          } catch (err) {
            console.warn('Invalid cached user data:', err);
          }
        }
        return false;
      }
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout

      const response = await fetch(`${API_BASE_URL}/users/me`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      localStorage.setItem('lastAuthVerifyTime', now.toString());
      
      if (response.ok) {
        const userData = await response.json();
        const sanitizedUser = {
          ...userData,
          avatar: userData.avatar_url || userData.avatar || 'https://i.pravatar.cc/150?img=3',
          fullName: userData.username || userData.fullName || 'User',
          level: userData.level || 'Początkujący',
          stats: userData.stats || {
            quizzes: 0,
            bestTime: '0min',
            correctAnswers: 0
          },
          lastVerified: now
        };
        
        setUser(sanitizedUser);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(sanitizedUser));
        
        // Only schedule refresh if we don't have an active timer and no recent refresh
        const lastSchedule = localStorage.getItem('lastTokenRefreshSchedule');
        const shouldSchedule = !tokenRefreshTimer && 
          (!lastSchedule || now - parseInt(lastSchedule, 10) > 60000); // 1 minute cooldown
        
        if (shouldSchedule) {
          scheduleTokenRefreshRef.current();
        }
        return true;
      } else {
        if (response.status === 401) {
          setUser(null);
          localStorage.removeItem(STORAGE_KEYS.USER);
          return false;
        }
        // For other errors, try to use cached data
        const cachedUser = localStorage.getItem(STORAGE_KEYS.USER);
        if (cachedUser) {
          try {
            const parsedUser = JSON.parse(cachedUser);
            if (parsedUser && parsedUser.id && now - parsedUser.lastVerified < 24 * 60 * 60 * 1000) {
              console.warn('Using cached auth state due to API error');
              return true;
            }
          } catch (err) {
            console.warn('Invalid cached user data:', err);
          }
        }
        setUser(null);
        localStorage.removeItem(STORAGE_KEYS.USER);
        return false;
      }
    } catch (err) {
      console.error('Błąd podczas weryfikacji stanu uwierzytelniania:', err);
      const cachedUser = localStorage.getItem(STORAGE_KEYS.USER);
      if (err.name === 'AbortError' || err.message.includes('Failed to fetch')) {
        if (cachedUser) {
          try {
            const parsedUser = JSON.parse(cachedUser);
            if (parsedUser && parsedUser.id && now - parsedUser.lastVerified < 24 * 60 * 60 * 1000) {
              console.warn('Using cached auth state due to network error');
              return true;
            }
          } catch (parseErr) {
            console.warn('Invalid cached user data:', parseErr);
          }
        }
      }
      setUser(null);
      localStorage.removeItem(STORAGE_KEYS.USER);
      return false;
    }
  }, [API_BASE_URL, tokenRefreshTimer]);

  // Update ref to point to the latest version of the function
  verifyAuthStateRef.current = verifyAuthState;
const TOKEN_REFRESH_INTERVAL = 270000; // 4.5 minutes (slightly less than backend expiry)
const MINIMUM_REFRESH_INTERVAL = 30000; // 30 seconds
let refreshTimeout = null;

  // Function to refresh token when it's about to expire
  const refreshToken = useCallback(async (force = false) => {
    const now = Date.now();

    try {
      if (!force) {
        const lastRefresh = localStorage.getItem('lastTokenRefresh');
        if (lastRefresh && now - parseInt(lastRefresh, 10) < MINIMUM_REFRESH_INTERVAL) {
          console.log("Skipping token refresh - too soon since last refresh");
          return true;
        }
      }

      console.log("Attempting to refresh access token...");

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout

      // Attempt to refresh token
      const response = await fetch(`${API_BASE_URL}/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Important: needed for cookies
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const data = await response.json();
        console.log("Access token refreshed successfully");
        
        // Store refresh time
        localStorage.setItem('lastTokenRefresh', now.toString());
        
        // Cancel any existing refresh timeout
        if (refreshTimeout) {
          clearTimeout(refreshTimeout);
        }
        
        // Schedule next refresh
        refreshTimeout = setTimeout(() => {
          refreshTokenRef.current(true).catch(err => {
            console.error('Error in scheduled token refresh:', err);
          });
        }, TOKEN_REFRESH_INTERVAL);
        
        return true;
      } else {
        const errorText = await response.text();
        console.error("Failed to refresh token:", errorText);
        if (response.status === 401) {
          console.warn("Token refresh failed with 401, logging out");
          await logoutRef.current();
          return false;
        }
        const isStillValid = await verifyAuthStateRef.current();
        if (!isStillValid) {
          console.warn("Auth state invalid after token refresh failure, logging out");
          await logoutRef.current();
        }
        return false;
      }
    } catch (err) {
      console.error('Error refreshing token:', err);
      if (err.name === 'AbortError') {
        console.warn('Token refresh request timed out');
      }
      return false;
    }
  }, [API_BASE_URL]);

  // Update ref to point to the latest version of the function
  refreshTokenRef.current = refreshToken;

  // Schedule token refresh function with debouncing and error prevention
  const scheduleTokenRefresh = useCallback(() => {
    // Clear any existing timer first
    if (tokenRefreshTimer) {
      clearTimeout(tokenRefreshTimer);
      setTokenRefreshTimer(null);
    }

    // Prevent too frequent scheduling attempts
    const lastScheduleTime = localStorage.getItem('lastTokenRefreshSchedule');
    const lastRefreshTime = localStorage.getItem('lastTokenRefresh');
    const now = Date.now();

    // Don't schedule if we recently did a refresh or schedule
    const MIN_INTERVAL = 30000; // 30 seconds
    if (lastScheduleTime && now - parseInt(lastScheduleTime, 10) < MIN_INTERVAL) {
      return;
    }
    if (lastRefreshTime && now - parseInt(lastRefreshTime, 10) < MIN_INTERVAL) {
      return;
    }

    const tokenExp = localStorage.getItem('tokenExpiration');
    
    if (tokenExp) {
      const expirationTime = parseInt(tokenExp, 10);
      if (expirationTime > now) {
        const timeUntilExpiry = expirationTime - now;
        const REFRESH_MARGIN = 5 * 60 * 1000; // 5 minutes before expiry
        
        if (timeUntilExpiry > REFRESH_MARGIN) {
          const refreshTime = timeUntilExpiry - REFRESH_MARGIN;
          const timer = setTimeout(() => {
            refreshTokenRef.current().catch(err => {
              console.error('Error in scheduled token refresh:', err);
            });
          }, refreshTime);
          
          setTokenRefreshTimer(timer);
          localStorage.setItem('lastTokenRefreshSchedule', now.toString());
          console.log(`Token refresh scheduled in ${Math.round(refreshTime/60000)} minutes`);
          return;
        }
      }
    }

    // If we got here, we either have no expiration time or it's too close/passed
    // But don't refresh immediately if we just did a refresh recently
    const lastRefresh = localStorage.getItem('lastTokenRefresh');
    if (lastRefresh && now - parseInt(lastRefresh, 10) < 60000) { // Don't refresh if done in last minute
      console.log('Token refresh attempted too recently, skipping');
      return;
    }
    
    console.log('No valid token expiration time found or too close to expiry, refreshing token now');
    refreshTokenRef.current().catch(err => {
      console.error('Error in immediate token refresh:', err);
    });
  }, [tokenRefreshTimer]);

  // Update ref to point to the latest version of the function
  scheduleTokenRefreshRef.current = scheduleTokenRefresh;

  // Funkcja do pobierania danych użytkowników
  const fetchUsers = useCallback(async () => {
    // Check if we have recent user data in cache
    const lastUsersFetch = localStorage.getItem('lastUsersFetch');
    const now = Date.now();
    if (lastUsersFetch && now - parseInt(lastUsersFetch, 10) < 30000) { // 30s cache
      const cachedUsers = localStorage.getItem('cachedUsers');
      if (cachedUsers) {
        const parsedUsers = JSON.parse(cachedUsers);
        setUsers(parsedUsers);
        setError(null);
        return;
      }
    }

    try {
      const response = await fetch(API_ENDPOINTS.USERS, {
        credentials: 'include' // Include cookies with request
      });
      if (!response.ok) throw new Error('Failed to load users');
      const data = await response.json();
      const usersList = data.users || [];
      setUsers(usersList);
      setError(null);
      
      // Cache the results
      localStorage.setItem('cachedUsers', JSON.stringify(usersList));
      localStorage.setItem('lastUsersFetch', now.toString());
    } catch (err) {
      console.error('Error loading users:', err);
      setError('Failed to load user data. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, []);
    // Function to sync user state with backend and tokens
  const refreshUserState = useCallback(async () => {
    const MIN_UPDATE_INTERVAL = 30000; // 30 seconds
    const lastUpdate = localStorage.getItem('lastUserStateUpdate');
    const now = Date.now();

    // Check cache validity
    if (lastUpdate) {
      const timeSinceLastUpdate = now - parseInt(lastUpdate, 10);
      if (timeSinceLastUpdate < MIN_UPDATE_INTERVAL) {
        const cachedUser = localStorage.getItem(STORAGE_KEYS.USER);
        if (cachedUser) {
          try {
            const parsedUser = JSON.parse(cachedUser);
            if (parsedUser && parsedUser.id) { // Basic validation
              return true;
            }
          } catch (err) {
            console.warn('Invalid cached user data:', err);
          }
        }
      }
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout

      const response = await fetch(`${API_BASE_URL}/users/me`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        const userData = await response.json();
        
        // Handle token expiration if provided
        if (userData.token_exp) {
          const expirationTime = userData.token_exp * 1000;
          localStorage.setItem('tokenExpiration', expirationTime.toString());
          
          // Schedule refresh if needed
          if (!tokenRefreshTimer && expirationTime > now) {
            scheduleTokenRefresh();
          }
        }
        
        // Sanitize and normalize user data
        const sanitizedUser = {
          ...userData,
          avatar: userData.avatar_url || userData.avatar || 'https://i.pravatar.cc/150?img=3',
          fullName: userData.username || userData.fullName || 'User',
          level: userData.level || USER_LEVELS.BEGINNER,
          stats: {
            quizzes: userData.stats?.quizzes || 0,
            bestTime: userData.stats?.bestTime || '0min',
            correctAnswers: userData.stats?.correctAnswers || 0
          },
          lastUpdated: now
        };
        
        setUser(sanitizedUser);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(sanitizedUser));
        localStorage.setItem('lastUserStateUpdate', now.toString());
        
        return true;
      } else {
        if (response.status === 401) {
          // Token likely expired or invalid
          await logoutRef.current();
        } else {
          console.error('Error refreshing user state:', await response.text());
        }
        setUser(null);
        localStorage.removeItem(STORAGE_KEYS.USER);
        return false;
      }
    } catch (err) {
      console.error('Error refreshing user state:', err);
      
      // Use localStorage as fallback only for network/timeout errors
      if (err.name === 'AbortError' || err.message.includes('Failed to fetch')) {
        const storedUser = localStorage.getItem(STORAGE_KEYS.USER);
        if (storedUser) {
          try {
            const userData = JSON.parse(storedUser);
            if (userData && userData.id && now - userData.lastUpdated < 24 * 60 * 60 * 1000) { // 24h max cache
              setUser(userData);
              console.warn('Using cached user data as fallback - will verify ASAP');
              return true;
            }
          } catch (parseErr) {
            console.error('Error parsing cached user data:', parseErr);
          }
        }
      }
      
      setUser(null);
      localStorage.removeItem(STORAGE_KEYS.USER);
      return false;
    }
  }, [API_BASE_URL, scheduleTokenRefresh, tokenRefreshTimer]);
  // Helper function to update the auth state based on current tokens (now cookies)
  const updateAuthStateFromTokens = useCallback(async () => {
    const lastAuthUpdate = localStorage.getItem('lastAuthUpdate');
    const now = Date.now();
    if (lastAuthUpdate) {
      const timeSinceLastUpdate = now - parseInt(lastAuthUpdate, 10);
      if (timeSinceLastUpdate < 30000) { // 30 seconds cache
        return true;
      }
    }
    try {
      const response = await fetch(`${API_BASE_URL}/users/me`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Poprawka: zawsze include
      });
      if (response.ok) {
        const data = await response.json();
        const userData = {
          ...data,
          avatar: data.avatar_url || data.avatar || 'https://i.pravatar.cc/150?img=3',
          fullName: data.username || data.fullName || 'User',
          level: data.level || USER_LEVELS.BEGINNER,
          stats: data.stats || { quizzes: 0, bestTime: '0min', correctAnswers: 0 }
        };
        setUser(userData);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
        localStorage.setItem('lastAuthUpdate', now.toString());
        return true;
      } else {
        setUser(null);
        localStorage.removeItem(STORAGE_KEYS.USER);
      }
    } catch (err) {
      const cachedUser = localStorage.getItem(STORAGE_KEYS.USER);
      if (cachedUser) {
        try {
          setUser(JSON.parse(cachedUser));
          return true;
        } catch (parseErr) {
          console.error('Error parsing cached user data:', parseErr);
        }
      }
    }
    return false;
  }, [API_BASE_URL]);
  // Pierwsze ładowanie i okresowe sprawdzanie stanu uwierzytelniania
  useEffect(() => {
    let checkTimer = null;
    const CHECK_INTERVAL = 60000; // Check every minute

    async function initialAuthCheck() {
      setLoading(true);
      try {
        const isAuthenticated = await verifyAuthState();
        
        if (!isAuthenticated) {
          setUser(null); // Explicitly set user to null if not authenticated
          if (localStorage.getItem(STORAGE_KEYS.USER)) {
            console.log('Wykryto dane użytkownika w localStorage, ale token JWT jest nieważny. Usuwanie danych...');
            localStorage.removeItem(STORAGE_KEYS.USER);
          }
        }
      } catch (err) {
        console.error('Błąd podczas początkowego sprawdzania uwierzytelniania:', err);
        setUser(null); // Also ensure user is null on error
        localStorage.removeItem(STORAGE_KEYS.USER);
      } finally {
        setLoading(false);
      }
    }
    
    // Initial check
    initialAuthCheck();

    // Clear any previous timer if dependency changes
    if (checkTimer) {
      clearInterval(checkTimer);
      checkTimer = null;
    }

    // Only set up periodic checks if user is logged in
    if (user) {
      checkTimer = setInterval(() => {
        console.log("AuthContext: Performing periodic auth check...");
        verifyAuthStateRef.current().catch(err => {
          console.error('Error in periodic auth check:', err);
        });
      }, CHECK_INTERVAL);
    }
    
    return () => {
      if (checkTimer) {
        clearInterval(checkTimer);
      }
    };
  }, [user, verifyAuthState]); // Include verifyAuthState in dependencies
  
  // Zapisywanie użytkowników
  const saveUsers = useCallback(async (updatedUsers) => {
    try {
      const response = await fetch(API_ENDPOINTS.USERS, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies with request
        body: JSON.stringify({ users: updatedUsers }),
      });
      if (!response.ok) throw new Error('Failed to save users');
      return true;
    } catch (error) {
      console.error('Error saving users:', error);
      setError('Failed to save user data. Please try again later.');
      return false;
    }
  }, []);  // Rejestracja użytkownika - zaktualizowana funkcja, aby korzystała z nowego API
  const register = useCallback(async (fullName, email, password) => {
    try {
      if (!fullName?.trim() || !email?.trim() || !password?.trim()) {
        return { success: false, error: 'Wszystkie pola są wymagane' };
      }
      // Bezpośrednie wywołanie do API rejestracji
      const response = await fetch(`${API_BASE_URL}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies with request
        body: JSON.stringify({ 
          username: fullName, // Send fullName as username which backend expects
          email, 
          password 
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        return { 
          success: false, 
          error: data.error || 'Wystąpił błąd podczas rejestracji' 
        };
      }
      // Po udanej rejestracji pobierz profil użytkownika z backendu
      const profileResp = await fetch(`${API_BASE_URL}/users/me`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      if (profileResp.ok) {
        const userData = await profileResp.json();
        const sanitizedUser = {
          ...userData,
          avatar: userData.avatar_url || userData.avatar || 'https://i.pravatar.cc/150?img=3',
          fullName: userData.username || userData.fullName || 'User',
          level: userData.level || USER_LEVELS.BEGINNER,
          stats: userData.stats || { quizzes: 0, bestTime: '0min', correctAnswers: 0 },
        };
        setUser(sanitizedUser);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(sanitizedUser));
      }
      await fetchUsers();
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.message || 'Wystąpił błąd podczas rejestracji' 
      };
    }
  }, [fetchUsers]);
  // Zaktualizowana funkcja logowania
  const login = useCallback(async (email, password) => {
    try {
      if (!email?.trim() || !password?.trim()) {
        return { success: false, error: 'Email i hasło są wymagane' };
      }
      
      console.log('[LOGIN] Starting login process for:', email);
      console.log('[LOGIN] API_BASE_URL:', API_BASE_URL);
      
      // Bezpośrednie wywołanie do API logowania
      console.log('[LOGIN] Making fetch request to:', `${API_BASE_URL}/login`);
      
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies in request
        body: JSON.stringify({ email, password }),
      });
      
      console.log('[LOGIN] Response received:', response.status, response.statusText);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.log('[LOGIN] Error response text:', errorText);
        
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch (e) {
          errorData = { error: errorText || 'Nieprawidłowy email lub hasło' };
        }
        
        return { 
          success: false, 
          error: errorData.error || 'Nieprawidłowy email lub hasło' 
        };
      }
      
      const data = await response.json();
      console.log('[LOGIN] Success response data:', data);
      // Po zalogowaniu pobierz profil użytkownika z backendu
      const profileResp = await fetch(`${API_BASE_URL}/users/me`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      if (profileResp.ok) {
        const userData = await profileResp.json();
        const sanitizedUser = {
          ...userData,
          avatar: userData.avatar_url || userData.avatar || 'https://i.pravatar.cc/150?img=3',
          fullName: userData.username || userData.fullName || 'User',
          level: userData.level || USER_LEVELS.BEGINNER,
          stats: userData.stats || { quizzes: 0, bestTime: '0min', correctAnswers: 0 },
        };
        setUser(sanitizedUser);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(sanitizedUser));
        scheduleTokenRefresh();
      }
      return { success: true };
    } catch (error) {
      console.error('[LOGIN] Error occurred:', error);
      console.error('[LOGIN] Error name:', error.name);
      console.error('[LOGIN] Error message:', error.message);
      console.error('[LOGIN] Error stack:', error.stack);
      
      let errorMessage = 'Wystąpił błąd podczas logowania';
      
      if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
        errorMessage = 'Nie można połączyć się z serwerem. Sprawdź połączenie internetowe i spróbuj ponownie.';
        console.error('[LOGIN] Network error - server might be down or CORS issue');
      } else if (error.name === 'AbortError') {
        errorMessage = 'Żądanie zostało przerwane - spróbuj ponownie.';
      }
      
      return { 
        success: false, 
        error: errorMessage
      };
    }
  }, [API_BASE_URL, scheduleTokenRefresh]);

  // Funkcja do wylogowania ze wszystkich urządzeń
  const logoutFromAllDevices = useCallback(async () => {
    return logout(true);
  }, [logout]);

  // Aktualizacja awatara użytkownika
  const updateUserAvatar = useCallback(async (userId, avatarUrl) => {
    try {
      // Basic URL validation
      if (!avatarUrl || !avatarUrl.startsWith('http')) {
        return {
          success: false,
          error: 'Podaj prawidłowy URL awatara (musi zaczynać się od http:// lub https://)'
        };
      }
      
      const response = await fetch(`${API_BASE_URL}/users/${userId}/avatar`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies with request
        body: JSON.stringify({ avatar_url: avatarUrl }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        console.error("Failed to update avatar:", data.error);
        return { 
          success: false, 
          error: data.error || 'Nie udało się zaktualizować awatara' 
        };
      }
      
      // Jeśli aktualizowany jest aktualnie zalogowany użytkownik, zaktualizuj również stan
      if (user && user.id === userId) {
        const updatedUser = { 
          ...user, 
          avatar: avatarUrl,
          avatar_url: avatarUrl  // Update both fields to ensure consistency
        };
        setUser(updatedUser);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(updatedUser));
      }
      
      // Zaktualizuj również listę użytkowników
      setUsers(prevUsers => prevUsers.map(u => 
        u.id === userId ? { 
          ...u, 
          avatar: avatarUrl, 
          avatar_url: avatarUrl  // Update both fields
        } : u
      ));
      
      return { success: true };
    } catch (error) {
      console.error("Error updating avatar:", error);
      return { 
        success: false, 
        error: error.message || 'Wystąpił błąd podczas aktualizacji awatara' 
      };
    }
  }, [user, API_BASE_URL, setUsers]);

  const updateUserData = useCallback(async (userId, userData) => {
    try {
      // Jeśli aktualizacja dotyczy tylko awatara, użyj dedykowanej funkcji
      if (userData.avatar && Object.keys(userData).length === 1) {
        return updateUserAvatar(userId, userData.avatar);
      }
      
      // Use the user-specific update endpoint instead of updating all users at once
      const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies with request
        body: JSON.stringify({
          // Map fullName to username which backend expects
          username: userData.fullName,
          email: userData.email
        }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        console.error("Failed to update user data:", data.error);
        return { success: false, error: data.error || 'Nie udało się zaktualizować danych użytkownika' };
      }
      
      // Update the user in the local state
      if (user && user.id === userId) {
        const updatedUser = { 
          ...user,
          username: userData.fullName || user.username,
          fullName: userData.fullName || user.fullName,
          email: userData.email || user.email
        };
        
        setUser(updatedUser);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(updatedUser));
      }
      
      return { success: true };
    } catch (error) {
      console.error("Error updating user data:", error);
      return { success: false, error: error.message || 'Wystąpił błąd podczas aktualizacji danych' };
    }
  }, [user, API_BASE_URL, updateUserAvatar]);

  // Komponent ładowania
  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Ładowanie danych...</p>
      </div>
    );
  }
  const contextValue = {
    user,
    users,
    loading,
    error,
    login,
    logout,
    register,
    updateUserData,
    updateUserAvatar,
    fetchUsers,
    saveUsers,
    refreshUserState,
    updateAuthStateFromTokens,
    verifyAuthState,
    refreshToken,
    logoutFromAllDevices
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};