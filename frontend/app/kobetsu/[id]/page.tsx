'use client'

import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { kobetsuApi } from '@/lib/api'
import { StatusBadge } from '@/components/kobetsu/StatusBadge'

export default function KobetsuDetailPage() {
  const params = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const id = Number(params.id)

  const { data: contract, isLoading, error } = useQuery({
    queryKey: ['kobetsu', id],
    queryFn: () => kobetsuApi.getById(id),
    enabled: !!id,
  })

  const activateMutation = useMutation({
    mutationFn: () => kobetsuApi.activate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kobetsu', id] })
      queryClient.invalidateQueries({ queryKey: ['kobetsu-list'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => kobetsuApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kobetsu-list'] })
      router.push('/kobetsu')
    },
  })

  const handleGeneratePDF = async () => {
    try {
      const blob = await kobetsuApi.generatePDF(id, 'pdf')
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${contract?.contract_number}.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      alert('PDF生成に失敗しました')
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner w-8 h-8"></div>
      </div>
    )
  }

  if (error || !contract) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">契約書が見つかりません</p>
        <Link href="/kobetsu" className="btn-primary">
          一覧に戻る
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">
              {contract.contract_number}
            </h1>
            <StatusBadge status={contract.status} />
          </div>
          <p className="text-gray-500 mt-1">
            {contract.worksite_name}
          </p>
        </div>
        <div className="flex gap-2">
          <Link href="/kobetsu" className="btn-secondary">
            ← 一覧に戻る
          </Link>
          {contract.status === 'draft' && (
            <>
              <Link href={`/kobetsu/${id}/edit`} className="btn-secondary">
                編集
              </Link>
              <button
                onClick={() => activateMutation.mutate()}
                className="btn-primary"
                disabled={activateMutation.isPending}
              >
                有効化
              </button>
            </>
          )}
          <button onClick={handleGeneratePDF} className="btn-secondary">
            PDF出力
          </button>
        </div>
      </div>

      {/* Contract Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Basic Info */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">基本情報</h2>
          </div>
          <div className="card-body space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">契約番号</p>
                <p className="font-medium">{contract.contract_number}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">契約締結日</p>
                <p className="font-medium">
                  {new Date(contract.contract_date).toLocaleDateString('ja-JP')}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">派遣開始日</p>
                <p className="font-medium">
                  {new Date(contract.dispatch_start_date).toLocaleDateString('ja-JP')}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">派遣終了日</p>
                <p className="font-medium">
                  {new Date(contract.dispatch_end_date).toLocaleDateString('ja-JP')}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">派遣労働者数</p>
                <p className="font-medium">{contract.number_of_workers}名</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">ステータス</p>
                <StatusBadge status={contract.status} />
              </div>
            </div>
          </div>
        </div>

        {/* Work Location */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">就業場所</h2>
          </div>
          <div className="card-body space-y-4">
            <div>
              <p className="text-sm text-gray-500">事業所名称</p>
              <p className="font-medium">{contract.worksite_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">所在地</p>
              <p className="font-medium">{contract.worksite_address}</p>
            </div>
            {contract.organizational_unit && (
              <div>
                <p className="text-sm text-gray-500">組織単位</p>
                <p className="font-medium">{contract.organizational_unit}</p>
              </div>
            )}
          </div>
        </div>

        {/* Work Content */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">業務内容</h2>
          </div>
          <div className="card-body space-y-4">
            <div>
              <p className="text-sm text-gray-500">業務内容</p>
              <p className="font-medium whitespace-pre-wrap">{contract.work_content}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">責任の程度</p>
              <p className="font-medium">{contract.responsibility_level}</p>
            </div>
          </div>
        </div>

        {/* Supervisor */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">指揮命令者</h2>
          </div>
          <div className="card-body space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-gray-500">部署</p>
                <p className="font-medium">{contract.supervisor_department}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">役職</p>
                <p className="font-medium">{contract.supervisor_position}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">氏名</p>
                <p className="font-medium">{contract.supervisor_name}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Working Hours */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">就業時間</h2>
          </div>
          <div className="card-body space-y-4">
            <div>
              <p className="text-sm text-gray-500">就業日</p>
              <p className="font-medium">{contract.work_days?.join('、')}</p>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-gray-500">始業時刻</p>
                <p className="font-medium">{contract.work_start_time}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">終業時刻</p>
                <p className="font-medium">{contract.work_end_time}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">休憩時間</p>
                <p className="font-medium">{contract.break_time_minutes}分</p>
              </div>
            </div>
          </div>
        </div>

        {/* Rates */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">派遣料金</h2>
          </div>
          <div className="card-body space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">基本時間単価</p>
                <p className="font-medium text-lg">¥{Number(contract.hourly_rate).toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">時間外単価</p>
                <p className="font-medium text-lg">¥{Number(contract.overtime_rate).toLocaleString()}</p>
              </div>
              {contract.night_shift_rate && (
                <div>
                  <p className="text-sm text-gray-500">深夜単価</p>
                  <p className="font-medium">¥{Number(contract.night_shift_rate).toLocaleString()}</p>
                </div>
              )}
              {contract.holiday_rate && (
                <div>
                  <p className="text-sm text-gray-500">休日単価</p>
                  <p className="font-medium">¥{Number(contract.holiday_rate).toLocaleString()}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Notes */}
      {contract.notes && (
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold">備考</h2>
          </div>
          <div className="card-body">
            <p className="whitespace-pre-wrap">{contract.notes}</p>
          </div>
        </div>
      )}

      {/* Actions */}
      {contract.status === 'draft' && (
        <div className="card border-red-200">
          <div className="card-body">
            <h3 className="text-lg font-semibold text-red-600 mb-4">危険な操作</h3>
            <button
              onClick={() => {
                if (confirm('この契約書を削除しますか？この操作は取り消せません。')) {
                  deleteMutation.mutate()
                }
              }}
              className="btn-danger"
              disabled={deleteMutation.isPending}
            >
              契約書を削除
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
