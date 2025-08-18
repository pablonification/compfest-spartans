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
    
    if (storedToken && storedUser && storedToken !== 'null') {
      try {
        // Validate token by checking if it's expired
        const tokenParts = storedToken.split('.');
        if (tokenParts.length === 3) {
          const tokenData = JSON.parse(atob(tokenParts[1]));
          const currentTime = Math.floor(Date.now() / 1000);
          
          if (tokenData.exp > currentTime) {
            // Token is still valid
            setToken(storedToken);
            setUser(JSON.parse(storedUser));
            console.log('Token loaded successfully, expires:', new Date(tokenData.exp * 1000));
          } else {
            // Token expired, remove from storage
            console.log('Token expired, removing from storage');
            localStorage.removeItem('smartbin_token');
            localStorage.removeItem('smartbin_user');
          }
        } else {
          console.log('Invalid token format, removing from storage');
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
    if (!userToken || userToken === 'null') {
      console.error('Invalid token provided to login');
      return;
    }
    
    console.log('Logging in user:', userData.email);
    setUser(userData);
    setToken(userToken);
    localStorage.setItem('smartbin_token', userToken);
    localStorage.setItem('smartbin_user', JSON.stringify(userData));
  };

  const logout = () => {
    console.log('Logging out user');
    setUser(null);
    setToken(null);
    localStorage.removeItem('smartbin_token');
    localStorage.removeItem('smartbin_user');
  };

  const updateUser = (userData) => {
    setUser(userData);
    localStorage.setItem('smartbin_user', JSON.stringify(userData));
  };

  const getAuthHeaders = () => {
    if (!token || token === 'null') {
      console.warn('Attempting to get auth headers with null token');
      console.warn('Current auth state:', { user: !!user, token: !!token, tokenValue: token });
      return {};
    }
    return {
      'Authorization': `Bearer ${token}`,
    };
  };

  const getJsonHeaders = () => {
    if (!token || token === 'null') {
      console.warn('Attempting to get JSON headers with null token');
      console.warn('Current auth state:', { user: !!user, token: !!token, tokenValue: token });
      return {
        'Content-Type': 'application/json',
      };
    }
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    };
  };

  // Enhanced token validation
  const validateToken = () => {
    if (!token || token === 'null') {
      return false;
    }
    
    try {
      const tokenParts = token.split('.');
      if (tokenParts.length !== 3) {
        console.warn('Invalid token format');
        return false;
      }
      
      const tokenData = JSON.parse(atob(tokenParts[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      
      if (tokenData.exp <= currentTime) {
        console.warn('Token expired');
        logout();
        return false;
      }
      
      return true;
    } catch (error) {
      console.error('Token validation error:', error);
      logout();
      return false;
    }
  };

  // Enhanced authentication check
  const isAuthenticated = () => {
    const isValid = validateToken();
    if (!isValid) {
      console.warn('Authentication check failed:', { user: !!user, token: !!token, tokenValid: isValid });
    }
    return isValid && !!user;
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
