/**
 * useAuth hook — manages auth state in localStorage + React state.
 *
 * Stores the JWT token and user profile in localStorage so auth
 * persists across page refreshes. Clears state on logout.
 *
 * This is a simple client-side auth implementation for Stage 2.
 * Stage 6 will add httpOnly cookie sessions and OAuth.
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import type { LoginResponse, UserResponse } from "@/types";

const TOKEN_KEY = "techhunt_token";
const USER_KEY = "techhunt_user";

export interface AuthState {
  token: string | null;
  user: UserResponse | null;
  isLoggedIn: boolean;
  isLoading: boolean;
}

export interface UseAuthReturn extends AuthState {
  setAuth: (response: LoginResponse) => void;
  logout: () => void;
}

export function useAuth(): UseAuthReturn {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Rehydrate from localStorage on mount
  useEffect(() => {
    try {
      const storedToken = localStorage.getItem(TOKEN_KEY);
      const storedUser = localStorage.getItem(USER_KEY);
      if (storedToken && storedUser) {
        setToken(storedToken);
        setUser(JSON.parse(storedUser) as UserResponse);
      }
    } catch {
      // localStorage not available (SSR guard)
    } finally {
      setIsLoading(false);
    }
  }, []);

  const setAuth = useCallback((response: LoginResponse) => {
    try {
      localStorage.setItem(TOKEN_KEY, response.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(response.user));
    } catch {
      // localStorage not available
    }
    setToken(response.access_token);
    setUser(response.user);
  }, []);

  const logout = useCallback(() => {
    try {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    } catch {
      // localStorage not available
    }
    setToken(null);
    setUser(null);
  }, []);

  return {
    token,
    user,
    isLoggedIn: token !== null && user !== null,
    isLoading,
    setAuth,
    logout,
  };
}
