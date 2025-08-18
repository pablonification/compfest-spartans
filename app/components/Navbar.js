"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "../contexts/AuthContext";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, token, logout } = useAuth();
  
  if (pathname === "/login") return null;
  
  return (
    <div className="w-full bg-white/90 border-b sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-5">
        {/* Left nav */}
        <Link href="/scan" className="text-gray-800 font-semibold">Scan</Link>
        <Link href="/history" className="text-gray-600 hover:text-gray-800">History</Link>
        <Link href="/statistics" className="text-gray-600 hover:text-gray-800">Statistics</Link>
        <Link href="/education" className="text-gray-600 hover:text-gray-800">Education</Link>
        <Link href="/payout" className="text-gray-600 hover:text-gray-800">Payout</Link>
        <Link href="/admin" className="text-gray-600 hover:text-gray-800">Admin</Link>
        <Link href="/rag" className="text-emerald-700 font-semibold hover:text-emerald-800">SmartBin AI Agent</Link>

        {/* Spacer */}
        <div className="ml-auto" />

        {/* User info + logout */}
        {token && user && (
          <div className="flex items-center gap-4">
            <div className="text-sm text-gray-700">
              <span className="font-medium">{user.name || user.email}</span>
              <span className="ml-2">• {(typeof user.points === 'number' && user.points >= 0) ? user.points : 0} points</span>
            </div>
            <button
              onClick={() => { logout(); router.push('/login'); }}
              className="text-sm text-gray-600 hover:text-gray-800"
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
