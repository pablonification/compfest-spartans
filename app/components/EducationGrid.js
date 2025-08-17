'use client';

import { useState, useEffect } from 'react';
import Image from 'next/image';

export default function EducationGrid() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchItems = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/education?limit=100');
      const data = await res.json();
      if (res.ok) {
        setItems(data.items || []);
      } else {
        setError(data.error || 'Failed to fetch');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  if (loading) {
    return <div className="p-8 text-center">Loading...</div>;
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 text-center">
        <p className="text-red-600">{error}</p>
        <button onClick={fetchItems} className="mt-2 px-4 py-2 bg-red-600 text-white rounded">Retry</button>
      </div>
    );
  }

  if (!items.length) {
    return <p className="text-center text-gray-500">Belum ada konten edukasi.</p>;
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      {items.map(item => (
        <div key={item.id} className="bg-white border rounded-lg overflow-hidden shadow-sm">
          {item.media_url && (
            <div className="relative w-full h-40">
              <Image src={item.media_url} fill style={{objectFit:'cover'}} alt={item.title} />
            </div>
          )}
          <div className="p-4">
            <h3 className="font-semibold text-gray-800 mb-2">{item.title}</h3>
            <p className="text-sm text-gray-600 line-clamp-3">{item.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
