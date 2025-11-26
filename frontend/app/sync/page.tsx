'use client'

/**
 * Sync Page - Sincronización de Datos desde Archivos
 *
 * Sincroniza empleados y fábricas desde archivos maestros:
 * - Empleados: E:\BASEDATEJP\【新】社員台帳(UNS)T　2022.04.05～.xlsm
 * - Fábricas: E:\BASEDATEJP\factories_index.json
 */

import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import axios from 'axios'

// Force correct API URL (debugging - env var issue)
const API_URL = 'http://localhost:8010/api/v1'

export default function SyncPage() {
  const [lastSyncResult, setLastSyncResult] = useState<any>(null)

  // Query para obtener estado actual
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ['syncStatus'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/sync/status`)
      return response.data
    },
    refetchInterval: 30000, // Refrescar cada 30 segundos
  })

  // Mutación para sincronizar empleados
  const syncEmployeesMutation = useMutation({
    mutationFn: async () => {
      const response = await axios.post(`${API_URL}/sync/employees`)
      return response.data
    },
    onSuccess: (data) => {
      setLastSyncResult({
        type: 'employees',
        success: true,
        data
      })
    },
    onError: (error: any) => {
      setLastSyncResult({
        type: 'employees',
        success: false,
        error: error.response?.data?.detail || error.message
      })
    }
  })

  // Mutación para sincronizar fábricas
  const syncFactoriesMutation = useMutation({
    mutationFn: async () => {
      const response = await axios.post(`${API_URL}/sync/factories`)
      return response.data
    },
    onSuccess: (data) => {
      setLastSyncResult({
        type: 'factories',
        success: true,
        data
      })
    },
    onError: (error: any) => {
      setLastSyncResult({
        type: 'factories',
        success: false,
        error: error.response?.data?.detail || error.message
      })
    }
  })

  // Mutación para sincronizar todo
  const syncAllMutation = useMutation({
    mutationFn: async () => {
      const response = await axios.post(`${API_URL}/sync/all`)
      return response.data
    },
    onSuccess: (data) => {
      setLastSyncResult({
        type: 'all',
        success: true,
        data
      })
    },
    onError: (error: any) => {
      setLastSyncResult({
        type: 'all',
        success: false,
        error: error.response?.data?.detail || error.message
      })
    }
  })

  const isAnySyncing =
    syncEmployeesMutation.isPending ||
    syncFactoriesMutation.isPending ||
    syncAllMutation.isPending

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">データ同期</h1>
        <p className="text-gray-600 mt-2">
          ネットワーク上のマスターファイルから従業員と工場のデータを同期
        </p>
      </div>

      {/* Estado Actual */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">現在の状態</h2>
        {statusLoading ? (
          <p>読み込み中...</p>
        ) : status ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 mb-2">従業員</h3>
              <div className="space-y-1 text-sm">
                <p>合計: {status.employees?.total || 0}名</p>
                <p>在籍: {status.employees?.active || 0}名</p>
                <p>退社: {status.employees?.resigned || 0}名</p>
              </div>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <h3 className="font-semibold text-green-900 mb-2">工場</h3>
              <div className="space-y-1 text-sm">
                <p>会社/工場: {status.factories?.total || 0}</p>
                <p>ライン: {status.factories?.lines || 0}</p>
              </div>
            </div>
          </div>
        ) : (
          <p>データを読み込めません</p>
        )}
      </div>

      {/* Botones de Sincronización */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">同期オプション</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Sincronizar Empleados */}
          <button
            onClick={() => syncEmployeesMutation.mutate()}
            disabled={isAnySyncing}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-3 px-6 rounded-lg transition-colors"
          >
            {syncEmployeesMutation.isPending ? (
              <span>同期中...</span>
            ) : (
              <span>従業員を同期</span>
            )}
          </button>

          {/* Sincronizar Fábricas */}
          <button
            onClick={() => syncFactoriesMutation.mutate()}
            disabled={isAnySyncing}
            className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium py-3 px-6 rounded-lg transition-colors"
          >
            {syncFactoriesMutation.isPending ? (
              <span>同期中...</span>
            ) : (
              <span>工場を同期</span>
            )}
          </button>

          {/* Sincronizar Todo */}
          <button
            onClick={() => syncAllMutation.mutate()}
            disabled={isAnySyncing}
            className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white font-medium py-3 px-6 rounded-lg transition-colors"
          >
            {syncAllMutation.isPending ? (
              <span>同期中...</span>
            ) : (
              <span>すべて同期</span>
            )}
          </button>
        </div>

        <div className="mt-4 text-sm text-gray-600 space-y-1">
          <p><strong>従業員:</strong> E:\BASEDATEJP\【新】社員台帳(UNS)T　2022.04.05～.xlsm</p>
          <p><strong>工場:</strong> E:\BASEDATEJP\factories_index.json</p>
        </div>
      </div>

      {/* Resultado de última sincronización */}
      {lastSyncResult && (
        <div className={`rounded-lg shadow-sm border p-6 ${
          lastSyncResult.success
            ? 'bg-green-50 border-green-200'
            : 'bg-red-50 border-red-200'
        }`}>
          <h2 className="text-xl font-semibold mb-4">
            {lastSyncResult.success ? '✅ 同期成功' : '❌ 同期エラー'}
          </h2>

          {lastSyncResult.success ? (
            <div className="space-y-3">
              {/* Empleados */}
              {lastSyncResult.data.employees && (
                <div className="bg-white rounded p-4">
                  <h3 className="font-semibold mb-2">従業員</h3>
                  <div className="text-sm space-y-1">
                    <p>処理済み: {lastSyncResult.data.employees.total || 0}</p>
                    <p>新規作成: {lastSyncResult.data.employees.created || 0}</p>
                    <p>更新: {lastSyncResult.data.employees.updated || 0}</p>
                    {lastSyncResult.data.employees.errors?.length > 0 && (
                      <p className="text-red-600">
                        エラー: {lastSyncResult.data.employees.errors.length}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Fábricas */}
              {lastSyncResult.data.factories && (
                <div className="bg-white rounded p-4">
                  <h3 className="font-semibold mb-2">工場</h3>
                  <div className="text-sm space-y-1">
                    <p>処理済み: {lastSyncResult.data.factories.total || 0}</p>
                    <p>新規作成: {lastSyncResult.data.factories.created || 0}</p>
                    <p>更新: {lastSyncResult.data.factories.updated || 0}</p>
                    {lastSyncResult.data.factories.errors?.length > 0 && (
                      <p className="text-red-600">
                        エラー: {lastSyncResult.data.factories.errors.length}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {lastSyncResult.data.elapsed_seconds && (
                <p className="text-sm text-gray-600">
                  所要時間: {lastSyncResult.data.elapsed_seconds.toFixed(2)}秒
                </p>
              )}
            </div>
          ) : (
            <div className="text-red-700">
              <p className="font-medium">エラーが発生しました:</p>
              <p className="mt-2 text-sm">{lastSyncResult.error}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
