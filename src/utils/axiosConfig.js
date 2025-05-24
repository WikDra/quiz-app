import axios from 'axios';

const instance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000', // Usuwam /api, bo endpointy są bez tego prefixu
  withCredentials: true, // Important for sending cookies with requests
});

// Add a request interceptor to include the token if available
instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Optional: Add a response interceptor for global error handling or token refresh
instance.interceptors.response.use(
  (response) => response,
  (error) => {
    // Example: Handle 401 Unauthorized (e.g., token expired)
    if (error.response && error.response.status === 401) {
      // Potentially redirect to login or try to refresh the token
      console.error('Unauthorized request. Token might be invalid or expired.');
      // localStorage.removeItem('token');
      // localStorage.removeItem('user');
      // window.location.href = '/login'; 
    }
    return Promise.reject(error);
  }
);

export default instance;
