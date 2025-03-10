import React, { useState, useCallback, memo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../styles/Auth.css';

// Komponent nagłówka formularza
const AuthHeader = memo(({ title }) => (
  <div className="auth-header">
    <h2>{title}</h2>
    <div className="logo">CyberQuiz</div>
  </div>
));

// Komponent komunikatu o błędzie
const ErrorMessage = memo(({ message }) => 
  message ? <div className="error-message">{message}</div> : null
);

// Komponent pola formularza
const FormField = memo(({ 
  id, 
  type = 'text', 
  label, 
  value, 
  onChange, 
  placeholder 
}) => (
  <div className="form-group">
    <label htmlFor={id}>{label}</label>
    <input
      type={type}
      id={id}
      name={id}
      value={value}
      onChange={onChange}
      required
      placeholder={placeholder}
    />
  </div>
));

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleChange = useCallback((e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  }, []);

  const handleSubmit = useCallback(async (e) => {
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
  }, [formData.email, formData.password, login, navigate]);

  return (
    <div className="auth-container">
      <div className="auth-card">
        <AuthHeader title="Zaloguj się" />
        <ErrorMessage message={error} />

        <form onSubmit={handleSubmit} className="auth-form">
          <FormField
            id="email"
            type="email"
            label="Email"
            value={formData.email}
            onChange={handleChange}
            placeholder="Wprowadź email"
          />

          <FormField
            id="password"
            type="password"
            label="Hasło"
            value={formData.password}
            onChange={handleChange}
            placeholder="Wprowadź hasło"
          />

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