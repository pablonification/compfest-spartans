'use client';

import { useEffect, useState } from 'react';

const WS_PATH = `${process.env.NEXT_PUBLIC_API_URL.replace('http', 'ws')}/ws/status`;

export default function ScanPage() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('Idle');
  const [result, setResult] = useState(null);

  useEffect(() => {
    const ws = new WebSocket(WS_PATH);
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === 'scan_result') {
        setResult(msg.data);
        setStatus('Completed');
      }
    };
    ws.onerror = () => setStatus('WebSocket error');
    return () => ws.close();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;
    setStatus('Uploading');
    const formData = new FormData();
    formData.append('image', file);

    const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/scan`, {
      method: 'POST',
      headers: {
        'X-User-Email': 'tester@example.com',
      },
      body: formData,
    });

    if (!resp.ok) {
      setStatus('Error');
      return;
    }

    const data = await resp.json();
    setResult(data);
    setStatus('Processing (waiting for IoT)');
  };

  return (
    <div className="p-8 space-y-6">
      <h1 className="text-2xl font-bold">SmartBin Scan Test</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="border p-2"
        />
        <button
          type="submit"
          className="bg-green-600 text-white px-4 py-2 rounded disabled:opacity-50"
          disabled={!file}
        >
          Upload & Scan
        </button>
      </form>

      <p>Status: {status}</p>

      {result && (
        <pre className="bg-gray-100 p-4 rounded overflow-x-auto text-sm">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
