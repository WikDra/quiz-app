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
      console.log("Próba logowania z danymi:", { email: formData.email });
      const result = await login(formData.email, formData.password);
      console.log("Otrzymany rezultat logowania:", result);
      
      if (result.success) {
        console.log("Logowanie udane, przekierowanie do /home");
        navigate('/home');
      } else {
        console.error("Błąd logowania:", result.error);
        setError(result.error || 'Nieprawidłowy email lub hasło');
      }
    } catch (err) {
      console.error("Wyjątek podczas logowania:", err);
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
        </form>        <div className="social-login">
          <p>Lub zaloguj się za pomocą:</p>
          <button 
            type="button" 
            onClick={() => {
              // Redirect to Google login endpoint
              window.location.href = "http://localhost:5000/api/login/google";
              // No polling needed since the server redirects back to our callback URL
            }} 
            className="google-login-button"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 18 18">
              <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z"/>
              <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z"/>
              <path fill="#FBBC05" d="M3.964 10.71c-.18-.54-.282-1.117-.282-1.71s.102-1.17.282-1.71V4.958H.957C.347 6.173 0 7.548 0 9s.348 2.827.957 4.042l3.007-2.332z"/>
              <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"/>
            </svg>
            <span>Google</span>
          </button>
        </div>

        <div className="auth-footer">
          <p>Nie masz jeszcze konta? <Link to="/register">Zarejestruj się</Link></p>
        </div>
      </div>
    </div>
  );
};

export default Login;