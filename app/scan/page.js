'use client';

export const dynamic = 'force-dynamic';

import { useEffect, useState, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '../components/ProtectedRoute';
import NotificationBell from '../components/NotificationBell';

export default function ScanPage() {
  const { user, token, logout } = useAuth();
  const router = useRouter();
  const [status, setStatus] = useState('Ready');
  const [result, setResult] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [cameraStream, setCameraStream] = useState(null);
  const [capturedImage, setCapturedImage] = useState(null);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!token) return;
    
    const ws = new WebSocket('ws://localhost:8000/ws/status');
    
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === 'scan_result') {
        setResult(msg.data);
        setStatus('Completed');
        setIsScanning(false);
      }
    };
    
    ws.onerror = () => setStatus('WebSocket error');
    ws.onclose = () => setStatus('WebSocket disconnected');
    
    return () => ws.close();
  }, [token]);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          facingMode: 'environment', // Use back camera on mobile
          width: { ideal: 1280 },
          height: { ideal: 720 }
        } 
      });
      
      setCameraStream(stream);
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setStatus('Camera ready');
    } catch (error) {
      console.error('Camera error:', error);
      setStatus('Camera access denied');
    }
  };

  const stopCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach(track => track.stop());
      setCameraStream(null);
      setCapturedImage(null);
      setStatus('Camera stopped');
    }
  };

  const captureImage = () => {
    if (!videoRef.current || !canvasRef.current) return;
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    
    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw video frame to canvas
    context.drawImage(video, 0, 0);
    
    // Convert to blob
    canvas.toBlob((blob) => {
      if (blob) {
        setCapturedImage(blob);
        setStatus('Image captured');
      }
    }, 'image/jpeg', 0.8);
  };

  const handleScan = async () => {
    if (!capturedImage || !token) return;
    
    setIsScanning(true);
    setStatus('Processing...');
    
    try {
      const formData = new FormData();
      formData.append('image', capturedImage, 'bottle.jpg');
      
      const response = await fetch('http://localhost:8000/scan', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setResult(data);
      setStatus('Scan completed');
      
    } catch (error) {
      console.error('Scan error:', error);
      setStatus('Scan failed');
    } finally {
      setIsScanning(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <div className="flex items-center space-x-3">
                <div className="h-8 w-8 bg-green-600 rounded-full flex items-center justify-center">
                  <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                </div>
                <h1 className="text-xl font-semibold text-gray-900">SmartBin</h1>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="text-sm text-gray-600">
                  <span className="font-medium">{user?.name || user?.email || 'User'}</span>
                  <span className="ml-2">• {user?.points || 0} points</span>
                </div>
                <NotificationBell />
                <button
                  onClick={() => router.push('/history')}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  History
                </button>
                <button
                  onClick={() => router.push('/statistics')}
                  className="text-sm text-green-600 hover:text-green-800"
                >
                  Statistics
                </button>
                <button
                  onClick={() => router.push('/statistics#leaderboard')}
                  className="text-sm text-purple-600 hover:text-purple-800"
                >
                  Leaderboard
                </button>
                <button
                  onClick={handleLogout}
                  className="text-sm text-gray-600 hover:text-gray-800"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Camera Section */}
            <div className="space-y-4">
              <h2 className="text-lg font-medium text-gray-900">Scan Bottle</h2>
              
              {!cameraStream ? (
                <button
                  onClick={startCamera}
                  className="w-full py-3 px-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-gray-400 transition-colors"
                >
                  <div className="text-center">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    <p className="mt-2 text-sm text-gray-600">Click to start camera</p>
                  </div>
                </button>
              ) : (
                <div className="space-y-4">
                  <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    className="w-full rounded-lg border border-gray-300"
                  />
                  
                  <div className="flex space-x-3">
                    <button
                      onClick={captureImage}
                      className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
                    >
                      Capture
                    </button>
                    <button
                      onClick={stopCamera}
                      className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 transition-colors"
                    >
                      Stop Camera
                    </button>
                  </div>
                  
                  {capturedImage && (
                    <div className="space-y-3">
                      <img
                        src={URL.createObjectURL(capturedImage)}
                        alt="Captured bottle"
                        className="w-full rounded-lg border border-gray-300"
                      />
                      <button
                        onClick={handleScan}
                        disabled={isScanning}
                        className="w-full bg-green-600 text-white py-3 px-4 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        {isScanning ? 'Scanning...' : 'Scan Bottle'}
                      </button>
                    </div>
                  )}
                </div>
              )}
              
              <div className="text-sm text-gray-600">
                Status: <span className="font-medium">{status}</span>
              </div>
            </div>

            {/* Results Section */}
            <div className="space-y-4">
              <h2 className="text-lg font-medium text-gray-900">Scan Results</h2>
              
              {result ? (
                <div className="bg-white p-6 rounded-lg border border-gray-200 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-medium text-gray-900">
                      {result.brand || 'Unknown Brand'}
                    </h3>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      result.valid ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {result.valid ? 'Valid' : 'Invalid'}
                    </span>
                  </div>
                  
                  {result.valid && (
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Points Awarded:</span>
                        <p className="font-medium text-green-600">{result.points_awarded}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Total Points:</span>
                        <p className="font-medium">{result.total_points}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Volume:</span>
                        <p className="font-medium">{result.volume_ml?.toFixed(1)} ml</p>
                      </div>
                      <div>
                        <span className="text-gray-500">Confidence:</span>
                        <p className="font-medium">{(result.confidence * 100).toFixed(1)}%</p>
                      </div>
                    </div>
                  )}
                  
                  {result.reason && (
                    <div>
                      <span className="text-gray-500 text-sm">Reason:</span>
                      <p className="text-sm">{result.reason}</p>
                    </div>
                  )}
                  
                  {result.debug_url && (
                    <div>
                      <span className="text-gray-500 text-sm">Debug Image:</span>
                      <img
                        src={`http://localhost:8000${result.debug_url}`}
                        alt="Debug preview"
                        className="mt-2 w-full rounded border"
                      />
                    </div>
                  )}
                </div>
              ) : (
                <div className="bg-white p-6 rounded-lg border border-gray-200 text-center text-gray-500">
                  No scan results yet. Capture an image and scan to see results here.
                </div>
              )}
            </div>
          </div>
          
          {/* Hidden canvas for image capture */}
          <canvas ref={canvasRef} className="hidden" />
        </div>
      </div>
    </ProtectedRoute>
  );
}
