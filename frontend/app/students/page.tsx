'use client'

import { useCallback, useEffect, useState } from 'react'
import {
  Users, Search, RefreshCw, CheckCircle, Clock,
  Ban, Wifi, WifiOff, Filter, ChevronDown, ChevronUp
} from 'lucide-react'
import { api, type Student, type StudentStatus, type Drive } from '@/lib/api'
import { format } from 'date-fns'

const STATUS_CONFIG = {
  REGISTERED: { label: 'Registered', cls: 'badge-registered', icon: CheckCircle },
  PENDING:    { label: 'Pending',    cls: 'badge-pending',    icon: Clock },
  BLOCKED:    { label: 'Blocked',    cls: 'badge-blocked',    icon: Ban },
} as const

export default function StudentsPage() {
  const [students, setStudents] = useState<Student[]>([])
  const [drives, setDrives] = useState<Drive[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState<StudentStatus | ''>('')
  const [filterDrive, setFilterDrive] = useState('')
  const [updatingId, setUpdatingId] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<string | null>(null)

  const fetchStudents = useCallback(async () => {
    setLoading(true)
    try {
      const [s, d] = await Promise.all([
        api.students.list({
          status: filterStatus || undefined,
          drive_id: filterDrive || undefined,
          search: search || undefined,
        }),
        api.drives.list(),
      ])
      setStudents(s)
      setDrives(d)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [filterStatus, filterDrive, search])

  useEffect(() => {
    const id = setTimeout(fetchStudents, 300)
    return () => clearTimeout(id)
  }, [fetchStudents])

  const updateStatus = async (id: string, status: StudentStatus) => {
    setUpdatingId(id)
    try {
      await api.students.update(id, { status })
      setStudents(prev => prev.map(s => s.id === id ? { ...s, status } : s))
    } finally {
      setUpdatingId(null)
    }
  }

  const pending = students.filter(s => s.status === 'PENDING').length
  const registered = students.filter(s => s.status === 'REGISTERED').length

  return (
    <div className="flex-1 p-8 space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Students</h1>
          <p className="text-sm text-slate-500 mt-1">
            {students.length} students · {registered} registered · {pending} pending
          </p>
        </div>
        <button onClick={fetchStudents} className="btn-secondary btn-sm" disabled={loading}>
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search name, roll, email..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input pl-9"
          />
        </div>
        <select
          value={filterStatus}
          onChange={e => setFilterStatus(e.target.value as StudentStatus | '')}
          className="input w-40"
        >
          <option value="">All Status</option>
          <option value="PENDING">Pending</option>
          <option value="REGISTERED">Registered</option>
          <option value="BLOCKED">Blocked</option>
        </select>
        <select
          value={filterDrive}
          onChange={e => setFilterDrive(e.target.value)}
          className="input w-48"
        >
          <option value="">All Drives</option>
          {drives.map(d => <option key={d.id} value={d.id}>{d.company_name}</option>)}
        </select>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="border-b border-surface-border bg-surface/50">
              <tr>
                <th className="th">Student</th>
                <th className="th">Roll No</th>
                <th className="th">Drive</th>
                <th className="th">Telegram</th>
                <th className="th">Nudges</th>
                <th className="th">Status</th>
                <th className="th">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="table-row">
                    {Array.from({ length: 7 }).map((_, j) => (
                      <td key={j} className="td">
                        <div className="h-4 bg-surface-border rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : students.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-16 text-center text-slate-600">
                    <Users className="w-8 h-8 mx-auto mb-3 opacity-30" />
                    <p>No students found. Upload a CSV to get started.</p>
                  </td>
                </tr>
              ) : (
                students.map(student => {
                  const cfg = STATUS_CONFIG[student.status]
                  const drive = drives.find(d => d.id === student.drive_id)
                  const isExpanded = expanded === student.id

                  return (
                    <>
                      <tr key={student.id} className="table-row cursor-pointer" onClick={() => setExpanded(isExpanded ? null : student.id)}>
                        <td className="td">
                          <div>
                            <p className="font-medium text-slate-200">{student.name}</p>
                            <p className="text-xs text-slate-500">{student.email}</p>
                          </div>
                        </td>
                        <td className="td">
                          <code className="text-xs bg-surface-border px-2 py-0.5 rounded-lg text-brand-400">
                            {student.roll_number}
                          </code>
                        </td>
                        <td className="td">
                          <span className="text-xs text-slate-400">{drive?.company_name || '—'}</span>
                        </td>
                        <td className="td">
                          {student.telegram_chat_id ? (
                            <span className="flex items-center gap-1.5 text-emerald-400 text-xs">
                              <Wifi className="w-3.5 h-3.5" /> Linked
                            </span>
                          ) : (
                            <span className="flex items-center gap-1.5 text-slate-600 text-xs">
                              <WifiOff className="w-3.5 h-3.5" /> Not linked
                            </span>
                          )}
                        </td>
                        <td className="td">
                          <span className="text-sm font-semibold text-slate-300">{student.nudge_count}</span>
                        </td>
                        <td className="td">
                          <span className={cfg.cls}>{cfg.label}</span>
                        </td>
                        <td className="td" onClick={e => e.stopPropagation()}>
                          <div className="flex gap-2">
                            {student.status !== 'REGISTERED' && (
                              <button
                                onClick={() => updateStatus(student.id, 'REGISTERED')}
                                disabled={updatingId === student.id}
                                className="btn-success btn-sm"
                              >
                                ✓
                              </button>
                            )}
                            {student.status !== 'BLOCKED' && (
                              <button
                                onClick={() => updateStatus(student.id, 'BLOCKED')}
                                disabled={updatingId === student.id}
                                className="btn-danger btn-sm"
                              >
                                ✕
                              </button>
                            )}
                            {student.status === 'BLOCKED' && (
                              <button
                                onClick={() => updateStatus(student.id, 'PENDING')}
                                disabled={updatingId === student.id}
                                className="btn-secondary btn-sm"
                              >
                                ↺
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr className="bg-surface/50">
                          <td colSpan={7} className="px-6 py-4">
                            <div className="grid grid-cols-4 gap-4 text-sm">
                              <div>
                                <p className="label">Branch</p>
                                <p className="text-slate-300">{student.branch || '—'}</p>
                              </div>
                              <div>
                                <p className="label">Year</p>
                                <p className="text-slate-300">{student.year || '—'}</p>
                              </div>
                              <div>
                                <p className="label">Phone</p>
                                <p className="text-slate-300">{student.phone || '—'}</p>
                              </div>
                              <div>
                                <p className="label">Last Nudge</p>
                                <p className="text-slate-300">
                                  {student.last_nudge_sent_at
                                    ? format(new Date(student.last_nudge_sent_at), 'dd MMM yyyy, HH:mm')
                                    : 'Never'}
                                </p>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
