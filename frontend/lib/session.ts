/**
 * Session Management for Multi-Role Portal
 * Implements 60-minute auto-logout for enhanced security
 * Supports separate sessions for Vendor and CEO roles
 */

const SESSION_DURATION = 60 * 60 * 1000; // 60 minutes in milliseconds
const WARNING_THRESHOLD = 5 * 60 * 1000; // Show warning at 5 minutes remaining

export type UserRole = 'vendor' | 'ceo' | 'buyer';

export interface SessionInfo {
  startTime: number;
  remainingTime: number;
  isExpired: boolean;
  isWarning: boolean;
}

/**
 * Get session key for specific role
 */
function getSessionKey(role?: UserRole): string {
  // Detect role from current path if not provided
  if (!role && typeof window !== 'undefined') {
    const path = window.location.pathname;
    if (path.startsWith('/vendor')) {
      role = 'vendor';
    } else if (path.startsWith('/ceo')) {
      role = 'ceo';
    } else if (path.startsWith('/buyer')) {
      role = 'buyer';
    }
  }
  return `${role || 'vendor'}_session_start`;
}

/**
 * Initialize session on successful login
 * @param role - User role (vendor, ceo, buyer) - auto-detected from path if not provided
 */
export function initSession(role?: UserRole): void {
  if (typeof window === 'undefined') return;
  const now = Date.now();
  const sessionKey = getSessionKey(role);
  localStorage.setItem(sessionKey, now.toString());
}

/**
 * Get current session information
 * @param role - User role (vendor, ceo, buyer) - auto-detected from path if not provided
 */
export function getSessionInfo(role?: UserRole): SessionInfo {
  if (typeof window === 'undefined') {
    return { startTime: 0, remainingTime: 0, isExpired: true, isWarning: false };
  }

  const sessionKey = getSessionKey(role);
  const sessionStart = localStorage.getItem(sessionKey);
  if (!sessionStart) {
    return { startTime: 0, remainingTime: 0, isExpired: true, isWarning: false };
  }

  const startTime = parseInt(sessionStart, 10);
  const now = Date.now();
  const elapsed = now - startTime;
  const remainingTime = SESSION_DURATION - elapsed;

  return {
    startTime,
    remainingTime: Math.max(0, remainingTime),
    isExpired: remainingTime <= 0,
    isWarning: remainingTime > 0 && remainingTime <= WARNING_THRESHOLD,
  };
}

/**
 * Format remaining time as MM:SS
 */
export function formatSessionTime(milliseconds: number): string {
  const totalSeconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

/**
 * Check if session is valid, clear if expired
 * Returns true if session is still valid
 * @param role - User role (vendor, ceo, buyer) - auto-detected from path if not provided
 */
export function validateSession(role?: UserRole): boolean {
  const { isExpired } = getSessionInfo(role);
  if (isExpired) {
    clearSession(role);
    return false;
  }
  return true;
}

/**
 * Clear session data
 * @param role - User role (vendor, ceo, buyer) - auto-detected from path if not provided
 */
export function clearSession(role?: UserRole): void {
  if (typeof window === 'undefined') return;
  const sessionKey = getSessionKey(role);
  const currentRole = role || (window.location.pathname.startsWith('/vendor') ? 'vendor' : 
                                window.location.pathname.startsWith('/ceo') ? 'ceo' : 
                                window.location.pathname.startsWith('/buyer') ? 'buyer' : null);
  
  localStorage.removeItem(sessionKey);
  
  // Remove role-specific token
  if (currentRole) {
    localStorage.removeItem(`${currentRole}_token`);
  }
  
  // Clean up role-specific data
  if (currentRole === 'vendor') {
    localStorage.removeItem('vendor_id');
  } else if (currentRole === 'ceo') {
    localStorage.removeItem('ceo_id');
  }
}

/**
 * Extend session (call on user activity if implementing activity-based timeout)
 * For now, we use fixed 60-minute timeout from login
 */
export function extendSession(): void {
  // Optional: Reset session timer on activity
  // For strict 60-min from login, comment this out
  // initSession();
}
