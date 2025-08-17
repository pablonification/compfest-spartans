'use client';

import ProtectedRoute from '../components/ProtectedRoute';
import NotificationBell from '../components/NotificationBell';
import EducationGrid from '../components/EducationGrid';

export default function EducationPage() {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center h-16">
            <h1 className="text-xl font-semibold text-gray-900">📚 Konten Edukasi</h1>
            <NotificationBell />
          </div>
        </header>

        <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          <p className="text-gray-600 mb-6">Pelajari lebih banyak tentang daur ulang plastik dan dampaknya.</p>
          <EducationGrid />
        </main>
      </div>
    </ProtectedRoute>
  );
}
