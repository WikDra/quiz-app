import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState([]);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    
    // Pobierz dane użytkowników z pliku JSON
    fetch('http://localhost:3001/users.json')
      .then(response => response.json())
      .then(data => {
        setUsers(data.users);
        setLoading(false);
      })
      .catch(error => {
        console.error('Error loading users:', error);
        setLoading(false);
      });
  }, []);

  const saveUsers = async (updatedUsers) => {
    try {
      const response = await fetch('http://localhost:3001/users.json', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ users: updatedUsers }),
      });
      if (!response.ok) throw new Error('Failed to save users');
    } catch (error) {
      console.error('Error saving users:', error);
      throw error;
    }
  };

  const login = async (email, password) => {
    try {
      const foundUser = users.find(u => u.email === email && u.password === password);
      
      if (!foundUser) {
        return { success: false, error: 'Nieprawidłowy email lub hasło' };
      }

      const userWithoutPassword = { ...foundUser };
      delete userWithoutPassword.password;
      
      setUser(userWithoutPassword);
      localStorage.setItem('user', JSON.stringify(userWithoutPassword));
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const register = async (name, email, password) => {
    try {
      if (users.some(u => u.email === email)) {
        return { success: false, error: 'Użytkownik o tym adresie email już istnieje' };
      }

      const newUser = {
        id: String(users.length + 1),
        name,
        email,
        password,
        level: 'Początkujący',
        stats: {
          quizzes: 0,
          bestTime: '0min',
          correctAnswers: 0
        },
        avatar: `https://i.pravatar.cc/200?img=${users.length + 1}`
      };
      
      const updatedUsers = [...users, newUser];
      await saveUsers(updatedUsers);
      setUsers(updatedUsers);

      const userWithoutPassword = { ...newUser };
      delete userWithoutPassword.password;
      
      setUser(userWithoutPassword);
      localStorage.setItem('user', JSON.stringify(userWithoutPassword));
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, register }}>
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