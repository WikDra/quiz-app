import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../styles/Auth.css';

const Register = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { register } = useAuth();

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

    if (formData.password !== formData.confirmPassword) {
      return setError('Hasła nie są identyczne');
    }

    try {
      setLoading(true);
      const result = await register(formData.name, formData.email, formData.password);
      if (result.success) {
        navigate('/home');
      } else {
        setError(result.error || 'Wystąpił błąd podczas rejestracji');
      }
    } catch (err) {
      setError('Wystąpił błąd podczas rejestracji');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h2>Zarejestruj się</h2>
          <div className="logo">🌐 CyberQuiz</div>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="name">Imię i nazwisko</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              placeholder="Wprowadź imię i nazwisko"
            />
          </div>

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

          <div className="form-group">
            <label htmlFor="confirmPassword">Potwierdź hasło</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              placeholder="Potwierdź hasło"
            />
          </div>

          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? 'Rejestracja...' : 'Zarejestruj się'}
          </button>
        </form>

        <div className="auth-footer">
          <p>Masz już konto? <Link to="/login">Zaloguj się</Link></p>
        </div>
      </div>
    </div>
  );
};

export default Register;