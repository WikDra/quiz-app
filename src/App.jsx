import React, { lazy, Suspense, memo, useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { QuizProvider } from './context/QuizContext';
import { LoadingSpinner, ErrorMessage } from './components/SharedComponents';
import './styles/SharedComponents.css';

import AuthVerifier from './components/AuthVerifier';
// Conditionally import TokenDiagnostics in development mode
const TokenDiagnostics = import.meta.env.DEV 
  ? lazy(() => import('./components/TokenDiagnostics'))
  : () => null;
// Lazy loading komponentów stron
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const HomePage = lazy(() => import('./pages/HomePage'));
const LandingPage = lazy(() => import('./pages/LandingPage'));
const CreateQuiz = lazy(() => import('./pages/CreateQuiz'));
const SolveQuiz = lazy(() => import('./pages/SolveQuiz'));
const UserSettings = lazy(() => import('./pages/UserSettings'));
const OAuthCallback = lazy(() => import('./pages/OAuthCallback'));
const PremiumPage = lazy(() => import('./pages/PremiumPage'));
const PaymentSuccessPage = lazy(() => import('./pages/PaymentSuccessPage')); 
const TestPremium = lazy(() => import('./pages/TestPremium')); // Dodaj stronę testową

// Komponent ładowania dla Suspense
const LoadingFallback = memo(() => (
  <LoadingSpinner message="Ładowanie strony..." />
));

// Komponent do obsługi błędów
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Error caught by ErrorBoundary:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <ErrorMessage 
          message={this.state.error?.message || "Wystąpił nieoczekiwany błąd"}
          onRetry={() => window.location.reload()}
        />
      );
    }

    return this.props.children;
  }
}

// Zoptymalizowane komponenty routingu z wykorzystaniem memo
const PrivateRoute = memo(({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <LoadingFallback />;
  }
  
  return user ? children : <Navigate to="/login" />;
});

const PublicRoute = memo(({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <LoadingFallback />;
  }
  
  return !user ? children : <Navigate to="/home" />;
});

// Komponent wykrywający stan online/offline z memoizacją komunikatu
const OfflineNotification = memo(() => (
  <div className="offline-notification">
    <p>Utracono połączenie z internetem. Niektóre funkcje mogą być niedostępne.</p>
  </div>
));

const OnlineStatusHandler = memo(() => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return !isOnline ? <OfflineNotification /> : null;
});

// Główny komponent routingu
const AppRoutes = memo(() => {
  const { user } = useAuth();

  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route path="/login" element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          } />
          <Route path="/register" element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          } />
          <Route path="/home" element={
            <PrivateRoute>
              <HomePage />
            </PrivateRoute>
          } />
          <Route path="/create-quiz" element={
            <PrivateRoute>
              <CreateQuiz />
            </PrivateRoute>
          } />          <Route path="/solve-quiz/:id" element={
            <PrivateRoute>
              <SolveQuiz />
            </PrivateRoute>
          } />
          <Route path="/user-settings" element={
            <PrivateRoute>
              <UserSettings />
            </PrivateRoute>
          } />
          <Route path="/oauth-callback" element={<OAuthCallback />} />
          <Route path="/premium" element={
            <PrivateRoute>
              <PremiumPage />
            </PrivateRoute>
          } />
          <Route path="/payment-success" element={
            <PrivateRoute>
              <PaymentSuccessPage />
            </PrivateRoute>
          } /> 
          <Route path="/test-premium" element={
            <PrivateRoute>
              <TestPremium />
            </PrivateRoute>
          } /> {/* Dodaj nową ścieżkę */}

          <Route path="/" element={user ? <Navigate to="/home" /> : <LandingPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </ErrorBoundary>
  );
});

// Główny komponent aplikacji
const App = memo(() => {  return (
    <AuthProvider>
      <QuizProvider>
        <Router> {/* Router is here */}
          <OnlineStatusHandler />
          <AuthVerifier />
          <AppRoutes />
          {import.meta.env.DEV && <TokenDiagnostics />}
        </Router>
      </QuizProvider>
    </AuthProvider>
  );
});

export default App;
