'use client';

import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function AuthDebugger() {
  const auth = useAuth();
  const [isVisible, setIsVisible] = useState(false);

  // Only show in development
  if (process.env.NODE_ENV !== 'development') {
    return null;
  }

  const toggleVisibility = () => setIsVisible(!isVisible);

  if (!isVisible) {
    return (
      <button
        onClick={toggleVisibility}
        className="fixed bottom-4 right-4 bg-gray-800 text-white p-2 rounded-full shadow-lg hover:bg-gray-700 transition-colors z-50"
        title="Show Auth Debugger"
      >
        🔍
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 bg-white border border-gray-300 rounded-lg shadow-lg p-4 max-w-sm z-50">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-800">🔍 Auth Debugger</h3>
        <button
          onClick={toggleVisibility}
          className="text-gray-500 hover:text-gray-700"
        >
          ✕
        </button>
      </div>
      
      <div className="space-y-2 text-xs">
        <div className="flex justify-between">
          <span className="text-gray-600">User:</span>
          <span className={auth.user ? 'text-green-600' : 'text-red-600'}>
            {auth.user ? '✅' : '❌'}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-600">Token:</span>
          <span className={auth.token ? 'text-green-600' : 'text-red-600'}>
            {auth.token ? '✅' : '❌'}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-600">Loading:</span>
          <span className={auth.loading ? 'text-yellow-600' : 'text-green-600'}>
            {auth.loading ? '⏳' : '✅'}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-600">Authenticated:</span>
          <span className={auth.isAuthenticated() ? 'text-green-600' : 'text-red-600'}>
            {auth.isAuthenticated() ? '✅' : '❌'}
          </span>
        </div>
        
        {auth.token && (
          <div className="pt-2 border-t border-gray-200">
            <div className="text-gray-600 mb-1">Token Preview:</div>
            <div className="bg-gray-100 p-2 rounded text-xs font-mono break-all">
              {auth.token.substring(0, 50)}...
            </div>
          </div>
        )}
        
        {auth.user && (
          <div className="pt-2 border-t border-gray-200">
            <div className="text-gray-600 mb-1">User Info:</div>
            <div className="text-xs">
              <div>Email: {auth.user.email}</div>
              <div>Name: {auth.user.name || 'N/A'}</div>
              <div>Points: {auth.user.points || 0}</div>
            </div>
          </div>
        )}
      </div>
      
      <div className="mt-3 pt-2 border-t border-gray-200">
        <button
          onClick={() => {
            console.log('Auth State:', auth);
            console.log('localStorage smartbin_token:', localStorage.getItem('smartbin_token'));
            console.log('localStorage smartbin_user:', localStorage.getItem('smartbin_user'));
          }}
          className="w-full text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
        >
          Log to Console
        </button>
      </div>
    </div>
  );
}
