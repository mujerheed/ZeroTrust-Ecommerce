import axios from 'axios';
import { validateSession, clearSession, UserRole } from './session';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Get the current user role from the URL path
 */
function getCurrentRole(): UserRole | null {
  if (typeof window === 'undefined') return null;
  const path = window.location.pathname;
  if (path.startsWith('/vendor')) return 'vendor';
  if (path.startsWith('/ceo')) return 'ceo';
  if (path.startsWith('/buyer')) return 'buyer';
  return null;
}

/**
 * Get role-specific token key
 */
function getTokenKey(role?: UserRole | null): string {
  const currentRole = role || getCurrentRole();
  return currentRole ? `${currentRole}_token` : 'token';
}

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include the token if available
api.interceptors.request.use((config) => {
  // Skip session validation for auth endpoints (login, register, verify-otp)
  const isAuthEndpoint = config.url?.includes('/auth/') || 
                         config.url?.includes('/login') || 
                         config.url?.includes('/register') ||
                         config.url?.includes('/verify-otp');
  
  if (!isAuthEndpoint) {
    // Validate session before each request (except auth endpoints)
    if (typeof window !== 'undefined') {
      const currentRole = getCurrentRole();
      const isValid = validateSession(currentRole || undefined);
      if (!isValid) {
        clearSession(currentRole || undefined);
        // Redirect to login
        if (window.location.pathname.startsWith('/vendor') && !window.location.pathname.includes('/login')) {
          window.location.href = '/vendor/login?expired=true';
        } else if (window.location.pathname.startsWith('/ceo') && !window.location.pathname.includes('/login')) {
          window.location.href = '/ceo/login?expired=true';
        }
        return Promise.reject(new Error('Session expired'));
      }
    }
  }

  // Get role-specific token
  const tokenKey = getTokenKey();
  const token = typeof window !== 'undefined' ? localStorage.getItem(tokenKey) : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const setToken = (token: string, role?: UserRole) => {
  if (typeof window !== 'undefined') {
    const tokenKey = getTokenKey(role);
    localStorage.setItem(tokenKey, token);
  }
};

export const clearToken = (role?: UserRole) => {
  if (typeof window !== 'undefined') {
    const tokenKey = getTokenKey(role);
    localStorage.removeItem(tokenKey);
  }
};
