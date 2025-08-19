'use client';

import { useState, useEffect, useRef } from 'react';
import { FiBell, FiX, FiCheck, FiTrash2, FiWifi, FiWifiOff, FiRefreshCw } from 'react-icons/fi';
import { useAuth } from '../contexts/AuthContext';
import { useNotificationWebSocket } from '../hooks/useWebSocket';

export default function NotificationBell() {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const dropdownRef = useRef(null);
  const { user, token, getAuthHeaders } = useAuth();
  
  console.log('NotificationBell: Component rendered with:', { 
    hasUser: !!user, 
    userId: user?.id || user?._id, 
    hasToken: !!token 
  });
  
  // Ensure we have a valid user ID for WebSocket connection
  const userId = user?.id || user?._id;
  
  // WebSocket hook for real-time notifications
  const { 
    isConnected, 
    connectionStatus, 
    error: wsError, 
    notifications: wsNotifications 
  } = useNotificationWebSocket(userId);

  useEffect(() => {
    if (user && token) {
      console.log('NotificationBell: Fetching notifications for user:', user.id || user._id);
      fetchNotifications();
      fetchUnreadCount();
    }
  }, [user, token]);

  // Handle real-time notifications from WebSocket
  useEffect(() => {
    console.log('NotificationBell: WebSocket notifications updated:', wsNotifications.length);
    if (wsNotifications.length > 0) {
      // Add new WebSocket notifications to the list
      const newNotifications = wsNotifications.filter(wsNotif => 
        !notifications.some(existing => existing.id === wsNotif.id)
      );
      
      if (newNotifications.length > 0) {
        console.log('NotificationBell: Adding new notifications:', newNotifications);
        setNotifications(prev => [...newNotifications, ...prev]);
        setUnreadCount(prev => prev + newNotifications.length);
      }
    }
  }, [wsNotifications, notifications]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchNotifications = async () => {
    if (!token) {
      console.warn('NotificationBell: No token available for fetching notifications');
      return;
    }
    
    console.log('NotificationBell: Fetching notifications...');
    try {
      const response = await fetch('/api/notifications', {
        headers: getAuthHeaders()
      });
      
      console.log('NotificationBell: Notifications response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('NotificationBell: Notifications data:', data);
        setNotifications(data.notifications || []);
      } else {
        console.error('NotificationBell: Failed to fetch notifications:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('NotificationBell: Error fetching notifications:', error);
    }
  };

  const fetchUnreadCount = async () => {
    if (!token) {
      console.warn('NotificationBell: No token available for fetching unread count');
      return;
    }
    
    console.log('NotificationBell: Fetching unread count...');
    try {
      const response = await fetch('/api/notifications/unread-count', {
        headers: getAuthHeaders()
      });
      
      console.log('NotificationBell: Unread count response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('NotificationBell: Unread count data:', data);
        setUnreadCount(data.unread_count || 0);
      } else {
        console.error('NotificationBell: Failed to fetch unread count:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('NotificationBell: Error fetching unread count:', error);
    }
  };

  const markAsRead = async (notificationId) => {
    if (!token) {
      console.warn('No token available for marking notification as read');
      return;
    }
    
    try {
      const response = await fetch(`/api/notifications/${notificationId}/read`, {
        method: 'PATCH',
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        setNotifications(prev => 
          prev.map(notif => 
            notif.id === notificationId 
              ? { ...notif, is_read: true }
              : notif
          )
        );
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const deleteNotification = async (notificationId) => {
    if (!token) {
      console.warn('No token available for deleting notification');
      return;
    }
    
    try {
      const response = await fetch(`/api/notifications/${notificationId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        const notification = notifications.find(n => n.id === notificationId);
        if (notification && !notification.is_read) {
          setUnreadCount(prev => Math.max(0, prev - 1));
        }
        setNotifications(prev => prev.filter(n => n.id !== notificationId));
      }
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  };

  const markAllAsRead = async () => {
    if (!token) {
      console.warn('No token available for marking all notifications as read');
      return;
    }
    
    try {
      const response = await fetch('/api/notifications/mark-all-read', {
        method: 'PATCH',
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
        setUnreadCount(0);
      }
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'bin_status':
        return '🗑️';
      case 'achievement':
        return '🏆';
      case 'reward':
        return '🎁';
      case 'system':
        return 'ℹ️';
      default:
        return '📢';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 3:
        return 'border-l-red-500';
      case 2:
        return 'border-l-yellow-500';
      case 1:
        return 'border-l-green-500';
      default:
        return 'border-l-gray-500';
    }
  };

  const getConnectionStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected':
        return <FiWifi className="w-4 h-4 text-green-500" />;
      case 'connecting':
        return <FiRefreshCw className="w-4 h-4 text-yellow-500 animate-spin" />;
      case 'reconnecting':
        return <FiRefreshCw className="w-4 h-4 text-yellow-500 animate-spin" />;
      case 'error':
        return <FiWifiOff className="w-4 h-4 text-red-500" />;
      default:
        return <FiWifiOff className="w-4 h-4 text-gray-400" />;
    }
  };

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Terhubung';
      case 'connecting':
        return 'Menghubungkan...';
      case 'reconnecting':
        return 'Mencoba menghubungkan...';
      case 'error':
        return 'Koneksi error';
      default:
        return 'Tidak terhubung';
    }
  };

  if (!user) return null;

  // Ensure we have a valid user ID for WebSocket connection
  if (!userId) {
    console.warn('NotificationBell: No valid user ID found');
    return null;
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 transition-colors"
        aria-label="Notifications"
      >
        <FiBell className="w-6 h-6" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
        
        {/* Connection status indicator */}
        <div className="absolute -bottom-1 -right-1">
          {getConnectionStatusIcon()}
        </div>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50 max-h-96 overflow-hidden">
          <div className="p-4 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Notifikasi</h3>
              <div className="flex items-center space-x-2">
                {/* Connection status */}
                <div className="flex items-center space-x-1 text-xs">
                  {getConnectionStatusIcon()}
                  <span className="text-gray-600">{getConnectionStatusText()}</span>
                </div>
                
                {unreadCount > 0 && (
                  <button
                    onClick={markAllAsRead}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    Tandai semua sudah dibaca
                  </button>
                )}
              </div>
            </div>
            
            {/* WebSocket error display */}
            {wsError && (
              <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                <div className="font-medium">Koneksi real-time error:</div>
                <div className="mt-1">{wsError}</div>
                <div className="mt-2 text-xs">
                  Pastikan backend berjalan dan WebSocket manager aktif.
                </div>
              </div>
            )}
            
            {/* Connection status info */}
            {!wsError && connectionStatus !== 'connected' && (
              <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-700">
                <div className="font-medium">Status Koneksi:</div>
                <div className="mt-1">{getConnectionStatusText()}</div>
                <div className="mt-2 text-xs">
                  Mencoba menghubungkan ke layanan notifikasi...
                </div>
              </div>
            )}
          </div>

          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                {isConnected ? 'Tidak ada notifikasi' : 'Menghubungkan ke layanan notifikasi...'}
              </div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 border-l-4 ${getPriorityColor(notification.priority)} ${
                    !notification.is_read ? 'bg-blue-50' : 'bg-white'
                  } hover:bg-gray-50 transition-colors`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3 flex-1">
                      <span className="text-xl">{getNotificationIcon(notification.notification_type)}</span>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-medium text-gray-900 mb-1">
                          {notification.title}
                        </h4>
                        <p className="text-sm text-gray-600 mb-2">
                          {notification.message}
                        </p>
                        <div className="flex items-center justify-between text-xs text-gray-500">
                          <span>
                            {new Date(notification.created_at).toLocaleDateString('id-ID', {
                              day: 'numeric',
                              month: 'short',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </span>
                          {!notification.is_read && (
                            <span className="bg-blue-500 text-white px-2 py-1 rounded-full text-xs">
                              Baru
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-1 ml-2">
                      {!notification.is_read && (
                        <button
                          onClick={() => markAsRead(notification.id)}
                          className="p-1 text-gray-400 hover:text-green-600 transition-colors"
                          title="Tandai sudah dibaca"
                        >
                          <FiCheck className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => deleteNotification(notification.id)}
                        className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                        title="Hapus notifikasi"
                      >
                        <FiTrash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
          
          {/* Footer with refresh button */}
          <div className="p-3 border-t border-gray-200 bg-gray-50">
            <button
              onClick={() => {
                fetchNotifications();
                fetchUnreadCount();
              }}
              disabled={isLoading}
              className="w-full text-sm text-gray-600 hover:text-gray-800 flex items-center justify-center space-x-2"
            >
              <FiRefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              <span>{isLoading ? 'Memuat...' : 'Refresh'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
