'use client';

import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing token on app load
    const storedToken = localStorage.getItem('smartbin_token');
    const storedUser = localStorage.getItem('smartbin_user');
    
    if (storedToken && storedUser) {
      try {
        // Validate token by checking if it's expired
        const tokenData = JSON.parse(atob(storedToken.split('.')[1]));
        const currentTime = Math.floor(Date.now() / 1000);
        
        if (tokenData.exp > currentTime) {
          // Token is still valid
          setToken(storedToken);
          setUser(JSON.parse(storedUser));
        } else {
          // Token expired, remove from storage
          console.log('Token expired, removing from storage');
          localStorage.removeItem('smartbin_token');
          localStorage.removeItem('smartbin_user');
        }
      } catch (error) {
        console.error('Error parsing stored user data or token:', error);
        localStorage.removeItem('smartbin_token');
        localStorage.removeItem('smartbin_user');
      }
    }
    
    setLoading(false);
  }, []);

  const login = (userData, userToken) => {
    setUser(userData);
    setToken(userToken);
    localStorage.setItem('smartbin_token', userToken);
    localStorage.setItem('smartbin_user', JSON.stringify(userData));
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('smartbin_token');
    localStorage.removeItem('smartbin_user');
  };

  const updateUser = (userData) => {
    setUser(userData);
    localStorage.setItem('smartbin_user', JSON.stringify(userData));
  };

  const isAuthenticated = () => {
    return !!token && !!user;
  };

  const getAuthHeaders = () => {
    return {
      'Authorization': `Bearer ${token}`,
    };
  };

  const getJsonHeaders = () => {
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  };

  const value = {
    user,
    token,
    loading,
    login,
    logout,
    updateUser,
    isAuthenticated,
    getAuthHeaders,
    getJsonHeaders,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
