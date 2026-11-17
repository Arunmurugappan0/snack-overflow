import axios from 'axios';

const TOKEN_KEY = 'snack-overflow-token';

export function getStoredToken() {
  let token = sessionStorage.getItem(TOKEN_KEY);
  if (!token) {
    token = localStorage.getItem('token');
    if (token) {
      sessionStorage.setItem(TOKEN_KEY, token);
      localStorage.removeItem('token');
    }
  }
  return token;
}

export function storeToken(token) {
  sessionStorage.setItem(TOKEN_KEY, token);
  localStorage.removeItem('token');
}

export function clearToken() {
  sessionStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem('token');
}

export function errorMessage(error) {
  const apiMessage = error.response?.data?.error?.message;
  if (apiMessage) return apiMessage;
  if (error.response?.status === 401) return 'Your session has expired. Please sign in again.';
  if (error.response?.status === 403) return 'You are not allowed to perform this action.';
  if (error.response?.status === 409) return 'This action conflicts with the latest pantry data.';
  if (!error.response) return 'Could not reach the pantry API. Check your connection and try again.';
  return 'The request could not be completed. Please try again.';
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000/api',
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && getStoredToken()) {
      clearToken();
      window.dispatchEvent(new Event('snack-overflow:unauthorized'));
    }
    return Promise.reject(error);
  },
);

export default api;
