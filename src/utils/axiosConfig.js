import axios from 'axios';
import { getCsrfToken } from './apiUtils';

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api',
  withCredentials: true, // Important for sending cookies with requests
});

// Add a request interceptor to include CSRF token
instance.interceptors.request.use(
  async (config) => {
    // Get CSRF token for state-changing operations
    if (['post', 'put', 'delete', 'patch'].includes(config.method?.toLowerCase())) {
      const csrfToken = await getCsrfToken();
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor for global error handling
instance.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized (session expired)
    if (error.response && error.response.status === 401) {
      console.error('Unauthorized request. Session might be expired.');
      // Clear any stored CSRF token
      localStorage.removeItem('quiz_app_csrf_token');
      // Optionally redirect to login
      // window.location.href = '/login'; 
    }
    return Promise.reject(error);
  }
);

export default instance;
