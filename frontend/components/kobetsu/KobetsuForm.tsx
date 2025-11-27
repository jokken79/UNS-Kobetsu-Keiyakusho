'use client'

import { useState, useEffect } from 'react'
import { factoryApi } from '@/lib/api'
import type { KobetsuCreate, FactoryListItem, LineOption } from '@/types'

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
    overtime_max_hours_day: undefined,
    overtime_max_hours_month: undefined,
    holiday_work_max_days: undefined,
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
  const [lines, setLines] = useState<LineOption[]>([])
  const [selectedLineId, setSelectedLineId] = useState<string>('')

  const [loadingFactories, setLoadingFactories] = useState(false)
  const [loadingLines, setLoadingLines] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    async function loadFactories() {
      setLoadingFactories(true)
      try {
        const data = await factoryApi.getList({ limit: 100 })
        setFactories(data)
      } catch (err) {
        console.error('Failed to load factories', err)
      } finally {
        setLoadingFactories(false)
      }
    }
    loadFactories()
  }, [])

  const handleFactoryChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const factoryId = Number(e.target.value)
    if (!factoryId) {
        setFormData(prev => ({ ...prev, factory_id: undefined }))
        setLines([])
        return
    }

    setFormData(prev => ({ ...prev, factory_id: factoryId }))

    // Fetch detailed factory data to pre-fill form
    try {
        const factory = await factoryApi.getById(factoryId)

        setFormData(prev => ({
            ...prev,
            factory_id: factoryId,
            worksite_name: factory.plant_name,
            worksite_address: factory.plant_address || factory.company_address || '',

            // Supervisor (Factory Default)
            supervisor_department: factory.supervisor_department || '',
            supervisor_name: factory.supervisor_name || '',

            // Working Conditions
            work_start_time: factory.day_shift_start?.toString().slice(0, 5) || '08:00',
            work_end_time: factory.day_shift_end?.toString().slice(0, 5) || '17:00',
            break_time_minutes: factory.break_minutes || 60,

            // Overtime Limits
            overtime_max_hours_day: factory.overtime_max_hours_day,
            overtime_max_hours_month: factory.overtime_max_hours_month,
            holiday_work_max_days: factory.holiday_work_max_days_month,

            // Haken Moto (UNS) Contacts from Factory Settings
            haken_moto_complaint_contact: {
                department: factory.dispatch_complaint_department || '管理部',
                position: '担当者',
                name: factory.dispatch_complaint_name || '',
                phone: factory.dispatch_complaint_phone || '',
            },
            haken_moto_manager: {
                department: factory.dispatch_responsible_department || '派遣事業部',
                position: '責任者',
                name: factory.dispatch_responsible_name || '',
                phone: factory.dispatch_responsible_phone || '',
            },

            // Haken Saki Contacts
            haken_saki_complaint_contact: {
                department: factory.client_complaint_department || '',
                position: '',
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

        // Load lines for this factory
        setLoadingLines(true)
        try {
            const linesData = await factoryApi.getLines(factoryId)
            setLines(linesData)
            setSelectedLineId('')
        } catch (err) {
            console.error('Failed to load lines', err)
        } finally {
            setLoadingLines(false)
        }

    } catch (err) {
        console.error('Failed to load factory details', err)
    }
  }

  const handleLineChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
      const lineId = e.target.value
      setSelectedLineId(lineId)

      const line = lines.find(l => l.id.toString() === lineId)
      if (line) {
          // Pre-fill line specific data
          setFormData(prev => ({
              ...prev,
              organizational_unit: line.department, // e.g. "Manufacturing Dept"
              work_content: line.name, // Usually maps to job description or line name
              // Note: LineOption might not have all details.
              // If LineOption is just {id, name}, we might need to fetch detailed line data or assume name is enough.
              // Assuming LineOption might be limited, but let's see.
              // If `factoryApi.getLines` returns full objects, we can use them.
              // The interface `LineOption` usually has id and name.
              // Let's assume we might need to fetch cascade data or just use what we have.
              // For now, let's put line name in organizational unit if department is missing.
          }))

          // If we had full line details (rates, etc), we would set them here.
          // Since getLines usually returns lightweight options, we might want to fetch details.
          // But `factoryApi.getCascadeData` exists.
          fetchLineDetails(Number(lineId))
      }
  }

  const fetchLineDetails = async (lineId: number) => {
      try {
          // This endpoint might return what we need
          const data = await factoryApi.getCascadeData(lineId)
          // `data` likely contains: rates, job description, supervisor override
          if (data) {
              setFormData(prev => ({
                  ...prev,
                  work_content: data.job_description || prev.work_content,
                  responsibility_level: data.responsibility_level || prev.responsibility_level,
                  hourly_rate: data.hourly_rate || prev.hourly_rate,
                  overtime_rate: data.overtime_rate || prev.overtime_rate,
                  organizational_unit: data.department || prev.organizational_unit,
                  // Supervisor override if present
                  supervisor_department: data.supervisor_department || prev.supervisor_department,
                  supervisor_name: data.supervisor_name || prev.supervisor_name,
              }))
          }
      } catch (err) {
          console.error('Failed to fetch line details', err)
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
      {/* Section 0: Factory & Line Selection */}
      <section>
        <h3 className="text-lg font-medium text-gray-900 mb-4 pb-2 border-b">
          派遣先・配属先選択
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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

            <div>
                <label className="form-label">配属ライン (任意)</label>
                <select
                    name="line_id"
                    value={selectedLineId}
                    onChange={handleLineChange}
                    className="form-select"
                    disabled={!formData.factory_id || loadingLines}
                >
                    <option value="">-- ライン/部署を選択 --</option>
                    {lines.map(l => (
                        <option key={l.id} value={l.id}>
                            {l.name}
                        </option>
                    ))}
                </select>
                {loadingLines && <p className="text-sm text-gray-500 mt-1">読み込み中...</p>}
                <p className="text-xs text-gray-500 mt-1">
                    選択すると業務内容や単価が自動入力されます
                </p>
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
