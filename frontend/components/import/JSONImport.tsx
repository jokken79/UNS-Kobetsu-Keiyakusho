'use client'

import { useState } from 'react'

interface ImportResult {
  success: boolean
  total_rows: number
  imported_count: number
  updated_count: number
  skipped_count: number
  factories_created?: number
  lines_created?: number
  errors: Array<{
    row: number
    field: string
    message: string
    value?: any
  }>
  message: string
}

interface JSONImportProps {
  type: 'factories' | 'employees'
  onSuccess?: () => void
}

export function JSONImport({ type, onSuccess }: JSONImportProps) {
  const [file, setFile] = useState<File | null>(null)
  const [jsonText, setJsonText] = useState('')
  const [importing, setImporting] = useState(false)
  const [result, setResult] = useState<ImportResult | null>(null)
  const [error, setError] = useState('')
  const [inputMode, setInputMode] = useState<'file' | 'text'>('file')

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.json')) {
        setError('JSONファイルを選択してください')
        return
      }
      setFile(selectedFile)
      setError('')
    }
  }

  const handleImport = async () => {
    setImporting(true)
    setError('')
    setResult(null)

    try {
      let jsonData: any

      if (inputMode === 'file') {
        if (!file) {
          throw new Error('ファイルを選択してください')
        }

        const fileContent = await file.text()
        jsonData = JSON.parse(fileContent)
      } else {
        if (!jsonText.trim()) {
          throw new Error('JSONデータを入力してください')
        }
        jsonData = JSON.parse(jsonText)
      }

      const endpoint = type === 'factories'
        ? '/api/v1/import/factories-json'
        : '/api/v1/import/employees-json'

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(jsonData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Import failed')
      }

      const data = await response.json()
      setResult(data)

      if (data.success && onSuccess) {
        onSuccess()
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setImporting(false)
    }
  }

  const title = type === 'factories' ? '工場データ JSONインポート' : '社員データ JSONインポート'
  const description = type === 'factories'
    ? 'JSON形式の工場データをインポートします。工場とライン情報を一括登録できます。'
    : 'JSON形式の社員データをインポートします。社員情報を一括登録・更新できます。'

  const sampleJson = type === 'factories' ? `{
  "company_name": "トヨタ自動車",
  "派遣先名": "トヨタ自動車",
  "plant_name": "田原工場",
  "工場名": "田原工場",
  "plant_address": "愛知県田原市",
  "conflict_date": "2025-03-01",
  "lines": [
    {
      "line_name": "組立ライン1",
      "department": "製造部",
      "hourly_rate": 1500,
      "billing_rate": 2000
    }
  ]
}` : `{
  "employee_number": "EMP001",
  "社員番号": "EMP001",
  "full_name_kanji": "山田太郎",
  "氏名": "山田太郎",
  "full_name_kana": "ヤマダタロウ",
  "カナ": "ヤマダタロウ",
  "hire_date": "2024-01-01",
  "入社日": "2024-01-01",
  "hourly_rate": 1300,
  "時給": 1300,
  "billing_rate": 1800,
  "単価": 1800
}`

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-xl font-bold mb-2">{title}</h2>
      <p className="text-sm text-gray-600 mb-6">{description}</p>

      {/* Input mode selector */}
      <div className="flex gap-4 mb-4">
        <button
          onClick={() => setInputMode('file')}
          className={`px-4 py-2 rounded ${
            inputMode === 'file'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          ファイル選択
        </button>
        <button
          onClick={() => setInputMode('text')}
          className={`px-4 py-2 rounded ${
            inputMode === 'text'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          テキスト入力
        </button>
      </div>

      {/* File input */}
      {inputMode === 'file' ? (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            JSONファイルを選択
          </label>
          <input
            type="file"
            accept=".json"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none p-2"
            disabled={importing}
          />
          {file && (
            <p className="text-sm text-green-600 mt-2">
              選択済み: {file.name}
            </p>
          )}
        </div>
      ) : (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            JSONデータを入力
          </label>
          <textarea
            value={jsonText}
            onChange={(e) => setJsonText(e.target.value)}
            placeholder={sampleJson}
            className="w-full h-64 border border-gray-300 rounded-lg p-3 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={importing}
          />
        </div>
      )}

      {/* Sample JSON */}
      <details className="mb-4">
        <summary className="cursor-pointer text-sm font-medium text-blue-600 hover:text-blue-800">
          サンプルJSON形式を表示
        </summary>
        <pre className="mt-2 bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs overflow-auto">
          {sampleJson}
        </pre>
        <p className="text-xs text-gray-600 mt-2">
          日本語フィールド名と英語フィールド名の両方をサポートしています。配列形式でも単一オブジェクト形式でも対応可能です。
        </p>
      </details>

      {/* Error display */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          <p className="font-medium">エラー</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Result display */}
      {result && (
        <div className={`border rounded-lg p-4 mb-4 ${
          result.success ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'
        }`}>
          <p className={`font-medium mb-2 ${
            result.success ? 'text-green-800' : 'text-yellow-800'
          }`}>
            {result.message}
          </p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div>
              <p className="text-gray-600">総件数</p>
              <p className="font-bold text-lg">{result.total_rows}</p>
            </div>
            <div>
              <p className="text-green-600">新規登録</p>
              <p className="font-bold text-lg">{result.imported_count}</p>
            </div>
            <div>
              <p className="text-blue-600">更新</p>
              <p className="font-bold text-lg">{result.updated_count}</p>
            </div>
            <div>
              <p className="text-gray-600">スキップ</p>
              <p className="font-bold text-lg">{result.skipped_count}</p>
            </div>
          </div>

          {type === 'factories' && result.factories_created !== undefined && (
            <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-green-600">工場作成</p>
                <p className="font-bold">{result.factories_created}</p>
              </div>
              <div>
                <p className="text-blue-600">ライン作成</p>
                <p className="font-bold">{result.lines_created || 0}</p>
              </div>
            </div>
          )}

          {result.errors.length > 0 && (
            <div className="mt-4">
              <p className="font-medium text-red-700 mb-2">
                エラー詳細 ({result.errors.length}件)
              </p>
              <div className="max-h-48 overflow-auto space-y-2">
                {result.errors.map((err, idx) => (
                  <div key={idx} className="text-xs bg-white border border-red-200 rounded p-2">
                    <p className="font-medium text-red-800">
                      行 {err.row}: {err.field}
                    </p>
                    <p className="text-gray-700">{err.message}</p>
                    {err.value && (
                      <p className="text-gray-500 mt-1">値: {JSON.stringify(err.value)}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Import button */}
      <button
        onClick={handleImport}
        disabled={importing || (inputMode === 'file' && !file) || (inputMode === 'text' && !jsonText.trim())}
        className="btn-primary w-full"
      >
        {importing ? 'インポート中...' : 'インポート実行'}
      </button>
    </div>
  )
}
