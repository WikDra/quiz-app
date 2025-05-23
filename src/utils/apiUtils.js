/**
 * API utilities for cookie-based authentication with backend v2
 */
import { API_ENDPOINTS, STORAGE_KEYS } from './constants';

/**
 * Get CSRF token from localStorage or fetch from server
 */
export const getCsrfToken = async () => {
  let token = localStorage.getItem(STORAGE_KEYS.CSRF_TOKEN);
  
  if (!token) {
    try {
      const response = await fetch(API_ENDPOINTS.AUTH_CSRF, {
        method: 'GET',
        credentials: 'include',
        cache: 'no-cache'
      });
      
      if (response.ok) {
        const data = await response.json();
        token = data.csrf_token;
        localStorage.setItem(STORAGE_KEYS.CSRF_TOKEN, token);
      } else {
        console.warn('Failed to fetch CSRF token:', response.status);
      }
    } catch (error) {
      console.error('Error fetching CSRF token:', error);
      // Don't throw, just return null
    }
  }
  
  return token;
};

/**
 * Clear stored CSRF token
 */
export const clearCsrfToken = () => {
  localStorage.removeItem(STORAGE_KEYS.CSRF_TOKEN);
};

/**
 * Make authenticated API call with CSRF protection
 */
export const apiCall = async (url, options = {}) => {
  let headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };
    // Get CSRF token for all requests
  try {
    const csrfToken = await getCsrfToken();
    if (csrfToken) {
      headers['X-CSRFToken'] = csrfToken; // Use consistent header name
    }
  } catch (error) {
    console.warn('Error getting CSRF token:', error);
  }
  
  const defaultOptions = {
    credentials: 'include', // Include cookies
    headers
  };
    try {
    // For POST requests, include CSRF token in body as well
    if (options.method === 'POST' || options.method === 'PUT' || options.method === 'DELETE') {
      const existingBody = options.body ? JSON.parse(options.body) : {};
      options.body = JSON.stringify({
        ...existingBody,
        csrf_token: headers['X-CSRFToken']
      });
    }
    
    const response = await fetch(url, { ...defaultOptions, ...options, headers });
    
    // If we get 401 or 403, clear CSRF token and retry once
    if ((response.status === 401 || response.status === 403)) {
      clearCsrfToken();
      
      try {
        const newCsrfToken = await getCsrfToken();
        
        if (newCsrfToken) {
          headers['X-CSRF-TOKEN'] = newCsrfToken;
          
          return fetch(url, { 
            ...defaultOptions, 
            ...options, 
            headers
          });
        }
      } catch (retryError) {
        console.error('Error on CSRF token retry:', retryError);
      }
    }
    
    return response;
  } catch (error) {
    console.error('API call failed:', error, 'URL:', url);
    throw error;
  }
};

/**
 * Handle API response with error handling
 */
export const handleApiResponse = async (response) => {
  let data;
  
  try {
    data = await response.json();
  } catch (error) {
    throw new Error('Invalid response format');
  }
  
  if (!response.ok) {
    throw new Error(data.message || `HTTP error! status: ${response.status}`);
  }
  
  return data;
};

/**
 * Authentication API calls
 */
export const authApi = {
  async checkAuth() {
    const response = await apiCall(API_ENDPOINTS.AUTH_CHECK);
    return handleApiResponse(response);
  },

  async refreshToken() {
    const response = await apiCall(API_ENDPOINTS.AUTH_REFRESH, {
      method: 'POST'
    });
    return handleApiResponse(response);
  },

  async login(credentials) {
    const response = await apiCall(API_ENDPOINTS.AUTH_LOGIN, {
      method: 'POST',
      body: JSON.stringify(credentials)
    });
    return handleApiResponse(response);
  },

  async register(userData) {
    const response = await apiCall(API_ENDPOINTS.AUTH_REGISTER, {
      method: 'POST',
      body: JSON.stringify(userData)
    });
    return handleApiResponse(response);
  },

  async logout() {
    const response = await apiCall(API_ENDPOINTS.AUTH_LOGOUT, {
      method: 'POST'
    });
    clearCsrfToken(); // Clear CSRF token on logout
    return handleApiResponse(response);
  },

  async getCurrentUser() {
    const response = await apiCall(API_ENDPOINTS.AUTH_ME);
    return handleApiResponse(response);
  }
};

/**
 * Quiz API calls
 */
export const quizApi = {
  async getPublicQuizzes(page = 1, perPage = 10, search = '') {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
      ...(search && { search })
    });
    
    const response = await apiCall(`${API_ENDPOINTS.QUIZ}?${params}`);
    return handleApiResponse(response);
  },

  async getMyQuizzes() {
    const response = await apiCall(API_ENDPOINTS.QUIZ_MY);
    return handleApiResponse(response);
  },

  async getQuizById(id) {
    const response = await apiCall(API_ENDPOINTS.QUIZ_BY_ID(id));
    return handleApiResponse(response);
  },

  async createQuiz(quizData) {
    const response = await apiCall(API_ENDPOINTS.QUIZ, {
      method: 'POST',
      body: JSON.stringify(quizData)
    });
    return handleApiResponse(response);
  },

  async updateQuiz(id, quizData) {
    const response = await apiCall(API_ENDPOINTS.QUIZ_BY_ID(id), {
      method: 'PUT',
      body: JSON.stringify(quizData)
    });
    return handleApiResponse(response);
  },

  async deleteQuiz(id) {
    const response = await apiCall(API_ENDPOINTS.QUIZ_BY_ID(id), {
      method: 'DELETE'
    });
    return handleApiResponse(response);
  },

  async submitQuizAttempt(id, answers) {
    const response = await apiCall(API_ENDPOINTS.QUIZ_ATTEMPT(id), {
      method: 'POST',
      body: JSON.stringify({ answers })
    });
    return handleApiResponse(response);
  }
};

/**
 * User API calls
 */
export const userApi = {
  async getProfile() {
    const response = await apiCall(API_ENDPOINTS.USER_PROFILE);
    return handleApiResponse(response);
  },

  async updateProfile(profileData) {
    const response = await apiCall(API_ENDPOINTS.USER_PROFILE, {
      method: 'PUT',
      body: JSON.stringify(profileData)
    });
    return handleApiResponse(response);
  },

  async getStats() {
    const response = await apiCall(API_ENDPOINTS.USER_STATS);
    return handleApiResponse(response);
  },

  async changePassword(passwordData) {
    const response = await apiCall(API_ENDPOINTS.USER_PASSWORD, {
      method: 'PUT',
      body: JSON.stringify(passwordData)
    });
    return handleApiResponse(response);
  }
};

/**
 * Payment API calls
 */
export const paymentApi = {
  async createPaymentIntent(amount, currency = 'usd') {
    const response = await apiCall(API_ENDPOINTS.STRIPE_CREATE_PAYMENT, {
      method: 'POST',
      body: JSON.stringify({ amount, currency })
    });
    return handleApiResponse(response);
  },

  async getSubscriptionStatus() {
    const response = await apiCall(API_ENDPOINTS.STRIPE_SUBSCRIPTION);
    return handleApiResponse(response);
  }
};
