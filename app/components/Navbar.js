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
        <Link href="/scan" className="text-gray-800 font-semibold">Scan</Link>
        <Link href="/history" className="text-gray-600 hover:text-gray-800">History</Link>
        <Link href="/statistics" className="text-gray-600 hover:text-gray-800">Statistics</Link>
        <Link href="/education" className="text-gray-600 hover:text-gray-800">Education</Link>
        <Link href="/rag" className="ml-auto text-emerald-700 font-semibold hover:text-emerald-800">SmartBin AI Agent</Link>
        {token && user && (
          <button
            onClick={() => { logout(); router.push('/login'); }}
            className="text-sm text-gray-600 hover:text-gray-800"
          >
            Logout
          </button>
        )}
      </div>
    </div>
  );
}
