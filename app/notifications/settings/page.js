'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { FiBell, FiMail, FiSmartphone, FiClock, FiSave, FiCheck } from 'react-icons/fi';

export default function NotificationSettings() {
  const { user, token, getAuthHeaders } = useAuth();
  const [settings, setSettings] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (user && token) {
      fetchSettings();
    }
  }, [user, token]);

  const fetchSettings = async () => {
    try {
      const response = await fetch('/api/notifications/settings', {
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      }
    } catch (error) {
      console.error('Failed to fetch notification settings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const updateSettings = async (updates) => {
    try {
      setIsSaving(true);
      const response = await fetch('/api/notifications/settings', {
        method: 'PATCH',
        headers: getAuthHeaders(),
        body: JSON.stringify(updates)
      });
      
      if (response.ok) {
        const updatedSettings = await response.json();
        setSettings(updatedSettings);
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3000);
      }
    } catch (error) {
      console.error('Failed to update notification settings:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleToggle = (key) => {
    if (!settings) return;
    
    const updates = { [key]: !settings[key] };
    updateSettings(updates);
  };

  const handleTimeChange = (key, value) => {
    if (!settings) return;
    
    const updates = { [key]: parseInt(value) };
    updateSettings(updates);
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Akses Ditolak</h1>
          <p className="text-gray-600">Silakan login untuk mengakses pengaturan notifikasi.</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Memuat pengaturan...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              <FiBell className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Pengaturan Notifikasi</h1>
                <p className="text-gray-600">Kelola preferensi notifikasi Anda</p>
              </div>
            </div>
          </div>

          {/* Settings Form */}
          <div className="px-6 py-6">
            {saveSuccess && (
              <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-2">
                <FiCheck className="w-5 h-5 text-green-600" />
                <span className="text-green-800">Pengaturan berhasil disimpan!</span>
              </div>
            )}

            {/* Notification Types */}
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Jenis Notifikasi</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <FiMail className="w-5 h-5 text-blue-600" />
                      <div>
                        <p className="font-medium text-gray-900">Email</p>
                        <p className="text-sm text-gray-500">Notifikasi via email</p>
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={settings?.email_notifications || false}
                        onChange={() => handleToggle('email_notifications')}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <FiSmartphone className="w-5 h-5 text-green-600" />
                      <div>
                        <p className="font-medium text-gray-900">Push Notifications</p>
                        <p className="text-sm text-gray-500">Notifikasi di aplikasi</p>
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={settings?.push_notifications || false}
                        onChange={() => handleToggle('push_notifications')}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>
              </div>

              {/* Notification Categories */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Kategori Notifikasi</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">🗑️</span>
                      <div>
                        <p className="font-medium text-gray-900">Status Tong Sampah</p>
                        <p className="text-sm text-gray-500">Update status dan maintenance</p>
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={settings?.bin_status_notifications || false}
                        onChange={() => handleToggle('bin_status_notifications')}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">🏆</span>
                      <div>
                        <p className="font-medium text-gray-900">Pencapaian</p>
                        <p className="text-sm text-gray-500">Milestone dan achievements</p>
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={settings?.achievement_notifications || false}
                        onChange={() => handleToggle('achievement_notifications')}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">🎁</span>
                      <div>
                        <p className="font-medium text-gray-900">Reward</p>
                        <p className="text-sm text-gray-500">Poin dan hadiah</p>
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={settings?.reward_notifications || false}
                        onChange={() => handleToggle('reward_notifications')}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>

                  <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">ℹ️</span>
                      <div>
                        <p className="font-medium text-gray-900">Sistem</p>
                        <p className="text-sm text-gray-500">Update aplikasi dan maintenance</p>
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        className="sr-only peer"
                        checked={settings?.system_notifications || false}
                        onChange={() => handleToggle('system_notifications')}
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>
              </div>

              {/* Quiet Hours */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Jam Tenang</h3>
                <p className="text-sm text-gray-600 mb-4">Atur waktu di mana notifikasi tidak akan dikirim</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center space-x-3">
                    <FiClock className="w-5 h-5 text-gray-400" />
                    <div className="flex-1">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Mulai
                      </label>
                      <select
                        value={settings?.quiet_hours_start || 22}
                        onChange={(e) => handleTimeChange('quiet_hours_start', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        {Array.from({ length: 24 }, (_, i) => (
                          <option key={i} value={i}>
                            {i.toString().padStart(2, '0')}:00
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <FiClock className="w-5 h-5 text-gray-400" />
                    <div className="flex-1">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Selesai
                      </label>
                      <select
                        value={settings?.quiet_hours_end || 7}
                        onChange={(e) => handleTimeChange('quiet_hours_end', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        {Array.from({ length: 24 }, (_, i) => (
                          <option key={i} value={i}>
                            {i.toString().padStart(2, '0')}:00
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Notifikasi tidak akan dikirim antara {settings?.quiet_hours_start || 22}:00 - {settings?.quiet_hours_end || 7}:00
                </p>
              </div>
            </div>

            {/* Save Button */}
            <div className="mt-8 pt-6 border-t border-gray-200">
              <button
                onClick={() => setSaveSuccess(true)}
                disabled={isSaving}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSaving ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Menyimpan...
                  </>
                ) : (
                  <>
                    <FiSave className="w-4 h-4 mr-2" />
                    Simpan Pengaturan
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
