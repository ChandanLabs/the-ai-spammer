'use client'

import { useCallback, useEffect, useState } from 'react'
import {
  Briefcase, Plus, Trash2, RefreshCw, ExternalLink,
  Calendar, CheckCircle, XCircle, Edit3, Save, X
} from 'lucide-react'
import { api, type Drive } from '@/lib/api'
import { format, formatDistanceToNow, isPast } from 'date-fns'
import UploadZone from '@/components/UploadZone'

interface DriveForm {
  company_name: string
  registration_link: string
  deadline: string
  is_active: boolean
}

const emptyForm: DriveForm = {
  company_name: '',
  registration_link: '',
  deadline: '',
  is_active: true,
}

export default function DrivesPage() {
  const [drives, setDrives] = useState<Drive[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<DriveForm>(emptyForm)
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [selectedDriveUpload, setSelectedDriveUpload] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    try {
      setDrives(await api.drives.list())
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetch() }, [fetch])

  const createDrive = async () => {
    if (!form.company_name || !form.deadline) return
    setSaving(true)
    setError(null)
    try {
      await api.drives.create({
        company_name: form.company_name,
        registration_link: form.registration_link || null,
        deadline: new Date(form.deadline).toISOString(),
        is_active: form.is_active,
      })
      setForm(emptyForm)
      setShowForm(false)
      await fetch()
    } catch (e: any) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  const toggleActive = async (drive: Drive) => {
    await api.drives.update(drive.id, { is_active: !drive.is_active })
    await fetch()
  }

  const deleteDrive = async (id: string) => {
    if (!confirm('Delete this drive? Students linked to it will lose their drive association.')) return
    setDeletingId(id)
    try {
      await api.drives.delete(id)
      await fetch()
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="flex-1 p-8 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Hiring Drives</h1>
          <p className="text-sm text-slate-500 mt-1">{drives.length} drives configured</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={fetch} className="btn-secondary btn-sm" disabled={loading}>
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button onClick={() => setShowForm(!showForm)} className="btn-primary">
            <Plus className="w-4 h-4" />
            New Drive
          </button>
        </div>
      </div>

      {/* Create Form */}
      {showForm && (
        <div className="card p-6 space-y-4 animate-slide-up border-brand-500/30">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-300">Create New Drive</h2>
            <button onClick={() => setShowForm(false)} className="text-slate-500 hover:text-slate-300">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Company Name *</label>
              <input
                className="input"
                placeholder="e.g. Google, TCS, Infosys"
                value={form.company_name}
                onChange={e => setForm(p => ({ ...p, company_name: e.target.value }))}
              />
            </div>
            <div>
              <label className="label">Registration Link</label>
              <input
                className="input"
                placeholder="https://apply.company.com/..."
                value={form.registration_link}
                onChange={e => setForm(p => ({ ...p, registration_link: e.target.value }))}
              />
            </div>
            <div>
              <label className="label">Registration Deadline *</label>
              <input
                type="datetime-local"
                className="input"
                value={form.deadline}
                onChange={e => setForm(p => ({ ...p, deadline: e.target.value }))}
              />
            </div>
            <div className="flex items-end gap-3">
              <label className="flex items-center gap-2 cursor-pointer">
                <div
                  onClick={() => setForm(p => ({ ...p, is_active: !p.is_active }))}
                  className={`w-10 h-5 rounded-full transition-colors ${form.is_active ? 'bg-brand-500' : 'bg-surface-border'} relative cursor-pointer`}
                >
                  <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all ${form.is_active ? 'left-5' : 'left-0.5'}`} />
                </div>
                <span className="text-sm text-slate-300">Active</span>
              </label>
            </div>
          </div>

          {error && (
            <p className="text-sm text-red-400 flex items-center gap-2">
              <XCircle className="w-4 h-4" /> {error}
            </p>
          )}

          <div className="flex gap-3 justify-end">
            <button onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
            <button onClick={createDrive} disabled={saving || !form.company_name || !form.deadline} className="btn-primary">
              {saving ? 'Creating...' : 'Create Drive'}
            </button>
          </div>
        </div>
      )}

      {/* Drives Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card p-6 space-y-3">
              <div className="h-5 bg-surface-border rounded animate-pulse w-2/3" />
              <div className="h-4 bg-surface-border rounded animate-pulse w-1/2" />
            </div>
          ))
        ) : drives.length === 0 ? (
          <div className="col-span-2 text-center py-16 text-slate-600">
            <Briefcase className="w-10 h-10 mx-auto mb-3 opacity-30" />
            <p>No drives yet. Create your first one above.</p>
          </div>
        ) : (
          drives.map(drive => {
            const expired = isPast(new Date(drive.deadline))
            return (
              <div key={drive.id} className={`card p-6 space-y-4 transition-all ${!drive.is_active ? 'opacity-60' : ''}`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-semibold text-slate-200">{drive.company_name}</h3>
                      {drive.is_active && !expired ? (
                        <span className="badge badge-registered">Active</span>
                      ) : expired ? (
                        <span className="badge badge-blocked">Expired</span>
                      ) : (
                        <span className="badge badge-pending">Paused</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-2 text-xs text-slate-500">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>Deadline: {format(new Date(drive.deadline), 'dd MMM yyyy, hh:mm a')}</span>
                    </div>
                    {!expired && drive.is_active && (
                      <p className="text-xs text-amber-400 mt-1">
                        ⏳ {formatDistanceToNow(new Date(drive.deadline), { addSuffix: true })}
                      </p>
                    )}
                    {drive.registration_link && (
                      <a
                        href={drive.registration_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-brand-400 hover:text-brand-300 mt-1.5 transition-colors"
                      >
                        <ExternalLink className="w-3 h-3" /> Registration Link
                      </a>
                    )}
                  </div>
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => toggleActive(drive)}
                      className={drive.is_active ? 'btn-secondary btn-sm' : 'btn-success btn-sm'}
                      title={drive.is_active ? 'Deactivate' : 'Activate'}
                    >
                      {drive.is_active ? <XCircle className="w-3.5 h-3.5" /> : <CheckCircle className="w-3.5 h-3.5" />}
                    </button>
                    <button
                      onClick={() => deleteDrive(drive.id)}
                      disabled={deletingId === drive.id}
                      className="btn-danger btn-sm"
                      title="Delete drive"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Upload for this drive */}
                <div>
                  {selectedDriveUpload === drive.id ? (
                    <div className="mt-2 space-y-2">
                      <div className="flex items-center justify-between">
                        <p className="text-xs text-slate-400 font-medium">Upload students to this drive</p>
                        <button onClick={() => setSelectedDriveUpload(null)} className="text-slate-500 hover:text-slate-300">
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                      <UploadZone drives={[drive]} onSuccess={() => { setSelectedDriveUpload(null); fetch() }} compact />
                    </div>
                  ) : (
                    <button
                      onClick={() => setSelectedDriveUpload(drive.id)}
                      className="btn-secondary btn-sm w-full justify-center mt-1"
                    >
                      Upload Students CSV
                    </button>
                  )}
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
