'use client'

import { useState, useEffect } from 'react'
import { factoryApi } from '@/lib/api'
import type { KobetsuCreate, FactoryListItem } from '@/types'

interface KobetsuFormProps {
  initialData?: Partial<KobetsuCreate>
  onSubmit: (data: KobetsuCreate) => void
  isLoading?: boolean
}

const WORK_DAYS = ['月', '火', '水', '木', '金', '土', '日']
const RESPONSIBILITY_LEVELS = ['補助的業務', '通常業務', '責任業務']

export function KobetsuForm({ initialData, onSubmit, isLoading }: KobetsuFormProps) {
  const [formData, setFormData] = useState<Partial<KobetsuCreate>>({
    factory_id: undefined,
    employee_ids: [1],
    contract_date: new Date().toISOString().split('T')[0],
    dispatch_start_date: '',
    dispatch_end_date: '',
    work_content: '',
    responsibility_level: '通常業務',
    worksite_name: '',
    worksite_address: '',
    organizational_unit: '',
    supervisor_department: '',
    supervisor_position: '',
    supervisor_name: '',
    work_days: ['月', '火', '水', '木', '金'],
    work_start_time: '08:00',
    work_end_time: '17:00',
    break_time_minutes: 60,
    hourly_rate: 1500,
    overtime_rate: 1875,
    haken_moto_complaint_contact: {
      department: '人事部',
      position: '課長',
      name: '',
      phone: '',
    },
    haken_saki_complaint_contact: {
      department: '',
      position: '',
      name: '',
      phone: '',
    },
    haken_moto_manager: {
      department: '派遣事業部',
      position: '部長',
      name: '',
      phone: '',
    },
    haken_saki_manager: {
      department: '',
      position: '',
      name: '',
      phone: '',
    },
    ...initialData,
  })

  const [factories, setFactories] = useState<FactoryListItem[]>([])
  const [loadingFactories, setLoadingFactories] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    async function loadFactories() {
      setLoadingFactories(true)
      try {
        const data = await factoryApi.getList({ limit: 100 })
        setFactories(data)

        // If initialData has factory_id, use it. Otherwise, if there are factories, select none by default
        if (!initialData?.factory_id && data.length > 0) {
            // Keep undefined to force user selection
        }
      } catch (err) {
        console.error('Failed to load factories', err)
      } finally {
        setLoadingFactories(false)
      }
    }
    loadFactories()
  }, [initialData])

  const handleFactoryChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const factoryId = Number(e.target.value)
    if (!factoryId) return

    setFormData(prev => ({ ...prev, factory_id: factoryId }))

    // Fetch detailed factory data to pre-fill form
    try {
        const factory = await factoryApi.getById(factoryId)
        setFormData(prev => ({
            ...prev,
            factory_id: factoryId,
            worksite_name: factory.plant_name,
            worksite_address: factory.plant_address || factory.company_address || '',
            supervisor_department: factory.supervisor_department || '',
            supervisor_name: factory.supervisor_name || '',
            haken_saki_complaint_contact: {
                department: factory.client_complaint_department || '',
                position: '', // Usually not in factory data directly unless mapped
                name: factory.client_complaint_name || '',
                phone: factory.client_complaint_phone || '',
            },
            haken_saki_manager: {
                department: factory.client_responsible_department || '',
                position: '',
                name: factory.client_responsible_name || '',
                phone: factory.client_responsible_phone || '',
            }
        }))
    } catch (err) {
        console.error('Failed to load factory details', err)
    }
  }

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? Number(value) : value,
    }))
  }

  const handleNestedChange = (
    parent: string,
    field: string,
    value: string
  ) => {
    setFormData((prev) => ({
      ...prev,
      [parent]: {
        ...(prev as any)[parent],
        [field]: value,
      },
    }))
  }

  const handleWorkDaysChange = (day: string) => {
    setFormData((prev) => {
      const currentDays = prev.work_days || []
      const newDays = currentDays.includes(day)
        ? currentDays.filter((d) => d !== day)
        : [...currentDays, day]
      return { ...prev, work_days: newDays }
    })
  }

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.factory_id) {
        newErrors.factory_id = '工場を選択してください'
    }
    if (!formData.worksite_name) {
      newErrors.worksite_name = '派遣先名を入力してください'
    }
    if (!formData.worksite_address) {
      newErrors.worksite_address = '所在地を入力してください'
    }
    if (!formData.work_content || formData.work_content.length < 10) {
      newErrors.work_content = '業務内容を10文字以上で入力してください'
    }
    if (!formData.dispatch_start_date) {
      newErrors.dispatch_start_date = '開始日を入力してください'
    }
    if (!formData.dispatch_end_date) {
      newErrors.dispatch_end_date = '終了日を入力してください'
    }
    if (formData.dispatch_start_date && formData.dispatch_end_date) {
      if (formData.dispatch_end_date < formData.dispatch_start_date) {
        newErrors.dispatch_end_date = '終了日は開始日以降にしてください'
      }
    }
    if (!formData.supervisor_name) {
      newErrors.supervisor_name = '指揮命令者を入力してください'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validate()) {
      onSubmit(formData as KobetsuCreate)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* Section 0: Factory Selection */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          派遣先選択
        </h3>
        <div className="grid grid-cols-1 gap-6">
            <div>
                <label className="form-label">工場を選択 *</label>
                <select
                    name="factory_id"
                    value={formData.factory_id || ''}
                    onChange={handleFactoryChange}
                    className={`form-select ${errors.factory_id ? 'border-red-500' : ''}`}
                    disabled={loadingFactories}
                    required
                >
                    <option value="">-- 選択してください --</option>
                    {factories.map(f => (
                        <option key={f.id} value={f.id}>
                            {f.company_name} - {f.plant_name}
                        </option>
                    ))}
                </select>
                {loadingFactories && <p className="text-sm text-gray-500 mt-1">読み込み中...</p>}
                {errors.factory_id && (
                  <p className="form-error">{errors.factory_id}</p>
                )}
            </div>
        </div>
      </section>

      {/* Section 1: Basic Info */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          基本情報
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="form-label">契約締結日 *</label>
            <input
              type="date"
              name="contract_date"
              value={formData.contract_date}
              onChange={handleChange}
              className="form-input"
              required
            />
          </div>
          <div></div>
          <div>
            <label className="form-label">派遣開始日 *</label>
            <input
              type="date"
              name="dispatch_start_date"
              value={formData.dispatch_start_date}
              onChange={handleChange}
              className={`form-input ${errors.dispatch_start_date ? 'border-red-500' : ''}`}
              required
            />
            {errors.dispatch_start_date && (
              <p className="form-error">{errors.dispatch_start_date}</p>
            )}
          </div>
          <div>
            <label className="form-label">派遣終了日 *</label>
            <input
              type="date"
              name="dispatch_end_date"
              value={formData.dispatch_end_date}
              onChange={handleChange}
              className={`form-input ${errors.dispatch_end_date ? 'border-red-500' : ''}`}
              required
            />
            {errors.dispatch_end_date && (
              <p className="form-error">{errors.dispatch_end_date}</p>
            )}
          </div>
        </div>
      </section>

      {/* Section 2: Work Location */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          就業場所
        </h3>
        <div className="grid grid-cols-1 gap-6">
          <div>
            <label className="form-label">派遣先事業所名 *</label>
            <input
              type="text"
              name="worksite_name"
              value={formData.worksite_name}
              onChange={handleChange}
              className={`form-input ${errors.worksite_name ? 'border-red-500' : ''}`}
              placeholder="例: トヨタ自動車株式会社 田原工場"
              required
            />
            {errors.worksite_name && (
              <p className="form-error">{errors.worksite_name}</p>
            )}
          </div>
          <div>
            <label className="form-label">所在地 *</label>
            <input
              type="text"
              name="worksite_address"
              value={formData.worksite_address}
              onChange={handleChange}
              className={`form-input ${errors.worksite_address ? 'border-red-500' : ''}`}
              placeholder="例: 愛知県田原市緑が浜2号1番地"
              required
            />
            {errors.worksite_address && (
              <p className="form-error">{errors.worksite_address}</p>
            )}
          </div>
          <div>
            <label className="form-label">組織単位</label>
            <input
              type="text"
              name="organizational_unit"
              value={formData.organizational_unit}
              onChange={handleChange}
              className="form-input"
              placeholder="例: 第1製造部"
            />
          </div>
        </div>
      </section>

      {/* Section 3: Work Content */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          業務内容
        </h3>
        <div className="grid grid-cols-1 gap-6">
          <div>
            <label className="form-label">業務内容 *</label>
            <textarea
              name="work_content"
              value={formData.work_content}
              onChange={handleChange}
              className={`form-textarea ${errors.work_content ? 'border-red-500' : ''}`}
              rows={4}
              placeholder="例: 製造ライン作業、検品、梱包業務"
              required
            />
            {errors.work_content && (
              <p className="form-error">{errors.work_content}</p>
            )}
          </div>
          <div>
            <label className="form-label">責任の程度 *</label>
            <select
              name="responsibility_level"
              value={formData.responsibility_level}
              onChange={handleChange}
              className="form-select"
              required
            >
              {RESPONSIBILITY_LEVELS.map((level) => (
                <option key={level} value={level}>
                  {level}
                </option>
              ))}
            </select>
          </div>
        </div>
      </section>

      {/* Section 4: Supervisor */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          指揮命令者
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="form-label">部署 *</label>
            <input
              type="text"
              name="supervisor_department"
              value={formData.supervisor_department}
              onChange={handleChange}
              className="form-input"
              placeholder="例: 製造部"
              required
            />
          </div>
          <div>
            <label className="form-label">役職 *</label>
            <input
              type="text"
              name="supervisor_position"
              value={formData.supervisor_position}
              onChange={handleChange}
              className="form-input"
              placeholder="例: 課長"
              required
            />
          </div>
          <div>
            <label className="form-label">氏名 *</label>
            <input
              type="text"
              name="supervisor_name"
              value={formData.supervisor_name}
              onChange={handleChange}
              className={`form-input ${errors.supervisor_name ? 'border-red-500' : ''}`}
              placeholder="例: 田中太郎"
              required
            />
            {errors.supervisor_name && (
              <p className="form-error">{errors.supervisor_name}</p>
            )}
          </div>
        </div>
      </section>

      {/* Section 5: Working Hours */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          就業時間
        </h3>
        <div className="grid grid-cols-1 gap-6">
          <div>
            <label className="form-label">就業日 *</label>
            <div className="flex flex-wrap gap-2">
              {WORK_DAYS.map((day) => (
                <button
                  key={day}
                  type="button"
                  onClick={() => handleWorkDaysChange(day)}
                  className={`px-4 py-2 rounded-md border ${
                    formData.work_days?.includes(day)
                      ? 'bg-primary-600 text-white border-primary-600'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {day}
                </button>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="form-label">始業時刻 *</label>
              <input
                type="time"
                name="work_start_time"
                value={formData.work_start_time}
                onChange={handleChange}
                className="form-input"
                required
              />
            </div>
            <div>
              <label className="form-label">終業時刻 *</label>
              <input
                type="time"
                name="work_end_time"
                value={formData.work_end_time}
                onChange={handleChange}
                className="form-input"
                required
              />
            </div>
            <div>
              <label className="form-label">休憩時間（分） *</label>
              <input
                type="number"
                name="break_time_minutes"
                value={formData.break_time_minutes}
                onChange={handleChange}
                className="form-input"
                min={0}
                max={180}
                required
              />
            </div>
          </div>
        </div>
      </section>

      {/* Section 6: Rates */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          派遣料金
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="form-label">基本時間単価（円） *</label>
            <input
              type="number"
              name="hourly_rate"
              value={formData.hourly_rate}
              onChange={handleChange}
              className="form-input"
              min={1000}
              max={10000}
              required
            />
          </div>
          <div>
            <label className="form-label">時間外単価（円） *</label>
            <input
              type="number"
              name="overtime_rate"
              value={formData.overtime_rate}
              onChange={handleChange}
              className="form-input"
              min={1000}
              max={15000}
              required
            />
          </div>
        </div>
      </section>

      {/* Section 7: Complaint Contacts */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          苦情処理担当者
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Haken Moto */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium mb-4">派遣元（UNS企画）</h4>
            <div className="space-y-4">
              <input
                type="text"
                value={formData.haken_moto_complaint_contact?.name}
                onChange={(e) => handleNestedChange('haken_moto_complaint_contact', 'name', e.target.value)}
                className="form-input"
                placeholder="氏名"
              />
              <input
                type="tel"
                value={formData.haken_moto_complaint_contact?.phone}
                onChange={(e) => handleNestedChange('haken_moto_complaint_contact', 'phone', e.target.value)}
                className="form-input"
                placeholder="電話番号 (例: 03-1234-5678)"
              />
            </div>
          </div>

          {/* Haken Saki */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium mb-4">派遣先</h4>
            <div className="space-y-4">
              <input
                type="text"
                value={formData.haken_saki_complaint_contact?.department}
                onChange={(e) => handleNestedChange('haken_saki_complaint_contact', 'department', e.target.value)}
                className="form-input"
                placeholder="部署"
              />
              <input
                type="text"
                value={formData.haken_saki_complaint_contact?.name}
                onChange={(e) => handleNestedChange('haken_saki_complaint_contact', 'name', e.target.value)}
                className="form-input"
                placeholder="氏名"
              />
              <input
                type="tel"
                value={formData.haken_saki_complaint_contact?.phone}
                onChange={(e) => handleNestedChange('haken_saki_complaint_contact', 'phone', e.target.value)}
                className="form-input"
                placeholder="電話番号"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Section 8: Managers */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          責任者
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Haken Moto Manager */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium mb-4">派遣元責任者</h4>
            <div className="space-y-4">
              <input
                type="text"
                value={formData.haken_moto_manager?.name}
                onChange={(e) => handleNestedChange('haken_moto_manager', 'name', e.target.value)}
                className="form-input"
                placeholder="氏名"
              />
              <input
                type="tel"
                value={formData.haken_moto_manager?.phone}
                onChange={(e) => handleNestedChange('haken_moto_manager', 'phone', e.target.value)}
                className="form-input"
                placeholder="電話番号"
              />
            </div>
          </div>

          {/* Haken Saki Manager */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <h4 className="font-medium mb-4">派遣先責任者</h4>
            <div className="space-y-4">
              <input
                type="text"
                value={formData.haken_saki_manager?.department}
                onChange={(e) => handleNestedChange('haken_saki_manager', 'department', e.target.value)}
                className="form-input"
                placeholder="部署"
              />
              <input
                type="text"
                value={formData.haken_saki_manager?.name}
                onChange={(e) => handleNestedChange('haken_saki_manager', 'name', e.target.value)}
                className="form-input"
                placeholder="氏名"
              />
              <input
                type="tel"
                value={formData.haken_saki_manager?.phone}
                onChange={(e) => handleNestedChange('haken_saki_manager', 'phone', e.target.value)}
                className="form-input"
                placeholder="電話番号"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Section 9: Notes */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          備考
        </h3>
        <textarea
          name="notes"
          value={formData.notes || ''}
          onChange={handleChange}
          className="form-textarea"
          rows={4}
          placeholder="その他の特記事項"
        />
      </section>

      {/* Submit */}
      <div className="flex justify-end gap-4 pt-6 border-t">
        <button type="button" className="btn-secondary">
          キャンセル
        </button>
        <button
          type="submit"
          className="btn-primary"
          disabled={isLoading}
        >
          {isLoading ? '保存中...' : '契約書を作成'}
        </button>
      </div>
    </form>
  )
}
