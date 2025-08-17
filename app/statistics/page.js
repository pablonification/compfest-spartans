'use client';

import { useAuth } from '../contexts/AuthContext';
import ProtectedRoute from '../components/ProtectedRoute';
import StatisticsDashboard from '../components/StatisticsDashboard';
import Leaderboard from '../components/Leaderboard';
import NotificationBell from '../components/NotificationBell';

export default function StatisticsPage() {
  const { user } = useAuth();

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <h1 className="text-xl font-semibold text-gray-900">
                  📊 Statistik SmartBin
                </h1>
              </div>
              <div className="flex items-center space-x-4">
                <NotificationBell />
                <div className="text-sm text-gray-600">
                  Hi, {user?.name || user?.email}!
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="mb-6">
              <h2 className="text-3xl font-bold text-gray-900">
                Dashboard Statistik Personal
              </h2>
              <p className="mt-2 text-gray-600">
                Lihat progress dan impact kamu dalam program daur ulang SmartBin
              </p>
            </div>

            <StatisticsDashboard />
            
            {/* Leaderboard Section */}
            <div className="mt-8">
              <Leaderboard />
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
