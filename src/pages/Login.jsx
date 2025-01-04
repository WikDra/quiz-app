import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../styles/Auth.css';

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      setLoading(true);
      const result = await login(formData.email, formData.password);
      if (result.success) {
        navigate('/home');
      } else {
        setError(result.error || 'Nieprawidłowy email lub hasło');
      }
    } catch (err) {
      setError('Wystąpił błąd podczas logowania');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h2>Zaloguj się</h2>
          <div className="logo">🌐 CyberQuiz</div>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder="Wprowadź email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Hasło</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              placeholder="Wprowadź hasło"
            />
          </div>

          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? 'Logowanie...' : 'Zaloguj się'}
          </button>
        </form>

        <div className="auth-footer">
          <p>Nie masz jeszcze konta? <Link to="/register">Zarejestruj się</Link></p>
        </div>
      </div>
    </div>
  );
};

export default Login;