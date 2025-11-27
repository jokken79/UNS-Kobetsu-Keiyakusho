'use client'

import { useEffect, useState } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { ja } from 'date-fns/locale'

interface Comment {
  id: number
  contract_id: number
  parent_id: number | null
  user_id: number
  user_email: string
  user_name?: string
  content: string
  comment_type: string
  is_internal: boolean
  created_at: string
  updated_at?: string
  is_edited: boolean
  is_deleted: boolean
}

interface CommentThreadProps {
  contractId: number
  currentUserId?: number
}

export function CommentThread({ contractId, currentUserId }: CommentThreadProps) {
  const [comments, setComments] = useState<Comment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [newComment, setNewComment] = useState('')
  const [replyTo, setReplyTo] = useState<number | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editContent, setEditContent] = useState('')

  useEffect(() => {
    fetchComments()
  }, [contractId])

  const fetchComments = async () => {
    try {
      const response = await fetch(
        `/api/v1/comments/contract/${contractId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        }
      )

      if (!response.ok) {
        throw new Error('Failed to fetch comments')
      }

      const data = await response.json()
      setComments(data)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmitComment = async () => {
    if (!newComment.trim()) return

    setIsSubmitting(true)
    setError('')

    try {
      const response = await fetch('/api/v1/comments/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          contract_id: contractId,
          content: newComment,
          parent_id: replyTo,
          comment_type: 'general',
          is_internal: true,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to post comment')
      }

      setNewComment('')
      setReplyTo(null)
      await fetchComments()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleEditComment = async (commentId: number) => {
    if (!editContent.trim()) return

    setIsSubmitting(true)
    setError('')

    try {
      const response = await fetch(`/api/v1/comments/${commentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          content: editContent,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to update comment')
      }

      setEditingId(null)
      setEditContent('')
      await fetchComments()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDeleteComment = async (commentId: number) => {
    if (!confirm('このコメントを削除しますか？')) return

    try {
      const response = await fetch(`/api/v1/comments/${commentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to delete comment')
      }

      await fetchComments()
    } catch (err: any) {
      setError(err.message)
    }
  }

  const renderComment = (comment: Comment, isReply: boolean = false) => {
    const isOwnComment = currentUserId === comment.user_id
    const replies = comments.filter(c => c.parent_id === comment.id)

    return (
      <div key={comment.id} className={`${isReply ? 'ml-12 mt-3' : 'mb-4'}`}>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium text-sm">
                {(comment.user_name || comment.user_email)[0].toUpperCase()}
              </div>
              <div>
                <div className="font-medium text-sm text-gray-900">
                  {comment.user_name || comment.user_email}
                </div>
                <div className="text-xs text-gray-500">
                  {formatDistanceToNow(new Date(comment.created_at), {
                    addSuffix: true,
                    locale: ja,
                  })}
                  {comment.is_edited && ' (編集済み)'}
                </div>
              </div>
            </div>

            {isOwnComment && !comment.is_deleted && (
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setEditingId(comment.id)
                    setEditContent(comment.content)
                  }}
                  className="text-blue-600 hover:text-blue-800 text-sm"
                >
                  編集
                </button>
                <button
                  onClick={() => handleDeleteComment(comment.id)}
                  className="text-red-600 hover:text-red-800 text-sm"
                >
                  削除
                </button>
              </div>
            )}
          </div>

          {editingId === comment.id ? (
            <div className="mt-2">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="w-full border border-gray-300 rounded-lg p-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                disabled={isSubmitting}
              />
              <div className="flex gap-2 mt-2">
                <button
                  onClick={() => handleEditComment(comment.id)}
                  disabled={isSubmitting}
                  className="btn-primary-sm"
                >
                  {isSubmitting ? '保存中...' : '保存'}
                </button>
                <button
                  onClick={() => {
                    setEditingId(null)
                    setEditContent('')
                  }}
                  className="btn-secondary-sm"
                >
                  キャンセル
                </button>
              </div>
            </div>
          ) : (
            <>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                {comment.content}
              </p>

              {!isReply && !comment.is_deleted && (
                <button
                  onClick={() => setReplyTo(comment.id)}
                  className="text-blue-600 hover:text-blue-800 text-xs mt-2"
                >
                  返信
                </button>
              )}
            </>
          )}
        </div>

        {/* Render replies */}
        {replies.length > 0 && (
          <div className="mt-2">
            {replies.map(reply => renderComment(reply, true))}
          </div>
        )}

        {/* Reply input */}
        {replyTo === comment.id && (
          <div className="ml-12 mt-3 bg-gray-50 border border-gray-200 rounded-lg p-3">
            <textarea
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="返信を入力..."
              className="w-full border border-gray-300 rounded-lg p-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              disabled={isSubmitting}
            />
            <div className="flex gap-2 mt-2">
              <button
                onClick={handleSubmitComment}
                disabled={isSubmitting || !newComment.trim()}
                className="btn-primary-sm"
              >
                {isSubmitting ? '送信中...' : '返信'}
              </button>
              <button
                onClick={() => {
                  setReplyTo(null)
                  setNewComment('')
                }}
                className="btn-secondary-sm"
              >
                キャンセル
              </button>
            </div>
          </div>
        )}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-3">
        <div className="h-24 bg-gray-200 rounded-lg"></div>
        <div className="h-24 bg-gray-200 rounded-lg"></div>
      </div>
    )
  }

  const topLevelComments = comments.filter(c => !c.parent_id)

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold mb-4">コメント ({comments.length})</h3>

      {error && (
        <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* New comment input */}
      {!replyTo && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="コメントを入力..."
            className="w-full border border-gray-300 rounded-lg p-3 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={3}
            disabled={isSubmitting}
          />
          <button
            onClick={handleSubmitComment}
            disabled={isSubmitting || !newComment.trim()}
            className="btn-primary mt-3"
          >
            {isSubmitting ? '送信中...' : 'コメント投稿'}
          </button>
        </div>
      )}

      {/* Comments list */}
      <div className="space-y-4">
        {topLevelComments.length === 0 ? (
          <div className="text-gray-500 text-center py-8">
            まだコメントがありません
          </div>
        ) : (
          topLevelComments.map(comment => renderComment(comment))
        )}
      </div>
    </div>
  )
}
