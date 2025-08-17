'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function StatisticsDashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (user) {
      fetchStatistics();
    }
  }, [user]);

  const fetchStatistics = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/statistics/personal', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch statistics');
      }

      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
        <p className="text-red-600">Error: {error}</p>
        <button 
          onClick={fetchStatistics}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">📊 Statistik Personal</h2>
      
      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-lg p-6 text-center">
          <div className="text-3xl font-bold">{stats.total_bottles}</div>
          <div className="text-blue-100">Total Botol</div>
        </div>
        
        <div className="bg-gradient-to-br from-green-500 to-green-600 text-white rounded-lg p-6 text-center">
          <div className="text-3xl font-bold">{stats.total_points}</div>
          <div className="text-green-100">Total Poin</div>
        </div>
        
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white rounded-lg p-6 text-center">
          <div className="text-3xl font-bold">{stats.total_scans}</div>
          <div className="text-purple-100">Total Scan</div>
        </div>
      </div>

      {/* Monthly Progress */}
      <div className="bg-gray-50 rounded-lg p-6 mb-8">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">📅 Progress Bulan Ini</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Botol:</span>
            <span className="font-semibold text-blue-600">{stats.bottles_this_month}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Poin:</span>
            <span className="font-semibold text-green-600">{stats.points_this_month}</span>
          </div>
        </div>
      </div>

      {/* Environmental Impact */}
      <div className="bg-gradient-to-r from-emerald-50 to-teal-50 rounded-lg p-6 mb-8">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">🌱 Dampak Lingkungan</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-emerald-600">
              {stats.plastic_waste_diverted_kg.toFixed(3)} kg
            </div>
            <div className="text-sm text-gray-600">Sampah Plastik Dihindari</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-teal-600">
              {stats.co2_emissions_saved_kg.toFixed(1)} kg
            </div>
            <div className="text-sm text-gray-600">CO2 Dihindari</div>
          </div>
        </div>
        
        {/* Environmental Summary */}
        <div className="mt-4 p-4 bg-white rounded-lg">
          <div className="text-sm text-gray-700 space-y-2">
            <div>♻️ {stats.environmental_impact.bottles_equivalent}</div>
            <div>🌿 {stats.environmental_impact.trees_equivalent}</div>
          </div>
        </div>
      </div>

      {/* Achievement Tracking */}
      <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-lg p-6 mb-8">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">🏆 Achievement</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-amber-600">
              {stats.current_streak_days}
            </div>
            <div className="text-sm text-gray-600">Streak Hari Ini</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {stats.longest_streak_days}
            </div>
            <div className="text-sm text-gray-600">Streak Terpanjang</div>
          </div>
        </div>
      </div>

      {/* Last Activity */}
      {stats.last_scan_date && (
        <div className="bg-gray-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">⏰ Aktivitas Terakhir</h3>
          <div className="text-sm text-gray-600">
            <div>Scan terakhir: {new Date(stats.last_scan_date).toLocaleDateString('id-ID')}</div>
            {stats.last_reward_date && (
              <div>Reward terakhir: {new Date(stats.last_reward_date).toLocaleDateString('id-ID')}</div>
            )}
          </div>
        </div>
      )}

      {/* Refresh Button */}
      <div className="mt-6 text-center">
        <button
          onClick={fetchStatistics}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          🔄 Refresh Data
        </button>
      </div>
    </div>
  );
}
