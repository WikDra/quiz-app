import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi } from '../utils/apiUtils';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Check authentication status on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = useCallback(async () => {
    try {
      setLoading(true);
      const response = await authApi.checkAuth();
      
      if (response.success && response.authenticated) {
        setUser(response.user);
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (credentials) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await authApi.login(credentials);
      
      if (response.success) {
        setUser(response.user);
        return { success: true, message: response.message };
      } else {
        setError(response.message);
        return { success: false, message: response.message };
      }
    } catch (error) {
      const errorMessage = error.message || 'Błąd podczas logowania';
      setError(errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (userData) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await authApi.register(userData);
      
      if (response.success) {
        setUser(response.user);
        return { success: true, message: response.message };
      } else {
        setError(response.message);
        return { success: false, message: response.message, errors: response.errors };
      }
    } catch (error) {
      const errorMessage = error.message || 'Błąd podczas rejestracji';
      setError(errorMessage);
      return { success: false, message: errorMessage };
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Error during logout:', error);
    } finally {
      setUser(null);
      setError(null);
    }
  }, []);

  const updateUser = useCallback((updatedUser) => {
    setUser(updatedUser);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const verifyAuthState = useCallback(async () => {
    try {
      const response = await authApi.checkAuth();
      return response.success && response.authenticated;
    } catch (error) {
      console.error('Error verifying auth state:', error);
      return false;
    }
  }, []);
  // For cookie-based auth
  const refreshToken = useCallback(async () => {
    try {
      const response = await authApi.refreshToken();      
      if (response.success) {
        setUser(response.user);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error refreshing session:', error);
      return false;
    }
  }, [setUser]);

  // Check if user has premium access
  const isPremium = user?.is_premium || false;
  const isAdmin = user?.is_admin || false;

  const value = {
    user,
    loading,
    error,
    isPremium,
    isAdmin,
    login,
    register,
    logout,
    updateUser,
    clearError,
    checkAuthStatus,
    verifyAuthState,
    refreshToken
  };

  return (
    <AuthContext.Provider value={value}>
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
