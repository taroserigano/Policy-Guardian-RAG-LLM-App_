/**
 * Authentication API client.
 * Handles all authentication-related API calls.
 */
import axios from "axios";
import { getAccessToken, getRefreshToken } from "../contexts/AuthContext";

const API_URL = "http://localhost:8003/api/v1/auth";

// Create axios instance for auth requests
const authAxios = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add auth token to requests
authAxios.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authApi = {
  /**
   * Register a new user
   */
  async register(email, password, fullName = null) {
    const response = await authAxios.post("/register", {
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  },

  /**
   * Login user and get tokens
   */
  async login(email, password) {
    const response = await authAxios.post("/login", {
      email,
      password,
    });
    return response.data;
  },

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken) {
    const response = await authAxios.post("/refresh", {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  /**
   * Get current user profile
   */
  async getCurrentUser() {
    const response = await authAxios.get("/me");
    return response.data;
  },

  /**
   * Update user profile
   */
  async updateProfile(data) {
    const response = await authAxios.patch("/me", data);
    return response.data;
  },

  /**
   * Change password
   */
  async changePassword(currentPassword, newPassword) {
    await authAxios.post("/change-password", {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },

  /**
   * Logout (client-side cleanup)
   */
  async logout() {
    try {
      await authAxios.post("/logout");
    } catch {
      // Ignore errors - we'll clear local storage anyway
    }
  },
};

export default authApi;
