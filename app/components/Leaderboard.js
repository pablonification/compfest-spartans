'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function Leaderboard() {
  const { user } = useAuth();
  const [rankings, setRankings] = useState([]);
  const [userRank, setUserRank] = useState(null);
  const [totalParticipants, setTotalParticipants] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (user) {
      fetchLeaderboard();
    }
  }, [user]);

  const fetchLeaderboard = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/statistics/leaderboard', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch leaderboard');
      }

      const data = await response.json();
      setRankings(data.rankings || []);
      setUserRank(data.user_rank);
      setTotalParticipants(data.total_participants);
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
          onClick={fetchLeaderboard}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!rankings.length) {
    return (
      <div className="bg-gray-50 rounded-lg p-6 text-center">
        <p className="text-gray-600">Belum ada data leaderboard</p>
        <p className="text-sm text-gray-500 mt-2">Mulai scan botol untuk muncul di leaderboard!</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-gray-800">🏆 Leaderboard</h3>
        <div className="text-sm text-gray-600">
          Total: {totalParticipants} peserta
        </div>
      </div>

      {/* User's Current Rank */}
      {userRank && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 mb-6 border border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm text-blue-600 font-medium">Posisi Kamu:</span>
              <span className="text-2xl font-bold text-blue-700 ml-2">#{userRank}</span>
            </div>
            <div className="text-right">
              <div className="text-sm text-blue-600">Total Botol</div>
              <div className="text-lg font-semibold text-blue-700">
                {rankings.find(r => r.rank === userRank)?.total_bottles || 0}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Top Rankings */}
      <div className="space-y-3">
        {rankings.map((rank, index) => (
          <div 
            key={rank.user_id}
            className={`flex items-center justify-between p-4 rounded-lg border ${
              index === 0 ? 'bg-gradient-to-r from-yellow-50 to-amber-50 border-yellow-200' :
              index === 1 ? 'bg-gradient-to-r from-gray-50 to-slate-50 border-gray-200' :
              index === 2 ? 'bg-gradient-to-r from-orange-50 to-red-50 border-orange-200' :
              'bg-gray-50 border-gray-100'
            }`}
          >
            {/* Rank & Name */}
            <div className="flex items-center space-x-4">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg ${
                index === 0 ? 'bg-yellow-400 text-white' :
                index === 1 ? 'bg-gray-400 text-white' :
                index === 2 ? 'bg-orange-400 text-white' :
                'bg-gray-300 text-gray-700'
              }`}>
                {rank.rank}
              </div>
              <div>
                <div className="font-semibold text-gray-900">
                  {rank.name || `User ${rank.user_id.slice(-4)}`}
                </div>
                <div className="text-sm text-gray-500">
                  {rank.total_scans || 0} scan sessions
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className="text-right">
              <div className="text-lg font-bold text-gray-900">
                {rank.total_bottles} botol
              </div>
              <div className="text-sm text-gray-600">
                {rank.total_points} poin
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Refresh Button */}
      <div className="mt-6 text-center">
        <button
          onClick={fetchLeaderboard}
          className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          🔄 Refresh Leaderboard
        </button>
      </div>
    </div>
  );
}
