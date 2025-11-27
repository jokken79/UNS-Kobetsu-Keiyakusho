'use client'

import { useEffect, useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { ja } from 'date-fns/locale'

interface ApprovalEvent {
  id: number
  entity_type: string
  entity_id: number
  action: string
  user_email: string
  user_name?: string
  timestamp: string
  reason?: string
  old_value?: string
  new_value?: string
}

interface ApprovalHistoryProps {
  contractId: number
}

export function ApprovalHistory({ contractId }: ApprovalHistoryProps) {
  const [events, setEvents] = useState<ApprovalEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchApprovalHistory()
  }, [contractId])

  const fetchApprovalHistory = async () => {
    try {
      const response = await fetch(
        `/api/v1/audit/logs/contract/${contractId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      )

      if (!response.ok) {
        throw new Error('Failed to fetch approval history')
      }

      const data = await response.json()
      // Filter only approval-related actions
      const approvalEvents = data.filter((event: ApprovalEvent) =>
        ['submit_for_approval', 'approve', 'reject', 'recall'].includes(event.action)
      )
      setEvents(approvalEvents)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const getActionLabel = (action: string) => {
    const labels: Record<string, string> = {
      submit_for_approval: '承認申請',
      approve: '承認',
      reject: '却下',
      recall: '取り下げ',
    }
    return labels[action] || action
  }

  const getActionColor = (action: string) => {
    const colors: Record<string, string> = {
      submit_for_approval: 'bg-blue-100 text-blue-800',
      approve: 'bg-green-100 text-green-800',
      reject: 'bg-red-100 text-red-800',
      recall: 'bg-gray-100 text-gray-800',
    }
    return colors[action] || 'bg-gray-100 text-gray-800'
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-3">
        <div className="h-20 bg-gray-200 rounded"></div>
        <div className="h-20 bg-gray-200 rounded"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 text-red-600 p-4 rounded-lg">
        エラー: {error}
      </div>
    )
  }

  if (events.length === 0) {
    return (
      <div className="text-gray-500 text-center py-8">
        承認履歴がありません
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold mb-4">承認履歴</h3>

      <div className="space-y-3">
        {events.map((event) => (
          <div
            key={event.id}
            className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-3">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getActionColor(event.action)}`}>
                  {getActionLabel(event.action)}
                </span>
                <div>
                  <div className="font-medium text-gray-900">
                    {event.user_name || event.user_email}
                  </div>
                  <div className="text-xs text-gray-500">
                    {formatDistanceToNow(new Date(event.timestamp), {
                      addSuffix: true,
                      locale: ja,
                    })}
                  </div>
                </div>
              </div>
            </div>

            {event.reason && (
              <div className="mt-2 text-sm text-gray-700 bg-gray-50 p-3 rounded">
                <span className="font-medium">理由: </span>
                {event.reason}
              </div>
            )}

            {event.action === 'reject' && event.new_value && (
              <div className="mt-2 text-sm text-red-700 bg-red-50 p-3 rounded">
                <span className="font-medium">却下理由: </span>
                {event.new_value}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
