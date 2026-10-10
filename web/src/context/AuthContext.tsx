import React, { createContext, useContext, useEffect, useState } from 'react';
import { api, UserAccount } from '../api/endpoints';
import { getAccessToken, setAccessToken, SESSION_EXPIRED_EVENT } from '../api/client';

interface AuthContextType {
  user: UserAccount | null;
  isLoading: boolean;
  login: (credentials: { username_or_email?: string; email?: string; password: string; remember_me?: boolean }) => Promise<UserAccount>;
  register: (payload: { email: string; password: string; full_name?: string; accept_disclaimer: boolean }) => Promise<UserAccount>;
  logout: () => Promise<void>;
  updateUser: (user: UserAccount) => void;
  sessionExpiredToast: boolean;
  dismissSessionToast: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserAccount | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [sessionExpiredToast, setSessionExpiredToast] = useState<boolean>(false);

  // Initialize auth session on app mount
  useEffect(() => {
    let isMounted = true;

    async function initAuth() {
      try {
        // Attempt refresh via httpOnly cookie
        const res = await api.auth.refresh();
        if (isMounted && res?.access_token) {
          setAccessToken(res.access_token);
          setUser(res.user);
        }
      } catch (err) {
        if (isMounted) {
          setUser(null);
          setAccessToken(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    initAuth();

    // Listen for 401 session expiration
    const handleSessionExpired = () => {
      setUser(null);
      setAccessToken(null);
      setSessionExpiredToast(true);
    };

    window.addEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired);
    return () => {
      isMounted = false;
      window.removeEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired);
    };
  }, []);

  const login = async (credentials: { username_or_email?: string; email?: string; password: string; remember_me?: boolean }) => {
    const res = await api.auth.login(credentials);
    setAccessToken(res.access_token);
    setUser(res.user);
    setSessionExpiredToast(false);
    return res.user;
  };

  const register = async (payload: { email: string; password: string; full_name?: string; accept_disclaimer: boolean }) => {
    const res = await api.auth.register(payload);
    setAccessToken(res.access_token);
    setUser(res.user);
    setSessionExpiredToast(false);
    return res.user;
  };

  const logout = async () => {
    try {
      await api.auth.logout();
    } catch {
      // ignore
    } finally {
      setUser(null);
      setAccessToken(null);
    }
  };

  const updateUser = (updated: UserAccount) => {
    setUser(updated);
  };

  const dismissSessionToast = () => {
    setSessionExpiredToast(false);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        login,
        register,
        logout,
        updateUser,
        sessionExpiredToast,
        dismissSessionToast,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
