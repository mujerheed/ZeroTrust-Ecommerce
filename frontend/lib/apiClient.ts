/**
 * API Client with automatic token refresh and error handling
 * 
 * Features:
 * - Automatically adds Authorization header
 * - Detects 401 errors and attempts token refresh
 * - Handles expired sessions gracefully
 * - Centralized error handling
 */

import { sessionManager } from "./sessionManager";
import { toast } from "sonner";

export interface ApiResponse<T = any> {
  status: string;
  message: string;
  data?: T;
}

export interface ApiError {
  status: string;
  message: string;
  detail?: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = "/api") {
    this.baseUrl = baseUrl;
  }

  /**
   * Make authenticated request with auto-retry on 401
   */
  async request<T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    const token = sessionManager.getToken();

    // Add Authorization header if token exists
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Handle 401 Unauthorized (expired or invalid token)
      if (response.status === 401) {
        const errorData = await response.json().catch(() => null);
        const errorMessage = errorData?.detail || errorData?.message || "Unauthorized";

        // Check if it's an expired session
        if (errorMessage.toLowerCase().includes("expired")) {
          console.log("[ApiClient] Session expired, attempting refresh...");

          // Attempt token refresh
          const refreshed = await sessionManager.refreshToken();

          if (refreshed) {
            // Retry original request with new token
            const newToken = sessionManager.getToken();
            if (newToken) {
              headers["Authorization"] = `Bearer ${newToken}`;
              const retryResponse = await fetch(url, {
                ...options,
                headers,
              });

              if (retryResponse.ok) {
                return await retryResponse.json();
              }
            }
          }

          // Refresh failed or retry failed - redirect to login
          sessionManager.logout();
          throw new Error("Session expired. Please log in again.");
        } else {
          // Invalid token (not expired) - redirect to login
          sessionManager.logout();
          throw new Error("Invalid authentication. Please log in.");
        }
      }

      // Handle other error responses
      if (!response.ok) {
        const errorData: ApiError = await response.json().catch(() => ({
          status: "error",
          message: `Request failed with status ${response.status}`,
        }));

        throw new Error(errorData.message || errorData.detail || "Request failed");
      }

      // Parse and return successful response
      const data: ApiResponse<T> = await response.json();
      return data;

    } catch (error: any) {
      console.error("[ApiClient] Request error:", error);

      // Show user-friendly error toast
      if (error.message && !error.message.includes("log in")) {
        toast.error("Request Failed", {
          description: error.message,
        });
      }

      throw error;
    }
  }

  /**
   * Convenience methods for common HTTP verbs
   */
  async get<T = any>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: "GET" });
  }

  async post<T = any>(endpoint: string, body?: any, options?: RequestInit): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async patch<T = any>(endpoint: string, body?: any, options?: RequestInit): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async put<T = any>(endpoint: string, body?: any, options?: RequestInit): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      ...options,
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  async delete<T = any>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { ...options, method: "DELETE" });
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export convenience functions
export const get = <T = any>(endpoint: string) => apiClient.get<T>(endpoint);
export const post = <T = any>(endpoint: string, body?: any) => apiClient.post<T>(endpoint, body);
export const patch = <T = any>(endpoint: string, body?: any) => apiClient.patch<T>(endpoint, body);
export const put = <T = any>(endpoint: string, body?: any) => apiClient.put<T>(endpoint, body);
export const del = <T = any>(endpoint: string) => apiClient.delete<T>(endpoint);
