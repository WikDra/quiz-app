import React, { useState, useCallback, memo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../styles/Auth.css';

// Reużywalne komponenty z Login.jsx
const AuthHeader = memo(({ title }) => (
  <div className="auth-header">
    <h2>{title}</h2>
    <div className="logo">CyberQuiz</div>
  </div>
));

const ErrorMessage = memo(({ message }) => 
  message ? <div className="error-message">{message}</div> : null
);

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

const Register = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { register } = useAuth();

  const handleChange = useCallback((e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  }, []);

  const validateForm = useCallback(() => {
    if (formData.password !== formData.confirmPassword) {
      setError('Hasła nie są identyczne');
      return false;
    }
    if (formData.password.length < 6) {
      setError('Hasło musi mieć co najmniej 6 znaków');
      return false;
    }
    return true;
  }, [formData.password, formData.confirmPassword]);
  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    setError('');

    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);
      
      // New format for backend v2
      const userData = {
        username: formData.username,
        email: formData.email,
        password: formData.password,
        first_name: formData.first_name,
        last_name: formData.last_name
      };
      
      const result = await register(userData);
      
      if (result.success) {
        navigate('/home');
      } else {
        setError(result.message || 'Wystąpił błąd podczas rejestracji');
      }
    } catch (err) {
      setError('Wystąpił błąd podczas rejestracji');
    } finally {
      setLoading(false);
    }
  }, [formData, register, navigate, validateForm]);

  return (
    <div className="auth-container">
      <div className="auth-card">
        <AuthHeader title="Zarejestruj się" />
        <ErrorMessage message={error} />        <form onSubmit={handleSubmit} className="auth-form">
          <FormField
            id="username"
            label="Nazwa użytkownika"
            value={formData.username}
            onChange={handleChange}
            placeholder="Wprowadź nazwę użytkownika"
          />

          <FormField
            id="email"
            type="email"
            label="Email"
            value={formData.email}
            onChange={handleChange}
            placeholder="Wprowadź email"
          />

          <FormField
            id="first_name"
            label="Imię"
            value={formData.first_name}
            onChange={handleChange}
            placeholder="Wprowadź imię"
          />

          <FormField
            id="last_name"
            label="Nazwisko"
            value={formData.last_name}
            onChange={handleChange}
            placeholder="Wprowadź nazwisko"
          />

          <FormField
            id="password"
            type="password"
            label="Hasło"
            value={formData.password}
            onChange={handleChange}
            placeholder="Wprowadź hasło"
          />

          <FormField
            id="confirmPassword"
            type="password"
            label="Potwierdź hasło"
            value={formData.confirmPassword}
            onChange={handleChange}
            placeholder="Potwierdź hasło"
          />

          <button 
            type="submit" 
            className="auth-button" 
            disabled={loading}
          >
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