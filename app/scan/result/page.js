'use client';

export const dynamic = 'force-dynamic';

import { useEffect, useState, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '../../components/ProtectedRoute';
import MobileScanResult from '../../components/MobileScanResult';
import TopBar from '../../components/TopBar';

function ScanResultContent() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);

  useEffect(() => {
    console.log('📡 Checking localStorage for scan results...');
    
    // Check localStorage for scan results
    const interval = setInterval(() => {
      try {
        const processing = localStorage.getItem('smartbin_scan_processing');
        const raw = localStorage.getItem('smartbin_last_scan');
        
        console.log('📡 localStorage check:', { 
          processing, 
          hasData: !!raw,
          rawData: raw ? 'exists' : 'none',
          currentTime: new Date().toISOString()
        });
        
        if (processing === '0' && raw) {
          console.log('📡 Found completed scan data:', raw);
          const parsed = JSON.parse(raw);
          setData(parsed);
          setLoading(false);
          clearInterval(interval);
        }
      } catch (e) {
        console.error('LocalStorage error:', e);
      }
    }, 300);
    
    return () => clearInterval(interval);
  }, []);

  // If still loading after 10 seconds, show error
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (loading) {
        console.warn('⚠️ Result page timeout - no data received');
        setLoading(false);
      }
    }, 10000);
    
    return () => clearTimeout(timeout);
  }, [loading]);

  // Manual refresh function
  const handleManualRefresh = () => {
    try {
      const processing = localStorage.getItem('smartbin_scan_processing');
      const raw = localStorage.getItem('smartbin_last_scan');
      
      console.log('🔄 Manual refresh check:', { processing, hasData: !!raw });
      
      if (processing === '0' && raw) {
        const parsed = JSON.parse(raw);
        setData(parsed);
        setLoading(false);
      } else {
        console.log('🔄 No completed scan data found, refreshing page...');
        window.location.reload();
      }
    } catch (e) {
      console.error('Manual refresh error:', e);
      window.location.reload();
    }
  };

  return (
    <div className="px-4">
      {loading ? (
        <div className="mt-12 flex flex-col items-center justify-center text-center">
          <div className="w-16 h-16 rounded-full border-4 border-white/40 border-t-[var(--color-primary-600)] animate-spin"></div>
          <p className="mt-4 text-sm text-gray-600">Memproses hasil scan...</p>
          <p className="mt-2 text-xs text-gray-400">Checking for scan results...</p>
          <button
            onClick={handleManualRefresh}
            className="mt-4 px-4 py-2 bg-[var(--color-primary-600)] text-white rounded-[var(--radius-pill)] text-sm"
          >
            Refresh Manual
          </button>
        </div>
      ) : data ? (
        <>
          <MobileScanResult result={data} />

          {(() => {
            const invalid = data?.is_valid === false || data?.valid === false || (typeof data?.points_awarded === 'number' && data.points_awarded <= 0);
            return (
              <div className="mt-6 space-y-3">
                {invalid ? (
                  <button
                    onClick={() => {
                      try {
                        localStorage.removeItem('smartbin_last_scan');
                        localStorage.setItem('smartbin_scan_processing', '0');
                      } catch {}
                      router.push('/scan');
                    }}
                    className="w-full h-12 rounded-[var(--radius-pill)] bg-[var(--color-primary-700)] text-white font-medium active:opacity-80"
                  >
                    Ambil Ulang Foto
                  </button>
                ) : null}
                <button
                  onClick={() => router.push('/')}
                  className="w-full h-12 rounded-[var(--radius-pill)] bg-transparent text-[var(--color-primary-700)] font-medium active:opacity-80 border-2 border-[var(--color-primary-700)]"
                >
                  Selesai
                </button>
              </div>
            );
          })()}
        </>
      ) : (
        <div className="mt-12 flex flex-col items-center justify-center text-center">
          <div className="w-16 h-16 rounded-full border-4 border-red-200 border-t-red-500 animate-spin"></div>
          <p className="mt-4 text-sm text-gray-600">Tidak ada hasil scan</p>
          <p className="mt-2 text-xs text-gray-400">No scan results found</p>
          <button
            onClick={() => router.push('/scan')}
            className="mt-4 px-6 py-2 bg-[var(--color-primary-600)] text-white rounded-[var(--radius-pill)] text-sm"
          >
            Kembali ke Scan
          </button>
        </div>
      )}
    </div>
  );
}

export default function ScanResultPage() {
  return (
    <ProtectedRoute userOnly={true}>
      <div className="w-full min-h-screen bg-[var(--background)] text-[var(--foreground)] font-inter">
        <TopBar title="Duitin" backHref="/scan" />
        
        <Suspense fallback={
          <div className="px-4 mt-12 flex flex-col items-center justify-center text-center">
            <div className="w-16 h-16 rounded-full border-4 border-white/40 border-t-[var(--color-primary-600)] animate-spin"></div>
            <p className="mt-4 text-sm text-gray-600">Loading...</p>
          </div>
        }>
          <ScanResultContent />
        </Suspense>
      </div>
    </ProtectedRoute>
  );
}
