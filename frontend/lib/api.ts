import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include the token if available
api.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const setToken = (token: string) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('token', token);
  }
};

export const clearToken = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('token');
  }
};
