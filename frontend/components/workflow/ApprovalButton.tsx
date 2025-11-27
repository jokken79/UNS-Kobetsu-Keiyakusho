'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

interface ApprovalButtonProps {
  contractId: number
  currentStatus: string
  onSuccess?: () => void
}

export function ApprovalButton({ contractId, currentStatus, onSuccess }: ApprovalButtonProps) {
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [showModal, setShowModal] = useState(false)
  const [action, setAction] = useState<'submit' | 'approve' | 'reject' | 'recall'>('submit')
  const [notes, setNotes] = useState('')
  const [error, setError] = useState('')

  const handleAction = async (actionType: typeof action) => {
    setAction(actionType)
    if (actionType === 'reject') {
      setShowModal(true)
    } else {
      await executeAction(actionType)
    }
  }

  const executeAction = async (actionType: typeof action) => {
    setIsSubmitting(true)
    setError('')

    try {
      const endpoints = {
        submit: `/api/v1/approvals/contract/${contractId}/submit`,
        approve: `/api/v1/approvals/contract/${contractId}/approve`,
        reject: `/api/v1/approvals/contract/${contractId}/reject`,
        recall: `/api/v1/approvals/contract/${contractId}/recall`,
      }

      const response = await fetch(endpoints[actionType], {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ notes }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Failed to perform action')
      }

      setShowModal(false)
      setNotes('')

      if (onSuccess) {
        onSuccess()
      } else {
        router.refresh()
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleModalConfirm = () => {
    if (action === 'reject' && !notes.trim()) {
      setError('却下理由は必須です')
      return
    }
    executeAction(action)
  }

  // Render buttons based on status
  if (currentStatus === 'draft' || currentStatus === 'rejected') {
    return (
      <button
        onClick={() => handleAction('submit')}
        disabled={isSubmitting}
        className="btn-primary"
      >
        {isSubmitting ? '送信中...' : '承認申請'}
      </button>
    )
  }

  if (currentStatus === 'pending_approval') {
    return (
      <div className="flex gap-2">
        <button
          onClick={() => handleAction('approve')}
          disabled={isSubmitting}
          className="btn-success"
        >
          {isSubmitting ? '処理中...' : '承認'}
        </button>
        <button
          onClick={() => handleAction('reject')}
          disabled={isSubmitting}
          className="btn-danger"
        >
          却下
        </button>
        <button
          onClick={() => handleAction('recall')}
          disabled={isSubmitting}
          className="btn-secondary"
        >
          取り下げ
        </button>

        {/* Rejection Modal */}
        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold mb-4">却下理由を入力</h3>

              {error && (
                <div className="bg-red-50 text-red-600 p-3 rounded mb-4 text-sm">
                  {error}
                </div>
              )}

              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="却下理由を入力してください（必須）"
                className="w-full border border-gray-300 rounded-lg p-3 mb-4 h-32 resize-none focus:outline-none focus:ring-2 focus:ring-red-500"
                disabled={isSubmitting}
              />

              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => {
                    setShowModal(false)
                    setNotes('')
                    setError('')
                  }}
                  disabled={isSubmitting}
                  className="btn-secondary"
                >
                  キャンセル
                </button>
                <button
                  onClick={handleModalConfirm}
                  disabled={isSubmitting}
                  className="btn-danger"
                >
                  {isSubmitting ? '処理中...' : '却下'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  return null
}
