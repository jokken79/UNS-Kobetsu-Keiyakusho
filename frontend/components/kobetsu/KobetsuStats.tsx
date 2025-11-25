'use client'

import type { KobetsuStats as StatsType } from '@/types'

interface KobetsuStatsProps {
  stats?: StatsType
  isLoading?: boolean
}

export function KobetsuStats({ stats, isLoading }: KobetsuStatsProps) {
  const statCards = [
    {
      label: '総契約数',
      value: stats?.total_contracts ?? 0,
      icon: '📋',
      color: 'bg-blue-50 text-blue-600',
    },
    {
      label: '有効な契約',
      value: stats?.active_contracts ?? 0,
      icon: '✅',
      color: 'bg-green-50 text-green-600',
    },
    {
      label: '期限間近',
      value: stats?.expiring_soon ?? 0,
      icon: '⚠️',
      color: 'bg-amber-50 text-amber-600',
      highlight: (stats?.expiring_soon ?? 0) > 0,
    },
    {
      label: '下書き',
      value: stats?.draft_contracts ?? 0,
      icon: '📝',
      color: 'bg-gray-50 text-gray-600',
    },
    {
      label: '期限切れ',
      value: stats?.expired_contracts ?? 0,
      icon: '❌',
      color: 'bg-red-50 text-red-600',
    },
    {
      label: '総派遣労働者数',
      value: stats?.total_workers ?? 0,
      icon: '👥',
      color: 'bg-purple-50 text-purple-600',
    },
  ]

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="stats-card animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-16 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-20"></div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {statCards.map((stat) => (
        <div
          key={stat.label}
          className={`stats-card ${stat.highlight ? 'ring-2 ring-amber-400' : ''}`}
        >
          <div className="flex items-center gap-2 mb-2">
            <span className={`p-2 rounded-lg ${stat.color}`}>
              {stat.icon}
            </span>
          </div>
          <p className="stats-value">{stat.value.toLocaleString()}</p>
          <p className="stats-label">{stat.label}</p>
        </div>
      ))}
    </div>
  )
}
