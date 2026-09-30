import axios, { AxiosError } from 'axios';
import type { ApiBaseResponse } from '../types/api';

// Resolves API gateway base URL from either VITE_API_BASE_URL or VITE_API_URL
// and guarantees trailing /api suffix for client route consistency.
const getApiBaseUrl = (): string => {
  const envUrl = (
    import.meta.env.VITE_API_BASE_URL ||
    import.meta.env.VITE_API_URL ||
    'http://localhost:5001/api'
  ).trim();
  const withoutTrailingSlash = envUrl.replace(/\/+$/, '');
  return withoutTrailingSlash.endsWith('/api')
    ? withoutTrailingSlash
    : `${withoutTrailingSlash}/api`;
};

export const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 60000,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('jwt_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiBaseResponse<unknown>>) => {
    if (error.response?.status === 401) {
      console.warn('Authentication token expired or invalid.');
      localStorage.removeItem('jwt_token');
      window.dispatchEvent(new Event('auth-unauthorized'));
    }
    return Promise.reject(error);
  }
);
