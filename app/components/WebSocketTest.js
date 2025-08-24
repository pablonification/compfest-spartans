'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useWebSocket } from '../hooks/useWebSocket';

export default function WebSocketTest() {
  const { user, token } = useAuth();
  const [testMessage, setTestMessage] = useState('');
  const [receivedMessages, setReceivedMessages] = useState([]);
  
  const userId = user?.id || user?._id;
  const { 
    isConnected, 
    connectionStatus, 
    error, 
    lastMessage, 
    sendMessage 
  } = useWebSocket(userId);

  useEffect(() => {
    if (lastMessage) {
      setReceivedMessages(prev => [lastMessage, ...prev.slice(0, 9)]);
    }
  }, [lastMessage]);

  const handleSendTest = () => {
    if (testMessage.trim() && sendMessage) {
      sendMessage({ type: 'test', message: testMessage, timestamp: new Date().toISOString() });
      setTestMessage('');
    }
  };

  const handleCreateTestNotification = async () => {
    try {
      const response = await fetch('/api/notifications/test-create-sample', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ type: 'system', count: 1 })
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`Test notification created: ${result.message}`);
      } else {
        alert('Failed to create test notification');
      }
    } catch (error) {
      console.error('Error creating test notification:', error);
      alert('Error creating test notification');
    }
  };

  if (!user) return null;

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 space-y-4">
      <h3 className="text-lg font-medium text-gray-900">WebSocket Test</h3>
      
      {/* Connection Status */}
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${
            isConnected ? 'bg-green-500' : 'bg-red-500'
          }`}></div>
          <span className="text-sm font-medium">
            Status: {connectionStatus}
          </span>
        </div>
        
        {error && (
          <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
            Error: {error}
          </div>
        )}
      </div>

      {/* Test Message Input */}
      <div className="space-y-2">
        <input
          type="text"
          value={testMessage}
          onChange={(e) => setTestMessage(e.target.value)}
          placeholder="Enter test message..."
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={handleSendTest}
          disabled={!isConnected}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send Test Message
        </button>
      </div>

      {/* Test Notification Button */}
      <div>
        <button
          onClick={handleCreateTestNotification}
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
        >
          Create Test Notification
        </button>
      </div>

      {/* Received Messages */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-gray-700">Received Messages:</h4>
        <div className="max-h-40 overflow-y-auto space-y-1">
          {receivedMessages.length === 0 ? (
            <p className="text-sm text-gray-500">No messages received yet</p>
          ) : (
            receivedMessages.map((msg, index) => (
              <div key={index} className="text-xs bg-gray-50 p-2 rounded">
                <div className="font-medium">{msg.type}</div>
                <div className="text-gray-600">{JSON.stringify(msg, null, 2)}</div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Debug Info */}
      <details className="text-xs text-gray-500">
        <summary className="cursor-pointer hover:text-gray-700">Debug Info</summary>
        <div className="mt-2 space-y-1">
          <div>User ID: {userId}</div>
          <div>Has Token: {!!token}</div>
          <div>WebSocket Hook: {typeof useWebSocket}</div>
          <div>Connection Status: {connectionStatus}</div>
          <div>Is Connected: {isConnected.toString()}</div>
        </div>
      </details>
    </div>
  );
}
