'use client';

import { useEffect } from 'react';
import { useAuth } from './contexts/AuthContext';
import { useRouter } from 'next/navigation';

export default function HomePage() {
  const { user, token, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading) {
      if (token && user) {
        router.push('/scan');
      } else {
        router.push('/login');
      }
    }
  }, [token, user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-green-600 mx-auto"></div>
          <h2 className="mt-4 text-xl font-semibold text-gray-900">Loading SmartBin...</h2>
          <p className="mt-2 text-gray-600">Please wait while we prepare your experience</p>
        </div>
      </div>
    );
  }

  return null;
}
