import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { API_BASE_URL, API_ENDPOINTS, STORAGE_KEYS, USER_LEVELS } from '../utils/constants';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState([]);
  const [error, setError] = useState(null);
  
  // Cookie helper to patch document.cookie API for cross-site compatibility
  const patchCookieApi = useCallback(() => {
    if (typeof document === 'undefined') return; // Skip if not in browser environment
    
    console.log("Patching document.cookie API for cross-site compatibility");
    
    try {
      // Save the original setters and getters
      const originalCookieGetter = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie').get;
      const originalCookieSetter = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie').set;
      
      // Replace the setter
      Object.defineProperty(document, 'cookie', {
        get: function() {
          return originalCookieGetter.call(document);
        },
        set: function(val) {
          console.log("Setting cookie with cross-site compatibility:", val);
          
          // Fix SameSite attribute if needed
          if (val.indexOf('SameSite=') === -1 && val.indexOf('samesite=') === -1) {
            val += '; SameSite=None';
          }
          
          // Call the original setter
          return originalCookieSetter.call(document, val);
        },
        configurable: true
      });
    } catch (err) {
      console.error("Error patching cookie API:", err);
    }
  }, []);

  // Apply cookie patch on initialization
  useEffect(() => {
    patchCookieApi();
  }, [patchCookieApi]);

  // Funkcja do pobierania danych użytkowników
  const fetchUsers = useCallback(async () => {
    try {
      const response = await fetch(API_ENDPOINTS.USERS, {
        credentials: 'include' // Include cookies with request
      });
      if (!response.ok) throw new Error('Failed to load users');
      const data = await response.json();
      setUsers(data.users || []);
      setError(null);
    } catch (err) {
      console.error('Error loading users:', err);
      setError('Failed to load user data. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, []);
  // Funkcja do synchronizacji użytkownika z tokenami
  const refreshUserState = useCallback(() => {
    const storedUser = localStorage.getItem(STORAGE_KEYS.USER);
    if (storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        
        // Upewnij się, że dane użytkownika zawierają wszystkie wymagane pola
        const sanitizedUser = {
          ...userData,
          stats: userData.stats || { 
            quizzes: 0,  // Use a number for count, not an array
            bestTime: '0min', 
            correctAnswers: 0 
          }
        };
        
        setUser(sanitizedUser);
        
        // Zapisz zaktualizowane dane do localStorage jeśli były zmodyfikowane
        if (JSON.stringify(userData) !== JSON.stringify(sanitizedUser)) {
          localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(sanitizedUser));
          console.log('User data structure was fixed during refresh');
        }
        
        return true;
      } catch (err) {
        console.error('Error parsing user data during refresh:', err);
        localStorage.removeItem(STORAGE_KEYS.USER);
      }
    }
    return false;
  }, [setUser]);
    // Helper function to update the auth state based on current tokens (now cookies)
  const updateAuthStateFromTokens = useCallback(async () => {
    try {
      // Make an API call to get fresh user data - now uses cookies
      const response = await fetch(`${API_BASE_URL}/api/users/me/profile`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include' // Include cookies with request
      });
      if (response.ok) {
        const data = await response.json();
        
        // Ensure user data has all required fields with proper structure
        const userData = {
          ...data,
          // Make sure both avatar and fullName are set correctly
          avatar: data.avatar_url || data.avatar || 'https://i.pravatar.cc/150?img=3',
          fullName: data.username || data.fullName || 'User',
          level: data.level || 'Początkujący',
          // Ensure stats structure is consistent
          stats: data.stats || {
            quizzes: 0,
            bestTime: '0min',
            correctAnswers: 0
          }
        };

        console.log('User data updated from API:', userData);
        setUser(userData);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
        return true;
      } else {
        console.error('Failed to fetch user profile:', await response.text());
      }
    } catch (err) {
      console.error('Failed to update auth state from token:', err);
    }
    return false;
  }, [API_BASE_URL]);

  useEffect(() => {
    // Pobierz zalogowanego użytkownika z localStorage
    const storedUser = localStorage.getItem(STORAGE_KEYS.USER);
    if (storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        
        // Upewnij się, że dane użytkownika zawierają wszystkie wymagane pola
        const sanitizedUser = {
          ...userData,
          // Ensure basic user fields exist
          fullName: userData.fullName || userData.username || 'User',
          avatar: userData.avatar || userData.avatar_url || 'https://i.pravatar.cc/150?img=3',
          level: userData.level || 'Początkujący',
          // Ensure stats is properly structured
          stats: userData.stats || { 
            quizzes: 0, 
            bestTime: '0min', 
            correctAnswers: 0 
          }
        };
        
        console.log('Initial user load with sanitized data:', sanitizedUser);
        setUser(sanitizedUser);
        
        // Zapisz zaktualizowane dane do localStorage jeśli były zmodyfikowane
        if (JSON.stringify(userData) !== JSON.stringify(sanitizedUser)) {
          localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(sanitizedUser));
          console.log('User data structure was fixed during initial load');
        }
        
        setLoading(false);
      } catch (err) {
        console.warn('Failed to parse user data during initial load:', err);
        console.error('Invalid user data in storage:', err);
        localStorage.removeItem(STORAGE_KEYS.USER);
      }
    }
    
    // Pobierz dane użytkowników z API
    fetchUsers();
  }, [fetchUsers]);
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
      const response = await fetch(`${API_BASE_URL}/api/register`, {
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
      
      // Po udanej rejestracji odświeżamy listę użytkowników
      await fetchUsers();
      
      // Ustawiamy zalogowanego użytkownika
      setUser(data);
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(data));
      
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
      
      console.log("AuthContext: Wysyłanie żądania logowania do API...");
      
      // Bezpośrednie wywołanie do API logowania
      const response = await fetch(`${API_BASE_URL}/api/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies in request
        body: JSON.stringify({ email, password }),
      });
      
      console.log("AuthContext: Otrzymano odpowiedź z API:", response.status, response.statusText);
      
      const data = await response.json();
      console.log("AuthContext: Dane odpowiedzi:", { 
        success: response.ok, 
        hasUserData: !!data.user_data,
        error: data.error || null
      });
      
      if (!response.ok) {
        return { 
          success: false, 
          error: data.error || 'Nieprawidłowy email lub hasło' 
        };
      }
      
      // Ustawiamy zalogowanego użytkownika
      if (data.user_data) {
        console.log("AuthContext: Ustawianie danych użytkownika");
        setUser(data.user_data);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(data.user_data));
      } else {
        console.warn("AuthContext: Brak danych użytkownika w odpowiedzi API");
      }
      
      return { success: true };
    } catch (error) {
      console.error("AuthContext: Błąd podczas logowania:", error);
      return { 
        success: false, 
        error: error.message || 'Wystąpił błąd podczas logowania' 
      };
    }
  }, []);
  // Wylogowanie użytkownika
  const logout = useCallback(async () => {
    try {
      // Call the API to clear cookies
      await fetch(`${API_BASE_URL}/api/logout`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });
    } catch (error) {
      console.error("Error during logout:", error);
    }
    // Clear local state regardless of API success
    setUser(null);
    localStorage.removeItem(STORAGE_KEYS.USER);
  }, [API_BASE_URL]);

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
      
      const response = await fetch(`${API_BASE_URL}/api/users/${userId}/avatar`, {
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
      const response = await fetch(`${API_BASE_URL}/api/users/${userId}`, {
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