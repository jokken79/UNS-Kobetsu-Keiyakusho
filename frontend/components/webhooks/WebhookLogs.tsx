'use client'

import { useEffect, useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { ja } from 'date-fns/locale'

interface WebhookLog {
  id: number
  webhook_config_id: number
  event_type: string
  attempt_number: number
  status_code?: number
  success: boolean
  attempted_at: string
  response_time_ms?: number
  error_message?: string
}

interface WebhookLogsProps {
  webhookId: number
}

export function WebhookLogs({ webhookId }: WebhookLogsProps) {
  const [logs, setLogs] = useState<WebhookLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState<'all' | 'success' | 'failed'>('all')

  useEffect(() => {
    fetchLogs()
  }, [webhookId, filter])

  const fetchLogs = async () => {
    try {
      let url = `/api/v1/webhooks/${webhookId}/logs?limit=50`
      if (filter === 'success') {
        url += '&success_only=true'
      } else if (filter === 'failed') {
        url += '&success_only=false'
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch webhook logs')
      }

      const data = await response.json()
      setLogs(data.items)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRetry = async (logId: number) => {
    try {
      const response = await fetch(`/api/v1/webhooks/logs/${logId}/retry`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to retry webhook')
      }

      alert('Webhookの再送信をキューに追加しました')
    } catch (err: any) {
      setError(err.message)
    }
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-2">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-16 bg-gray-200 rounded"></div>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">配信ログ</h3>
        <div className="flex gap-2">
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1 rounded text-sm ${
              filter === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            すべて
          </button>
          <button
            onClick={() => setFilter('success')}
            className={`px-3 py-1 rounded text-sm ${
              filter === 'success'
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            成功
          </button>
          <button
            onClick={() => setFilter('failed')}
            className={`px-3 py-1 rounded text-sm ${
              filter === 'failed'
                ? 'bg-red-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            失敗
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded text-sm">
          {error}
        </div>
      )}

      {logs.length === 0 ? (
        <div className="text-center text-gray-500 py-8">
          ログがありません
        </div>
      ) : (
        <div className="space-y-2">
          {logs.map((log) => (
            <div
              key={log.id}
              className={`border rounded-lg p-4 ${
                log.success
                  ? 'border-green-200 bg-green-50'
                  : 'border-red-200 bg-red-50'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <span className={`w-3 h-3 rounded-full ${
                    log.success ? 'bg-green-500' : 'bg-red-500'
                  }`}></span>
                  <span className="font-mono text-sm text-gray-700">
                    {log.event_type}
                  </span>
                  {log.status_code && (
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      log.status_code >= 200 && log.status_code < 300
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {log.status_code}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-500">
                    {formatDistanceToNow(new Date(log.attempted_at), {
                      addSuffix: true,
                      locale: ja,
                    })}
                  </span>
                  {!log.success && (
                    <button
                      onClick={() => handleRetry(log.id)}
                      className="text-xs text-blue-600 hover:text-blue-800"
                    >
                      再送信
                    </button>
                  )}
                </div>
              </div>

              {log.response_time_ms && (
                <div className="text-xs text-gray-600 mb-1">
                  レスポンス時間: {log.response_time_ms}ms
                </div>
              )}

              {log.error_message && (
                <div className="text-xs text-red-700 bg-red-100 p-2 rounded mt-2 font-mono">
                  {log.error_message}
                </div>
              )}

              {log.attempt_number > 1 && (
                <div className="text-xs text-gray-600 mt-1">
                  試行回数: {log.attempt_number}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
