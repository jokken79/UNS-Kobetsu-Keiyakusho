'use client'

import { useEffect, useState } from 'react'

interface WebhookConfig {
  id: number
  name: string
  url: string
  events: string[]
  is_active: boolean
  created_at: string
  last_triggered_at?: string
  description?: string
}

export function WebhookConfigList() {
  const [webhooks, setWebhooks] = useState<WebhookConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)

  useEffect(() => {
    fetchWebhooks()
  }, [])

  const fetchWebhooks = async () => {
    try {
      const response = await fetch('/api/v1/webhooks/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch webhooks')
      }

      const data = await response.json()
      setWebhooks(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleToggle = async (webhookId: number) => {
    try {
      const response = await fetch(`/api/v1/webhooks/${webhookId}/toggle`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to toggle webhook')
      }

      await fetchWebhooks()
    } catch (err: any) {
      setError(err.message)
    }
  }

  const handleDelete = async (webhookId: number) => {
    if (!confirm('このWebhook設定を削除しますか？')) return

    try {
      const response = await fetch(`/api/v1/webhooks/${webhookId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to delete webhook')
      }

      await fetchWebhooks()
    } catch (err: any) {
      setError(err.message)
    }
  }

  const handleTest = async (webhookId: number) => {
    try {
      const response = await fetch(`/api/v1/webhooks/${webhookId}/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          event_type: 'test.webhook',
          event_data: { test: true, timestamp: new Date().toISOString() }
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to test webhook')
      }

      alert('テストWebhookを送信しました')
    } catch (err: any) {
      setError(err.message)
    }
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-3">
        <div className="h-32 bg-gray-200 rounded-lg"></div>
        <div className="h-32 bg-gray-200 rounded-lg"></div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Webhook設定</h2>
        <button
          onClick={() => setShowForm(true)}
          className="btn-primary"
        >
          + Webhook追加
        </button>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 p-4 rounded-lg">
          エラー: {error}
        </div>
      )}

      {webhooks.length === 0 ? (
        <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <p className="text-gray-600 mb-4">Webhookが設定されていません</p>
          <button
            onClick={() => setShowForm(true)}
            className="btn-primary"
          >
            最初のWebhookを追加
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {webhooks.map((webhook) => (
            <div
              key={webhook.id}
              className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold">{webhook.name}</h3>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      webhook.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {webhook.is_active ? '有効' : '無効'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{webhook.url}</p>
                  {webhook.description && (
                    <p className="text-sm text-gray-500">{webhook.description}</p>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => handleToggle(webhook.id)}
                    className={`px-3 py-1 rounded text-sm ${
                      webhook.is_active
                        ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                        : 'bg-green-100 text-green-800 hover:bg-green-200'
                    }`}
                  >
                    {webhook.is_active ? '無効化' : '有効化'}
                  </button>
                  <button
                    onClick={() => handleTest(webhook.id)}
                    className="px-3 py-1 bg-blue-100 text-blue-800 rounded text-sm hover:bg-blue-200"
                  >
                    テスト
                  </button>
                  <button
                    onClick={() => handleDelete(webhook.id)}
                    className="px-3 py-1 bg-red-100 text-red-800 rounded text-sm hover:bg-red-200"
                  >
                    削除
                  </button>
                </div>
              </div>

              <div className="mt-3">
                <p className="text-xs font-medium text-gray-700 mb-2">イベント:</p>
                <div className="flex flex-wrap gap-2">
                  {webhook.events.map((event) => (
                    <span
                      key={event}
                      className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs font-mono"
                    >
                      {event}
                    </span>
                  ))}
                </div>
              </div>

              {webhook.last_triggered_at && (
                <p className="text-xs text-gray-500 mt-3">
                  最終実行: {new Date(webhook.last_triggered_at).toLocaleString('ja-JP')}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
