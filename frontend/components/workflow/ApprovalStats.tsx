'use client'

import { useEffect, useState } from 'react'

interface ApprovalStatsData {
  pending_count: number
  approved_this_month: number
  rejected_this_month: number
  avg_approval_time_hours: number
  oldest_pending_days: number | null
  oldest_pending_contract: string | null
}

export function ApprovalStats() {
  const [stats, setStats] = useState<ApprovalStatsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/approvals/stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch approval stats')
      }

      const data = await response.json()
      setStats(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="bg-gray-200 h-32 rounded-lg"></div>
          </div>
        ))}
      </div>
    )
  }

  if (error || !stats) {
    return (
      <div className="bg-red-50 text-red-600 p-4 rounded-lg">
        統計情報の読み込みに失敗しました
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Pending Count */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-yellow-800">承認待ち</h3>
          <svg className="w-8 h-8 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p className="text-3xl font-bold text-yellow-900">{stats.pending_count}</p>
        {stats.oldest_pending_days !== null && stats.oldest_pending_days > 3 && (
          <p className="text-xs text-yellow-700 mt-2">
            最古: {stats.oldest_pending_days}日前
          </p>
        )}
      </div>

      {/* Approved This Month */}
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-green-800">今月承認</h3>
          <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p className="text-3xl font-bold text-green-900">{stats.approved_this_month}</p>
        <p className="text-xs text-green-700 mt-2">今月の承認件数</p>
      </div>

      {/* Rejected This Month */}
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-red-800">今月却下</h3>
          <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p className="text-3xl font-bold text-red-900">{stats.rejected_this_month}</p>
        <p className="text-xs text-red-700 mt-2">今月の却下件数</p>
      </div>

      {/* Average Approval Time */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-blue-800">平均承認時間</h3>
          <svg className="w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <p className="text-3xl font-bold text-blue-900">
          {stats.avg_approval_time_hours.toFixed(1)}
        </p>
        <p className="text-xs text-blue-700 mt-2">時間</p>
      </div>
    </div>
  )
}
