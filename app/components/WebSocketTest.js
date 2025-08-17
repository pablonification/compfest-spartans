'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function WebSocketTest() {
  const { token } = useAuth();
  const [wsStatus, setWsStatus] = useState('disconnected');
  const [messages, setMessages] = useState([]);
  const [connectionInfo, setConnectionInfo] = useState(null);
  const wsRef = useRef(null);

  const connectWebSocket = () => {
    if (!token) {
      setWsStatus('no-token');
      return;
    }

    try {
      // Fix WebSocket URL to use localhost instead of container name
      const apiUrl = process.env.NEXT_PUBLIC_BROWSER_API_URL || 'http://localhost:8000';
      const wsUrl = apiUrl.replace('http://', 'ws://').replace('https://', 'wss://');
      const ws = new WebSocket(`${wsUrl}/ws/status`);
      
      console.log('Connecting to WebSocket:', wsUrl);
      setWsStatus('connecting');
      
      ws.onopen = () => {
        console.log('WebSocket connected successfully');
        setWsStatus('connected');
        setMessages(prev => [...prev, { type: 'system', text: 'Connected to WebSocket', timestamp: new Date().toISOString() }]);
      };
      
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          console.log('WebSocket message received:', msg);
          setMessages(prev => [...prev, { type: 'received', text: JSON.stringify(msg, null, 2), timestamp: new Date().toISOString() }]);
          
          if (msg.type === 'connection_status') {
            setConnectionInfo(msg);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
          setMessages(prev => [...prev, { type: 'error', text: `Parse error: ${error.message}`, timestamp: new Date().toISOString() }]);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsStatus('error');
        setMessages(prev => [...prev, { type: 'error', text: `WebSocket error: ${error}`, timestamp: new Date().toISOString() }]);
      };
      
      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setWsStatus('disconnected');
        setMessages(prev => [...prev, { type: 'system', text: `Disconnected: ${event.code} - ${event.reason}`, timestamp: new Date().toISOString() }]);
      };
      
      wsRef.current = ws;
      
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setWsStatus('error');
      setMessages(prev => [...prev, { type: 'error', text: `Connection failed: ${error.message}`, timestamp: new Date().toISOString() }]);
    }
  };

  const disconnectWebSocket = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  const sendPing = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const pingMessage = {
        type: 'ping',
        timestamp: new Date().toISOString()
      };
      wsRef.current.send(JSON.stringify(pingMessage));
      setMessages(prev => [...prev, { type: 'sent', text: JSON.stringify(pingMessage, null, 2), timestamp: new Date().toISOString() }]);
    }
  };

  const sendScanRequest = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const scanMessage = {
        type: 'scan_request',
        timestamp: new Date().toISOString()
      };
      wsRef.current.send(JSON.stringify(scanMessage));
      setMessages(prev => [...prev, { type: 'sent', text: JSON.stringify(scanMessage, null, 2), timestamp: new Date().toISOString() }]);
    }
  };

  const clearMessages = () => {
    setMessages([]);
  };

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected': return 'text-green-600';
      case 'connecting': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      case 'disconnected': return 'text-gray-600';
      case 'no-token': return 'text-orange-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">WebSocket Test</h3>
        <div className="flex items-center space-x-2">
          <span className={`text-sm font-medium ${getStatusColor(wsStatus)}`}>
            Status: {wsStatus}
          </span>
          {connectionInfo && (
            <span className="text-xs text-gray-500">
              ({connectionInfo.status})
            </span>
          )}
        </div>
      </div>

      <div className="flex space-x-2">
        <button
          onClick={connectWebSocket}
          disabled={wsStatus === 'connected' || wsStatus === 'connecting'}
          className="px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Connect
        </button>
        <button
          onClick={disconnectWebSocket}
          disabled={wsStatus !== 'connected'}
          className="px-3 py-2 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Disconnect
        </button>
        <button
          onClick={sendPing}
          disabled={wsStatus !== 'connected'}
          className="px-3 py-2 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send Ping
        </button>
        <button
          onClick={sendScanRequest}
          disabled={wsStatus !== 'connected'}
          className="px-3 py-2 bg-purple-600 text-white text-sm rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send Scan Request
        </button>
        <button
          onClick={clearMessages}
          className="px-3 py-2 bg-gray-600 text-white text-sm rounded-md hover:bg-gray-700"
        >
          Clear Messages
        </button>
      </div>

      {connectionInfo && (
        <div className="bg-blue-50 p-3 rounded-md">
          <h4 className="text-sm font-medium text-blue-900 mb-2">Connection Info</h4>
          <pre className="text-xs text-blue-800 overflow-x-auto">
            {JSON.stringify(connectionInfo, null, 2)}
          </pre>
        </div>
      )}

      <div className="space-y-2">
        <h4 className="text-sm font-medium text-gray-900">Messages</h4>
        <div className="max-h-64 overflow-y-auto space-y-2">
          {messages.length === 0 ? (
            <p className="text-sm text-gray-500">No messages yet</p>
          ) : (
            messages.map((msg, index) => (
              <div key={index} className={`p-2 rounded text-xs ${
                msg.type === 'sent' ? 'bg-blue-50 text-blue-800' :
                msg.type === 'received' ? 'bg-green-50 text-green-800' :
                msg.type === 'error' ? 'bg-red-50 text-red-800' :
                'bg-gray-50 text-gray-800'
              }`}>
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium capitalize">{msg.type}</span>
                  <span className="text-xs opacity-75">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                </div>
                <pre className="whitespace-pre-wrap break-words">{msg.text}</pre>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
