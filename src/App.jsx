import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { QuizProvider } from './context/QuizContext';
import Login from './pages/Login';
import Register from './pages/Register';
import HomePage from './pages/HomePage';
import LandingPage from './pages/LandingPage';
import CreateQuiz from './pages/CreateQuiz';
import SolveQuiz from './pages/SolveQuiz';

const PrivateRoute = ({ children }) => {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" />;
};

const PublicRoute = ({ children }) => {
  const { user } = useAuth();
  return !user ? children : <Navigate to="/home" />;
};

function AppRoutes() {
  const { user } = useAuth();

  return (
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
      } />
      <Route path="/solve-quiz/:id" element={
        <PrivateRoute>
          <SolveQuiz />
        </PrivateRoute>
      } />
      <Route path="/" element={user ? <Navigate to="/home" /> : <LandingPage />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <QuizProvider>
        <Router>
          <AppRoutes />
        </Router>
      </QuizProvider>
    </AuthProvider>
  );
}

export default App;
