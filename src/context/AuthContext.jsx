import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { API_BASE_URL, API_ENDPOINTS, STORAGE_KEYS, USER_LEVELS } from '../utils/constants';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState([]);
  const [error, setError] = useState(null);

  // Funkcja do pobierania danych użytkowników
  const fetchUsers = useCallback(async () => {
    try {
      const response = await fetch(API_ENDPOINTS.USERS);
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

  useEffect(() => {
    // Pobierz zalogowanego użytkownika z localStorage
    const storedUser = localStorage.getItem(STORAGE_KEYS.USER);
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (err) {
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
        body: JSON.stringify({ users: updatedUsers }),
      });
      if (!response.ok) throw new Error('Failed to save users');
      return true;
    } catch (error) {
      console.error('Error saving users:', error);
      setError('Failed to save user data. Please try again later.');
      return false;
    }
  }, []);

  // Rejestracja użytkownika - zaktualizowana funkcja, aby korzystała z nowego API
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
        body: JSON.stringify({ fullName, email, password }),
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
      
      // Bezpośrednie wywołanie do API logowania
      const response = await fetch(`${API_BASE_URL}/api/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        return { 
          success: false, 
          error: data.error || 'Nieprawidłowy email lub hasło' 
        };
      }
      
      // Ustawiamy zalogowanego użytkownika
      setUser(data);
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(data));
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.message || 'Wystąpił błąd podczas logowania' 
      };
    }
  }, []);

  // Wylogowanie użytkownika
  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem(STORAGE_KEYS.USER);
  }, []);

  // Aktualizacja danych użytkownika  // Aktualizacja awatara użytkownika
  const updateUserAvatar = useCallback(async (userId, avatarUrl) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/users/${userId}/avatar`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ avatar_url: avatarUrl }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        return { 
          success: false, 
          error: data.error || 'Nie udało się zaktualizować awatara' 
        };
      }
      
      // Jeśli aktualizowany jest aktualnie zalogowany użytkownik, zaktualizuj również stan
      if (user && user.id === userId) {
        const updatedUser = { ...user, avatar: avatarUrl };
        setUser(updatedUser);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(updatedUser));
      }
      
      // Zaktualizuj również listę użytkowników
      setUsers(prevUsers => prevUsers.map(u => 
        u.id === userId ? { ...u, avatar: avatarUrl } : u
      ));
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.message || 'Wystąpił błąd podczas aktualizacji awatara' 
      };
    }
  }, [user, API_BASE_URL]);

  const updateUserData = useCallback(async (userId, userData) => {
    try {
      // Jeśli aktualizacja dotyczy tylko awatara, użyj dedykowanej funkcji
      if (userData.avatar && Object.keys(userData).length === 1) {
        return updateUserAvatar(userId, userData.avatar);
      }
      
      const userIndex = users.findIndex(u => u.id === userId);
      
      if (userIndex === -1) {
        return { success: false, error: 'Użytkownik nie został znaleziony' };
      }
      
      // Aktualizacja danych użytkownika z zabezpieczeniem przed nieprawidłowymi danymi
      const updatedUsers = [...users];
      updatedUsers[userIndex] = {
        ...updatedUsers[userIndex],
        ...userData,
        // Zabezpieczenie przed nadpisaniem istotnych danych
        id: updatedUsers[userIndex].id,
        email: userData.email || updatedUsers[userIndex].email,
        password: userData.password || updatedUsers[userIndex].password
      };
      
      const saved = await saveUsers(updatedUsers);
      
      if (!saved) {
        return { success: false, error: 'Nie udało się zaktualizować danych użytkownika' };
      }
      
      setUsers(updatedUsers);
      
      // Jeśli aktualizowany jest aktualnie zalogowany użytkownik, zaktualizuj również stan
      if (user && user.id === userId) {
        const updatedUser = { ...updatedUsers[userIndex] };
        delete updatedUser.password;
        setUser(updatedUser);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(updatedUser));
      }
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message || 'Wystąpił błąd podczas aktualizacji danych' };
    }
  }, [users, user, saveUsers, updateUserAvatar]);

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
    login,
    logout,
    register,
    updateUserAvatar,
    updateUserData,
    error,
    refreshUsers: fetchUsers
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