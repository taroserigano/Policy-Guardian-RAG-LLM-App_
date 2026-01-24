/**
 * Authentication Context
 * Manages user authentication state across the application.
 */
import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi } from '../api/auth';

const AuthContext = createContext(null);

// Token storage keys
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_KEY = 'user';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load user from storage on mount
  useEffect(() => {
    const loadUser = async () => {
      try {
        const token = localStorage.getItem(ACCESS_TOKEN_KEY);
        const storedUser = localStorage.getItem(USER_KEY);
        
        if (token && storedUser) {
          // Validate token by fetching current user
          try {
            const userData = await authApi.getCurrentUser();
            setUser(userData);
            localStorage.setItem(USER_KEY, JSON.stringify(userData));
          } catch (err) {
            // Token might be expired, try to refresh
            const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
            if (refreshToken) {
              try {
                const tokens = await authApi.refreshToken(refreshToken);
                saveTokens(tokens);
                const userData = await authApi.getCurrentUser();
                setUser(userData);
                localStorage.setItem(USER_KEY, JSON.stringify(userData));
              } catch {
                // Refresh failed, clear everything
                clearAuth();
              }
            } else {
              clearAuth();
            }
          }
        }
      } catch (err) {
        console.error('Auth load error:', err);
        clearAuth();
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, []);

  const saveTokens = (tokens) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  };

  const clearAuth = () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
  };

  const login = useCallback(async (email, password) => {
    setError(null);
    try {
      const tokens = await authApi.login(email, password);
      saveTokens(tokens);
      
      const userData = await authApi.getCurrentUser();
      setUser(userData);
      localStorage.setItem(USER_KEY, JSON.stringify(userData));
      
      return userData;
    } catch (err) {
      const message = err.response?.data?.detail || 'Login failed';
      setError(message);
      throw new Error(message);
    }
  }, []);

  const register = useCallback(async (email, password, fullName) => {
    setError(null);
    try {
      const userData = await authApi.register(email, password, fullName);
      
      // Auto-login after registration
      const tokens = await authApi.login(email, password);
      saveTokens(tokens);
      setUser(userData);
      localStorage.setItem(USER_KEY, JSON.stringify(userData));
      
      return userData;
    } catch (err) {
      const message = err.response?.data?.detail || 'Registration failed';
      setError(message);
      throw new Error(message);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignore logout API errors
    } finally {
      clearAuth();
    }
  }, []);

  const updateProfile = useCallback(async (data) => {
    setError(null);
    try {
      const updatedUser = await authApi.updateProfile(data);
      setUser(updatedUser);
      localStorage.setItem(USER_KEY, JSON.stringify(updatedUser));
      return updatedUser;
    } catch (err) {
      const message = err.response?.data?.detail || 'Update failed';
      setError(message);
      throw new Error(message);
    }
  }, []);

  const changePassword = useCallback(async (currentPassword, newPassword) => {
    setError(null);
    try {
      await authApi.changePassword(currentPassword, newPassword);
    } catch (err) {
      const message = err.response?.data?.detail || 'Password change failed';
      setError(message);
      throw new Error(message);
    }
  }, []);

  const value = {
    user,
    loading,
    error,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    updateProfile,
    changePassword,
    clearError: () => setError(null),
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Get access token for API requests
export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

// Get refresh token
export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export default AuthContext;
