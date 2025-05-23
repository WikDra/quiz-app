/**
 * Globalne stałe aplikacji Quiz-App
 */

// API URLs
export const API_BASE_URL = 'http://localhost:5000';
export const API_ENDPOINTS = {
  // Authentication endpoints
  AUTH_CSRF: `${API_BASE_URL}/api/auth/csrf-token`,
  AUTH_LOGIN: `${API_BASE_URL}/api/auth/login`,
  AUTH_REGISTER: `${API_BASE_URL}/api/auth/register`,
  AUTH_LOGOUT: `${API_BASE_URL}/api/auth/logout`,
  AUTH_CHECK: `${API_BASE_URL}/api/auth/check`,
  AUTH_ME: `${API_BASE_URL}/api/auth/me`,
  AUTH_REFRESH: `${API_BASE_URL}/api/auth/refresh`,
  AUTH_PING: `${API_BASE_URL}/api/auth/ping`,
  AUTH_DEBUG: `${API_BASE_URL}/api/auth/debug`,
  AUTH_SET_SESSION: `${API_BASE_URL}/api/auth/set-session`,
  
  // Quiz endpoints
  QUIZ: `${API_BASE_URL}/api/quiz`,
  QUIZ_BY_ID: (id) => `${API_BASE_URL}/api/quiz/${id}`,
  QUIZ_MY: `${API_BASE_URL}/api/quiz/my`,
  QUIZ_ATTEMPT: (id) => `${API_BASE_URL}/api/quiz/${id}/attempt`,
  
  // User endpoints
  USER_PROFILE: `${API_BASE_URL}/api/user/profile`,
  USER_STATS: `${API_BASE_URL}/api/user/stats`,
  USER_PASSWORD: `${API_BASE_URL}/api/user/password`,
  
  // Payment endpoints
  STRIPE_CREATE_PAYMENT: `${API_BASE_URL}/api/stripe/create-payment-intent`,
  STRIPE_SUBSCRIPTION: `${API_BASE_URL}/api/stripe/subscription-status`
};

// Kategorie quizów
export const QUIZ_CATEGORIES = [
  { id: '', name: 'Wszystkie' },
  { id: 'cybersecurity', name: 'Cyberbezpieczeństwo' },
  { id: 'programming', name: 'Programowanie' },
  { id: 'networking', name: 'Sieci komputerowe' },
  { id: 'other', name: 'Inne' }
];

// Poziomy trudności quizów
export const DIFFICULTY_LEVELS = [
  { id: 'easy', name: 'Łatwy' },
  { id: 'medium', name: 'Średni' },
  { id: 'hard', name: 'Trudny' }
];

// Domyślne wartości dla quizów
export const DEFAULT_QUIZ_VALUES = {
  timeLimit: 30,
  difficulty: 'medium',
  category: 'other'
};

// Mapowanie poziomu trudności na nazwy
export const DIFFICULTY_MAP = {
  easy: 'Łatwy',
  medium: 'Średni',
  hard: 'Trudny'
};

// Poziomy doświadczenia użytkowników
export const USER_LEVELS = [
  'Początkujący',
  'Średniozaawansowany',
  'Zaawansowany',
  'Ekspert'
];

// Klucze dla localStorage (zredukowane dla cookie-based auth)
export const STORAGE_KEYS = {
  THEME: 'quiz_app_theme',
  QUIZ_HISTORY: 'quiz_app_history',
  CSRF_TOKEN: 'quiz_app_csrf_token'
};

// Limity i ograniczenia
export const LIMITS = {
  MIN_QUESTIONS: 1,
  MAX_QUESTIONS: 50,
  MIN_TIME_PER_QUESTION: 10,
  MAX_TIME_PER_QUESTION: 300,
  MAX_SEARCH_RESULTS: 100
};

// Komunikaty błędów
export const ERROR_MESSAGES = {
  QUIZ_NOT_FOUND: 'Nie znaleziono quizu',
  NETWORK_ERROR: 'Wystąpił problem z połączeniem sieciowym',
  AUTHENTICATION_REQUIRED: 'Musisz się zalogować, aby wykonać tę operację',
  INVALID_FORM: 'Formularz zawiera błędy. Sprawdź podane dane.'
};