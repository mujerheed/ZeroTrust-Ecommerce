/**
 * Session Manager for TrustGuard CEO Portal
 * 
 * Handles JWT token lifecycle:
 * - Auto-refresh tokens before expiration (at 50 minutes)
 * - Detect and handle expired sessions
 * - Automatic logout on expiration
 * - Secure token storage
 */

import { toast } from "sonner";

const TOKEN_KEY = "trustguard_token";
const USER_KEY = "trustguard_user";
const TOKEN_EXPIRY_KEY = "trustguard_token_expiry";

// Token refresh interval: 50 minutes (before 60-minute expiration)
const REFRESH_INTERVAL = 50 * 60 * 1000; // 50 minutes in milliseconds
const TOKEN_LIFETIME = 60 * 60 * 1000; // 60 minutes in milliseconds

export interface UserSession {
  user_id: string;
  role: string;
  name?: string;
  email?: string;
}

class SessionManager {
  private refreshTimer: NodeJS.Timeout | null = null;
  private expiryCheckTimer: NodeJS.Timeout | null = null;

  /**
   * Initialize session after successful login
   */
  initializeSession(token: string, user: UserSession): void {
    // Store token and user data
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    
    // Calculate and store expiry time
    const expiryTime = Date.now() + TOKEN_LIFETIME;
    localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());

    // Start auto-refresh timer
    this.startAutoRefresh();
    
    // Start expiry check timer
    this.startExpiryCheck();

    console.log("[SessionManager] Session initialized", {
      user_id: user.user_id,
      role: user.role,
      expiresIn: "60 minutes"
    });
  }

  /**
   * Get current JWT token
   */
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  /**
   * Get current user session
   */
  getUser(): UserSession | null {
    const userStr = localStorage.getItem(USER_KEY);
    if (!userStr) return null;

    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    const token = this.getToken();
    const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);

    if (!token || !expiry) return false;

    // Check if token is expired
    const expiryTime = parseInt(expiry, 10);
    if (Date.now() > expiryTime) {
      this.handleSessionExpired();
      return false;
    }

    return true;
  }

  /**
   * Start auto-refresh timer (refresh at 50 minutes)
   */
  private startAutoRefresh(): void {
    // Clear existing timer
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
    }

    // Set new timer
    this.refreshTimer = setInterval(() => {
      this.refreshToken();
    }, REFRESH_INTERVAL);
  }

  /**
   * Start expiry check timer (check every minute)
   */
  private startExpiryCheck(): void {
    // Clear existing timer
    if (this.expiryCheckTimer) {
      clearInterval(this.expiryCheckTimer);
    }

    // Check every minute
    this.expiryCheckTimer = setInterval(() => {
      const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
      if (!expiry) return;

      const expiryTime = parseInt(expiry, 10);
      const timeLeft = expiryTime - Date.now();

      // If less than 5 minutes left, show warning
      if (timeLeft > 0 && timeLeft < 5 * 60 * 1000) {
        const minutesLeft = Math.ceil(timeLeft / 60000);
        toast.warning(`Session expires in ${minutesLeft} minute${minutesLeft > 1 ? 's' : ''}`);
      }

      // If expired, handle it
      if (timeLeft <= 0) {
        this.handleSessionExpired();
      }
    }, 60 * 1000); // Check every minute
  }

  /**
   * Refresh token via API
   */
  async refreshToken(): Promise<boolean> {
    const token = this.getToken();
    if (!token) {
      console.error("[SessionManager] No token to refresh");
      return false;
    }

    try {
      const response = await fetch("/api/auth/refresh-token", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        }
      });

      if (response.ok) {
        const data = await response.json();
        const newToken = data.data?.token;
        const user = this.getUser();

        if (newToken && user) {
          // Update token and expiry
          localStorage.setItem(TOKEN_KEY, newToken);
          const newExpiry = Date.now() + TOKEN_LIFETIME;
          localStorage.setItem(TOKEN_EXPIRY_KEY, newExpiry.toString());

          console.log("[SessionManager] Token refreshed successfully");
          toast.success("Session extended", {
            description: "You can continue working securely."
          });
          return true;
        }
      } else if (response.status === 401) {
        // Token expired, can't refresh
        this.handleSessionExpired();
        return false;
      } else {
        console.error("[SessionManager] Token refresh failed:", response.status);
        return false;
      }
    } catch (error) {
      console.error("[SessionManager] Token refresh error:", error);
      return false;
    }

    return false;
  }

  /**
   * Handle expired session
   */
  private handleSessionExpired(): void {
    console.log("[SessionManager] Session expired");
    
    // Clear timers
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
    if (this.expiryCheckTimer) {
      clearInterval(this.expiryCheckTimer);
      this.expiryCheckTimer = null;
    }

    // Clear storage
    this.clearSession();

    // Show notification
    toast.error("Session Expired", {
      description: "Please log in again for security.",
      duration: 5000
    });

    // Redirect to login
    window.location.href = "/login";
  }

  /**
   * Manual logout
   */
  logout(): void {
    console.log("[SessionManager] Manual logout");

    // Clear timers
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
    if (this.expiryCheckTimer) {
      clearInterval(this.expiryCheckTimer);
      this.expiryCheckTimer = null;
    }

    // Clear storage
    this.clearSession();

    // Show notification
    toast.success("Logged out successfully");

    // Redirect to login
    window.location.href = "/login";
  }

  /**
   * Clear all session data
   */
  private clearSession(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
  }

  /**
   * Stop all timers (cleanup)
   */
  cleanup(): void {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = null;
    }
    if (this.expiryCheckTimer) {
      clearInterval(this.expiryCheckTimer);
      this.expiryCheckTimer = null;
    }
  }
}

// Export singleton instance
export const sessionManager = new SessionManager();

// Export utility functions
export const getToken = () => sessionManager.getToken();
export const getUser = () => sessionManager.getUser();
export const isAuthenticated = () => sessionManager.isAuthenticated();
export const logout = () => sessionManager.logout();
