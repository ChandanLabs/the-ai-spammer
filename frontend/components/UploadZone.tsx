'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { Upload, FileText, CheckCircle, XCircle, AlertTriangle, X } from 'lucide-react'
import { api, type Drive, type UploadResult } from '@/lib/api'

interface Props {
  drives: Drive[]
  onSuccess?: () => void
  compact?: boolean
}

export default function UploadZone({ drives, onSuccess, compact }: Props) {
  const [dragging, setDragging] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [selectedDrive, setSelectedDrive] = useState<string>('')
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<UploadResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f?.name.endsWith('.csv')) setFile(f)
    else setError('Please drop a .csv file')
  }, [])

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    setResult(null)
    setError(null)
    try {
      const res = await api.upload(file, selectedDrive || undefined)
      setResult(res)
      setFile(null)
      onSuccess?.()
    } catch (e: any) {
      setError(e.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`
          relative border-2 border-dashed rounded-2xl
          ${compact ? 'p-6' : 'p-10'}
          flex flex-col items-center justify-center gap-3 cursor-pointer
          transition-all duration-200
          ${dragging
            ? 'border-brand-500 bg-brand-500/10'
            : file
              ? 'border-emerald-500/50 bg-emerald-500/5'
              : 'border-surface-border bg-surface hover:border-brand-500/50 hover:bg-brand-500/5'}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={e => {
            const f = e.target.files?.[0]
            if (f) setFile(f)
          }}
        />
        {file ? (
          <>
            <FileText className="w-8 h-8 text-emerald-400" />
            <div className="text-center">
              <p className="text-sm font-medium text-emerald-400">{file.name}</p>
              <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
            <button
              onClick={e => { e.stopPropagation(); setFile(null) }}
              className="absolute top-3 right-3 text-slate-500 hover:text-red-400 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </>
        ) : (
          <>
            <div className="w-12 h-12 rounded-2xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center">
              <Upload className="w-6 h-6 text-brand-400" />
            </div>
            <div className="text-center">
              <p className="text-sm font-medium text-slate-300">
                Drag & drop CSV here
              </p>
              <p className="text-xs text-slate-500 mt-1">
                or click to browse — Required: <code className="text-brand-400">name</code>, <code className="text-brand-400">roll_no</code>
              </p>
            </div>
          </>
        )}
      </div>

      {/* Drive selector + Upload button */}
      <div className="flex gap-3">
        <select
          value={selectedDrive}
          onChange={e => setSelectedDrive(e.target.value)}
          className="input flex-1"
        >
          <option value="">No Drive (upload only)</option>
          {drives.map(d => (
            <option key={d.id} value={d.id}>{d.company_name}</option>
          ))}
        </select>
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="btn-primary shrink-0"
        >
          {uploading ? (
            <span className="animate-spin">⟳</span>
          ) : (
            <Upload className="w-4 h-4" />
          )}
          {uploading ? 'Uploading...' : 'Upload'}
        </button>
      </div>

      {/* Result */}
      {result && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 space-y-2 animate-slide-up">
          <div className="flex items-center gap-2 text-emerald-400 font-medium text-sm">
            <CheckCircle className="w-4 h-4" />
            Upload Successful
          </div>
          <div className="grid grid-cols-4 gap-2 text-center">
            {[
              { label: 'Total', value: result.total_rows },
              { label: 'Inserted', value: result.inserted },
              { label: 'Updated', value: result.updated },
              { label: 'Skipped', value: result.skipped },
            ].map(item => (
              <div key={item.label} className="bg-surface rounded-xl p-2">
                <p className="text-lg font-bold text-slate-100">{item.value}</p>
                <p className="text-xs text-slate-500">{item.label}</p>
              </div>
            ))}
          </div>
          {result.errors.length > 0 && (
            <div className="space-y-1 mt-2">
              {result.errors.map((e, i) => (
                <div key={i} className="flex items-center gap-2 text-xs text-amber-400">
                  <AlertTriangle className="w-3 h-3 shrink-0" />
                  {e}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm animate-slide-up">
          <XCircle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}
    </div>
  )
}
