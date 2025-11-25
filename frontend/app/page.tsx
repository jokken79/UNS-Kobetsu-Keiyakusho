'use client'

import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'
import { kobetsuApi } from '@/lib/api'
import { KobetsuStats } from '@/components/kobetsu/KobetsuStats'
import { KobetsuTable } from '@/components/kobetsu/KobetsuTable'

export default function HomePage() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['kobetsu-stats'],
    queryFn: () => kobetsuApi.getStats(),
  })

  const { data: recentContracts, isLoading: contractsLoading } = useQuery({
    queryKey: ['kobetsu-recent'],
    queryFn: () => kobetsuApi.getList({ limit: 5, sort_by: 'created_at', sort_order: 'desc' }),
  })

  const { data: expiringContracts } = useQuery({
    queryKey: ['kobetsu-expiring'],
    queryFn: () => kobetsuApi.getExpiring(30),
  })

  // 抵触日アラート
  const { data: conflictAlerts } = useQuery({
    queryKey: ['conflict-alerts'],
    queryFn: () => kobetsuApi.getConflictDateAlerts(90),
  })

  // 契約期限アラート（詳細）
  const { data: expiringAlerts } = useQuery({
    queryKey: ['expiring-alerts'],
    queryFn: () => kobetsuApi.getExpiringContractsAlerts(30),
  })

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            ダッシュボード
          </h1>
          <p className="text-gray-500 mt-1">
            個別契約書の概要と最新情報
          </p>
        </div>
        <Link href="/kobetsu/create" className="btn-primary">
          + 新規契約書作成
        </Link>
      </div>

      {/* Statistics Cards */}
      <KobetsuStats stats={stats} isLoading={statsLoading} />

      {/* Alert Banners */}
      {(conflictAlerts?.length > 0 || expiringAlerts?.length > 0) && (
        <div className="space-y-3">
          {/* 抵触日警告 */}
          {conflictAlerts?.filter((a: any) => a.days_remaining <= 30).map((alert: any) => (
            <div
              key={alert.factory_id}
              className="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-md"
            >
              <div className="flex items-center">
                <span className="text-2xl mr-3">⚠️</span>
                <div className="flex-1">
                  <h4 className="text-red-800 font-semibold">
                    抵触日警告: {alert.company_name} {alert.plant_name}
                  </h4>
                  <p className="text-red-700 text-sm">
                    抵触日まで残り <strong>{alert.days_remaining}日</strong>
                    （{alert.conflict_date}）- {alert.total_employees}名が影響を受けます
                  </p>
                </div>
                <Link
                  href={`/kobetsu?factory_id=${alert.factory_id}`}
                  className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                >
                  確認
                </Link>
              </div>
            </div>
          ))}

          {/* 期限7日以内の契約 */}
          {expiringAlerts?.filter((a: any) => a.days_remaining <= 7).map((alert: any) => (
            <div
              key={alert.id}
              className="bg-orange-50 border-l-4 border-orange-500 p-4 rounded-r-md"
            >
              <div className="flex items-center">
                <span className="text-2xl mr-3">📅</span>
                <div className="flex-1">
                  <h4 className="text-orange-800 font-semibold">
                    契約期限間近: {alert.contract_number}
                  </h4>
                  <p className="text-orange-700 text-sm">
                    {alert.worksite_name} - 残り <strong>{alert.days_remaining}日</strong>
                    （{alert.dispatch_end_date}）- {alert.employee_count}名
                  </p>
                </div>
                <Link
                  href={`/kobetsu/${alert.id}`}
                  className="px-3 py-1 bg-orange-600 text-white text-sm rounded hover:bg-orange-700"
                >
                  詳細
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Contracts */}
        <div className="card">
          <div className="card-header flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">
              最近の契約書
            </h2>
            <Link href="/kobetsu" className="text-primary-600 hover:text-primary-700 text-sm">
              すべて表示 →
            </Link>
          </div>
          <div className="card-body p-0">
            {contractsLoading ? (
              <div className="p-6 text-center text-gray-500">
                読み込み中...
              </div>
            ) : recentContracts?.items?.length ? (
              <KobetsuTable
                contracts={recentContracts.items}
                compact
              />
            ) : (
              <div className="p-6 text-center text-gray-500">
                契約書がありません
              </div>
            )}
          </div>
        </div>

        {/* Expiring Soon */}
        <div className="card">
          <div className="card-header flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">
              期限間近の契約書
              {expiringContracts?.length > 0 && (
                <span className="ml-2 badge-expired">
                  {expiringContracts.length}件
                </span>
              )}
            </h2>
          </div>
          <div className="card-body">
            {expiringContracts?.length ? (
              <ul className="divide-y divide-gray-200">
                {expiringContracts.map((contract: any) => (
                  <li key={contract.id} className="py-3">
                    <Link
                      href={`/kobetsu/${contract.id}`}
                      className="flex justify-between items-center hover:bg-gray-50 -mx-4 px-4 py-2 rounded"
                    >
                      <div>
                        <p className="font-medium text-gray-900">
                          {contract.contract_number}
                        </p>
                        <p className="text-sm text-gray-500">
                          {contract.worksite_name}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-red-600 font-medium">
                          {new Date(contract.dispatch_end_date).toLocaleDateString('ja-JP')}
                        </p>
                        <p className="text-xs text-gray-500">
                          まで
                        </p>
                      </div>
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-center text-gray-500 py-4">
                期限間近の契約書はありません
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold text-gray-900">
            クイックアクション
          </h2>
        </div>
        <div className="card-body">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <Link
              href="/assign"
              className="flex flex-col items-center p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors border-2 border-blue-200"
            >
              <span className="text-3xl mb-2">👤</span>
              <span className="text-sm font-medium text-blue-700">従業員配属</span>
            </Link>
            <Link
              href="/kobetsu/create"
              className="flex flex-col items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <span className="text-3xl mb-2">📝</span>
              <span className="text-sm font-medium text-gray-700">新規契約作成</span>
            </Link>
            <Link
              href="/kobetsu?status=draft"
              className="flex flex-col items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <span className="text-3xl mb-2">📋</span>
              <span className="text-sm font-medium text-gray-700">下書き一覧</span>
            </Link>
            <Link
              href="/kobetsu?status=active"
              className="flex flex-col items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <span className="text-3xl mb-2">✅</span>
              <span className="text-sm font-medium text-gray-700">有効な契約</span>
            </Link>
            <Link
              href="/kobetsu?status=expired"
              className="flex flex-col items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <span className="text-3xl mb-2">📊</span>
              <span className="text-sm font-medium text-gray-700">期限切れ</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
