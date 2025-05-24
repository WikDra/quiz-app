/**
 * Globalne stałe aplikacji Quiz-App
 */

// API URLs
export const API_BASE_URL = 'http://localhost:5000';
export const API_ENDPOINTS = {
  PRODUCTS: `${API_BASE_URL}/products`,
  PRODUCT_BY_ID: (id) => `${API_BASE_URL}/products/${id}`,
  REGISTER: `${API_BASE_URL}/auth/register`,
  LOGIN: `${API_BASE_URL}/auth/login`,
  REFRESH: `${API_BASE_URL}/refresh`,
  GOOGLE_LOGIN_REDIRECT: `${API_BASE_URL}/auth/oauth2/redirect`,
  GOOGLE_LOGIN_CALLBACK: `${API_BASE_URL}/auth/oauth2/callback`,
  PROFILE: `${API_BASE_URL}/profile`,
  CREATE_PAYMENT: `${API_BASE_URL}/payments/create`,
  STRIPE_WEBHOOK: `${API_BASE_URL}/payments/webhook`,
  CREATE_PAYMENT_GENERIC: `${API_BASE_URL}/payments/create-payment`,
  QUIZ: `${API_BASE_URL}/quiz`,
  QUIZ_BY_ID: (id) => `${API_BASE_URL}/quiz/${id}`,
  QUIZ_MY: `${API_BASE_URL}/quiz/my`,
  QUIZ_ATTEMPT: (id) => `${API_BASE_URL}/quiz/${id}/attempt`,
  
  // User endpoints
  USER_PROFILE: `${API_BASE_URL}/api/user/profile`,
  USER_STATS: `${API_BASE_URL}/api/user/stats`,
  USER_PASSWORD: `${API_BASE_URL}/api/user/password`,
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

// Klucze dla localStorage
export const STORAGE_KEYS = {
  USER: 'quiz_app_user',
  ACCESS_TOKEN: 'quiz_app_access_token',
  REFRESH_TOKEN: 'quiz_app_refresh_token',
  THEME: 'quiz_app_theme',
  QUIZ_HISTORY: 'quiz_app_history'
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