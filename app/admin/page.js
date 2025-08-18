'use client';

import { useEffect, useMemo, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useRouter } from 'next/navigation';

export default function AdminPage() {
  const { token, user } = useAuth();
  const router = useRouter();
  const [error, setError] = useState('');
  const [list, setList] = useState([]);
  const [status, setStatus] = useState('pending');
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const apiBase = process.env.NEXT_PUBLIC_BROWSER_API_URL || 'http://localhost:8000';

  useEffect(() => {
    if (!token) {
      router.push('/login');
      return;
    }
    fetchList();
  }, [token, status]);

  const fetchList = async () => {
    try {
      setLoading(true);
      const resp = await fetch(`${apiBase}/payout/admin/withdrawals?status=${encodeURIComponent(status)}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!resp.ok) {
        const t = await resp.json().catch(() => ({}));
        throw new Error(t.detail || `Failed: ${resp.status}`);
      }
      const data = await resp.json();
      setList(data || []);
    } catch (e) {
      setError(e.message || 'Failed to fetch');
    } finally {
      setLoading(false);
    }
  };

  const markComplete = async (id) => {
    try {
      const resp = await fetch(`${apiBase}/payout/admin/withdrawals/${id}/complete`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!resp.ok) throw new Error('Failed to complete');
      fetchList();
    } catch (e) {
      setError(e.message || 'Update failed');
    }
  };

  const rejectRefund = async (id) => {
    try {
      const resp = await fetch(`${apiBase}/payout/admin/withdrawals/${id}/reject`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ admin_note: 'Rejected by admin' }),
      });
      if (!resp.ok) throw new Error('Failed to reject');
      fetchList();
    } catch (e) {
      setError(e.message || 'Update failed');
    }
  };

  const exportCsv = async () => {
    try {
      setExporting(true);
      const resp = await fetch(`${apiBase}/payout/admin/withdrawals/export.csv${status?`?status=${encodeURIComponent(status)}`:''}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!resp.ok) throw new Error('Export failed');
      const blob = await resp.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'withdrawals_export.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      setError(e.message || 'Export failed');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-4">Admin Panel</h1>
        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 border border-red-200 rounded">{error}</div>
        )}

        {/* User Info moved to Navbar */}

        <div className="bg-white rounded border p-4 mb-6">
          <div className="flex items-center gap-3">
            <label>Status</label>
            <select className="border rounded p-2" value={status} onChange={e=>setStatus(e.target.value)}>
              <option value="pending">Pending</option>
              <option value="completed">Completed</option>
              <option value="rejected">Rejected</option>
              <option value="">All</option>
            </select>
          </div>
        </div>

        <div className="bg-white rounded border p-4">
          <h2 className="font-semibold mb-2">Pengajuan Pencairan</h2>
          <div className="mb-3">
            <button className="px-3 py-1 bg-indigo-600 text-white rounded" onClick={exportCsv} disabled={exporting}>{exporting? 'Mengunduh...' : 'Unduh CSV'}</button>
          </div>
          {loading ? (
            <div>Loading...</div>
          ) : list.length === 0 ? (
            <div className="text-sm text-gray-600">Tidak ada data</div>
          ) : (
            <div className="divide-y">
              {list.map(item => (
                <div key={item.id} className="py-3 flex items-center justify-between">
                  <div>
                    <div className="font-medium">{item.amount_points} poin — {item.method_type}</div>
                    <div className="text-xs text-gray-500">{new Date(item.created_at).toLocaleString('id-ID')}</div>
                    <div className="text-xs text-gray-600">
                      {item.method_type === 'bank' ? (
                        <>Bank {item.bank_code} • {item.bank_account_number} • {item.bank_account_name}</>
                      ) : (
                        <>{item.ewallet_provider} • {item.phone_number}</>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {item.status === 'pending' ? (
                      <>
                        <button className="px-3 py-1 bg-green-600 text-white rounded" onClick={()=>markComplete(item.id)}>Mark Selesai</button>
                        <button className="px-3 py-1 bg-red-600 text-white rounded" onClick={()=>rejectRefund(item.id)}>Tolak + Refund</button>
                      </>
                    ) : (
                      <div className={`text-sm font-semibold ${item.status==='completed'?'text-green-600':item.status==='rejected'?'text-red-600':'text-gray-600'}`}>{item.status}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white rounded border p-4 mt-6">
          <h2 className="font-semibold mb-2">Halaman Admin Lainnya</h2>
          <ul className="list-disc pl-6 text-sm text-gray-700 space-y-1">
            <li>Konfigurasi harga PET per kg dan koefisien (roadmap)</li>
            <li>Daftar pengguna dan total poin (roadmap)</li>
            <li>Export CSV riwayat pencairan (roadmap)</li>
          </ul>
        </div>
      </div>
    </div>
  );
}


