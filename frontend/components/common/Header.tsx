'use client'

import { useState } from 'react'
import { useAuthStore } from '@/store/authStore'

export function Header() {
  const [showDropdown, setShowDropdown] = useState(false)
  const { user, logout } = useAuthStore()

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex justify-between items-center">
        {/* Search (placeholder) */}
        <div className="flex-1 max-w-md">
          <input
            type="search"
            placeholder="契約書を検索..."
            className="form-input w-full"
          />
        </div>

        {/* Right side */}
        <div className="flex items-center gap-4">
          {/* Notifications */}
          <button className="relative p-2 text-gray-400 hover:text-gray-600">
            <span className="text-xl">🔔</span>
            <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className="flex items-center gap-2 p-2 rounded-md hover:bg-gray-100"
            >
              <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-white font-medium">
                {user?.full_name?.[0] || 'U'}
              </div>
              <span className="text-sm font-medium text-gray-700">
                {user?.full_name || 'ユーザー'}
              </span>
              <span className="text-gray-400">▼</span>
            </button>

            {showDropdown && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-50">
                <div className="px-4 py-2 border-b border-gray-100">
                  <p className="text-sm font-medium text-gray-900">
                    {user?.full_name || 'ユーザー'}
                  </p>
                  <p className="text-xs text-gray-500">
                    {user?.email || 'user@example.com'}
                  </p>
                </div>
                <button
                  onClick={() => {
                    logout()
                    setShowDropdown(false)
                  }}
                  className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  ログアウト
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
