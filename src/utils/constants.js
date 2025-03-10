/**
 * Globalne stałe aplikacji Quiz-App
 */

// API URLs
export const API_BASE_URL = 'http://localhost:3001';
export const API_ENDPOINTS = {
  QUIZ: `${API_BASE_URL}/quiz`,
  USERS: `${API_BASE_URL}/users.json`,
  QUIZ_BY_ID: (id) => `${API_BASE_URL}/quiz/${id}`
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

// Klucze dla localStorage
export const STORAGE_KEYS = {
  USER: 'user',
  THEME: 'theme',
  RECENT_QUIZZES: 'recentQuizzes'
};