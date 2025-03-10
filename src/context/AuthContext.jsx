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

  // Logowanie użytkownika
  const login = useCallback(async (email, password) => {
    try {
      if (!email?.trim() || !password?.trim()) {
        return { success: false, error: 'Email i hasło są wymagane' };
      }
      
      const foundUser = users.find(u => u.email === email && u.password === password);
      
      if (!foundUser) {
        return { success: false, error: 'Nieprawidłowy email lub hasło' };
      }

      // Nie przechowuj hasła w stanie aplikacji ani localStorage
      const userWithoutPassword = { ...foundUser };
      delete userWithoutPassword.password;
      
      setUser(userWithoutPassword);
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userWithoutPassword));
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message || 'Wystąpił błąd podczas logowania' };
    }
  }, [users]);

  // Rejestracja użytkownika
  const register = useCallback(async (name, email, password) => {
    try {
      if (!name?.trim() || !email?.trim() || !password?.trim()) {
        return { success: false, error: 'Wszystkie pola są wymagane' };
      }
      
      if (users.some(u => u.email === email)) {
        return { success: false, error: 'Użytkownik o tym adresie email już istnieje' };
      }

      // Poprawne ID - zapewnienie unikalności
      const newId = users.length > 0 
        ? Math.max(...users.map(u => parseInt(u.id))) + 1 
        : 1;
      
      const newUser = {
        id: String(newId),
        name,
        email,
        password,
        level: USER_LEVELS[0], // Początkujący z constants
        stats: {
          quizzes: 0,
          bestTime: '0min',
          correctAnswers: 0
        },
        avatar: `https://i.pravatar.cc/200?img=${Math.floor(Math.random() * 70)}`
      };
      
      const updatedUsers = [...users, newUser];
      const saved = await saveUsers(updatedUsers);
      
      if (!saved) {
        return { success: false, error: 'Nie udało się zapisać nowego użytkownika' };
      }
      
      setUsers(updatedUsers);

      const userWithoutPassword = { ...newUser };
      delete userWithoutPassword.password;
      
      setUser(userWithoutPassword);
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userWithoutPassword));
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message || 'Wystąpił błąd podczas rejestracji' };
    }
  }, [users, saveUsers]);

  // Wylogowanie użytkownika
  const logout = useCallback(() => {
    setUser(null);
    localStorage.removeItem(STORAGE_KEYS.USER);
  }, []);

  // Aktualizacja danych użytkownika
  const updateUserData = useCallback(async (userId, userData) => {
    try {
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
  }, [users, user, saveUsers]);

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